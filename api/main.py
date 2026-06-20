import logging
import os
import json
import uuid
import time
import contextlib
from typing import List, Dict, Any

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from neuromarketing import TribeAdapter, NeuromarketingAnalyzer
from api.routers import analysis, copywriting, history, thumbnail
from api.auth import router as auth_router
from api.billing import router as billing_router
from api.database import init_db, ensure_database
from neuromarketing.models import HealthResponse
from neuromarketing.config import ATTENTION_ROIS, DOPAMINE_ROIS, MEMORY_ROIS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

tribe = TribeAdapter()
analyzer: NeuromarketingAnalyzer | None = None

# Redis client (optional)
_redis = None


def get_redis():
    global _redis
    if _redis is None:
        redis_url = os.getenv("REDIS_URL", "")
        if redis_url:
            try:
                import redis.asyncio as aioredis
                _redis = aioredis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                logger.info("Redis connected")
            except Exception as e:
                logger.warning(f"Redis unavailable ({e}), rate limiting disabled")
                _redis = None
    return _redis


# Rate limiting config
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
RATE_LIMIT_WINDOW_SEC = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
RATE_LIMIT_AUTH_REQUESTS = int(os.getenv("RATE_LIMIT_AUTH_REQUESTS", "20"))
RATE_LIMIT_AUTH_WINDOW_SEC = int(os.getenv("RATE_LIMIT_AUTH_WINDOW_SEC", "60"))
RATE_LIMIT_ANALYSIS_REQUESTS = int(os.getenv("RATE_LIMIT_ANALYSIS_REQUESTS", "10"))
RATE_LIMIT_ANALYSIS_WINDOW_SEC = int(os.getenv("RATE_LIMIT_ANALYSIS_WINDOW_SEC", "60"))

# Sentry (optional)
SENTRY_DSN = os.getenv("SENTRY_DSN", "")
if SENTRY_DSN:
    try:
        import sentry_sdk
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )
        logger.info("Sentry initialized")
    except ImportError:
        logger.info("sentry-sdk not installed, skipping")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TRIBE v2 adapter...")
    ok = tribe.initialize()
    logger.info(f"TRIBE v2 initialized: {ok}")
    global analyzer
    analyzer = NeuromarketingAnalyzer(tribe)

    logger.info("Connecting to database...")
    db_ok = await ensure_database()
    if db_ok:
        await init_db()
        logger.info("Database initialized")
    else:
        logger.warning("Database unavailable - running without persistence")

    redis_client = get_redis()
    if redis_client:
        try:
            await redis_client.ping()
            logger.info("Redis connection verified")
        except Exception:
            logger.warning("Redis ping failed - rate limiting disabled")

    yield

    if _redis:
        await _redis.close()
    logger.info("Shutting down...")


app = FastAPI(
    title="NeuralPulse Engine - Neuromarketing API",
    description="Brain-validated ad optimization using simulated fMRI responses via TRIBE v2",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)

# CORS - strict origins in production
cors_origins = os.getenv("CORS_ORIGINS", "*")
if cors_origins == "*" and os.getenv("ENVIRONMENT") == "production":
    cors_origins = []
    logger.warning("CORS_ORIGINS not set in production - restricting to empty")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins.split(",") if isinstance(cors_origins, str) else cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=os.getenv("TRUSTED_HOSTS", "*").split(","),
)

app.include_router(analysis.router)
app.include_router(copywriting.router)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(history.router)
app.include_router(thumbnail.router)


# ==========================================================
# Middleware: Request ID + Timing + Rate Limiting
# ==========================================================
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    start_time = time.time()

    response = await call_next(request)
    process_time = time.time() - start_time

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)

    if process_time > 5:
        logger.warning(f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s [rid={request_id}]")

    return response


# ==========================================================
# Middleware: Rate Limiting (Redis-backed)
# ==========================================================
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    redis_client = get_redis()
    if redis_client is None:
        return await call_next(request)

    # Determine rate limit tier
    if path.startswith("/auth/"):
        limit = RATE_LIMIT_AUTH_REQUESTS
        window = RATE_LIMIT_AUTH_WINDOW_SEC
    elif path.startswith("/analyze/") or path.startswith("/api/predict"):
        limit = RATE_LIMIT_ANALYSIS_REQUESTS
        window = RATE_LIMIT_ANALYSIS_WINDOW_SEC
    else:
        limit = RATE_LIMIT_REQUESTS
        window = RATE_LIMIT_WINDOW_SEC

    key = f"ratelimit:{client_ip}:{path.split('/')[1]}"
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window)

        if current > limit:
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Rate limit exceeded. Try again later."},
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(window),
                    "Retry-After": str(window),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - current))
        response.headers["X-RateLimit-Reset"] = str(window)
        return response
    except Exception:
        return await call_next(request)


# ==========================================================
# Endpoints
# ==========================================================
@app.get("/health", response_model=HealthResponse)
async def health():
    db_ok = False
    try:
        engine = None
        from api.database import get_engine
        engine = get_engine()
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok",
        model_loaded=tribe._initialized if hasattr(tribe, '_initialized') else False,
    )


@app.get("/api/info")
async def api_info():
    return {
        "service": "NeuralPulse Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "features": {
            "video_analysis": True,
            "audio_analysis": True,
            "text_analysis": True,
            "ab_testing": True,
            "copy_analysis": True,
            "authentication": True,
            "token_billing": True,
            "database": True,
            "thumbnail_generation": True,
        }
    }


@app.post("/api/predict-brain")
async def predict_brain(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    video_exts = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
    audio_exts = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
    text_exts = {".txt", ".md", ".html"}

    os.makedirs("./uploads", exist_ok=True)
    path = os.path.join("./uploads", f"{uuid.uuid4().hex}{ext}")
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)

    try:
        if ext in video_exts:
            result = analyzer.analyze_video(path, file.filename)
        elif ext in audio_exts:
            result = analyzer.analyze_audio(path, file.filename)
        elif ext in text_exts:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            result = analyzer.analyze_text(text, file.filename)
        else:
            os.remove(path)
            raise HTTPException(400, f"Unsupported file type: {ext}")

        os.remove(path)

        bs = result.brain_scores
        scores = {
            "attention": round(bs.attention.overall, 4),
            "dopamine": round(bs.dopamine.overall, 4),
            "memory": round(bs.memory.overall, 4),
        }

        roi_breakdown = {}
        for dim in ["attention", "dopamine", "memory"]:
            dim_data = getattr(bs, dim)
            for roi, val in dim_data.roi_breakdown.items():
                roi_breakdown[roi] = max(roi_breakdown.get(roi, 0), val)

        sorted_rois = sorted(roi_breakdown.items(), key=lambda x: -x[1])
        region_map = {}
        for roi, _ in getattr(bs, "attention").roi_breakdown.items(): region_map[roi] = "attention"
        for roi, _ in getattr(bs, "dopamine").roi_breakdown.items(): region_map[roi] = "dopamine"
        for roi, _ in getattr(bs, "memory").roi_breakdown.items(): region_map[roi] = "memory"

        roi_full_names = {
            "V1": "V1 (Primary Visual)", "V2": "V2 (Visual)", "V3": "V3 (Visual)",
            "V4": "V4 (Visual)", "MT": "MT/V5 (Visual Motion)", "FEF": "FEF (Frontal Eye Fields)",
            "IPS": "IPS (Intraparietal Sulcus)", "VS": "VS (Ventral Striatum)",
            "NAcc": "NAcc (Nucleus Accumbens)", "vmPFC": "vmPFC",
            "SN": "SN (Substantia Nigra)", "VTA": "VTA (Ventral Tegmental)",
            "HIP": "HIP (Hippocampus)", "PHC": "PHC (Parahippocampal)",
            "PRC": "PRC (Perirhinal)", "ERC": "ERC (Entorhinal)",
            "ANG": "ANG (Angular Gyrus)", "PCC": "PCC (Posterior Cingulate)",
            "DLPFC": "DLPFC", "A1": "A1 (Primary Auditory)",
            "A2": "A2 (Auditory)", "STG": "STG (Superior Temporal)",
            "MTG": "MTG (Middle Temporal)", "IFG": "IFG (Inferior Frontal)",
            "AG": "AG (Angular)", "Precuneus": "Precuneus",
            "M1": "M1 (Primary Motor)", "S1": "S1 (Somatosensory)",
            "SMA": "SMA (Supplementary Motor)", "Caude": "Caudate",
        }

        regions = [
            {
                "name": roi_full_names.get(roi, roi),
                "value": round(val * 100, 1),
                "impact": region_map.get(roi, "attention"),
            }
            for roi, val in sorted_rois[:15]
        ]

        virality_factors = {
            "Face Engagement (FFA/TPJ)": (bs.attention.overall * 0.6 + bs.dopamine.overall * 0.4),
            "Emotional Arousal (Amygdala)": bs.dopamine.overall,
            "Auditory Hook (A1)": bs.memory.overall * 0.5 + bs.attention.overall * 0.3,
            "Visual Salience (MT/V1)": bs.attention.overall,
            "Narrative Immersion (DMN)": bs.memory.overall,
        }
        virality_colors = {
            "Face Engagement (FFA/TPJ)": "#4d6cf5",
            "Emotional Arousal (Amygdala)": "#f59e0b",
            "Auditory Hook (A1)": "#10b981",
            "Visual Salience (MT/V1)": "#8b5cf6",
            "Narrative Immersion (DMN)": "#ef4444",
        }
        factors = [
            {"label": k, "value": round(v, 4), "color": virality_colors[k]}
            for k, v in virality_factors.items()
        ]
        virality_score = round(
            0.30 * virality_factors["Face Engagement (FFA/TPJ)"]
            + 0.20 * virality_factors["Emotional Arousal (Amygdala)"]
            + 0.15 * virality_factors["Auditory Hook (A1)"]
            + 0.15 * virality_factors["Visual Salience (MT/V1)"]
            + 0.20 * virality_factors["Narrative Immersion (DMN)"],
            4,
        )

        overall = bs.attention.overall * 0.35 + bs.dopamine.overall * 0.35 + bs.memory.overall * 0.30
        if overall > 0.7:
            length_rec = "15-30s"
            format_rec = "Vertical (9:16)"
            retention_rec = "2-5s"
            audience_rec = "Gen Z/Mill (18-35)"
        elif overall > 0.45:
            length_rec = "30-60s"
            format_rec = "Horizontal (16:9)"
            retention_rec = "5-10s"
            audience_rec = "Mill/Gen X (25-50)"
        else:
            length_rec = "Variable"
            format_rec = "Adaptive"
            retention_rec = "3-8s"
            audience_rec = "Broad (18-54)"

        stats = [
            {"label": "Optimal Length", "value": length_rec, "sub": "AI estimated"},
            {"label": "Best Format", "value": format_rec, "sub": "Recommended"},
            {"label": "Peak Retention", "value": retention_rec, "sub": "Hook window"},
            {"label": "Target Audience", "value": audience_rec, "sub": "Predicted"},
        ]

        return {
            "success": True,
            "filename": file.filename,
            "scores": scores,
            "regions": regions,
            "virality": round(virality_score * 100),
            "score": virality_score,
            "factors": factors,
            "stats": stats,
            "overall_grade": result.overall_grade,
            "summary": result.summary,
        }

    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(path):
            try: os.remove(path)
            except OSError: pass
        logger.exception("Brain prediction failed")
        return {"success": False, "error": str(e)}


# Legacy static file serving (for backward compatibility)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.get("/")
async def serve_landing():
    landing_path = os.path.join(FRONTEND_DIR, "landing.html")
    if os.path.exists(landing_path):
        return FileResponse(landing_path)
    return {"service": "NeuralPulse Engine", "version": "1.0.0", "docs": "/docs"}

@app.get("/app/{rest_of_path:path}")
async def serve_app(rest_of_path: str):
    file_path = os.path.join(FRONTEND_DIR, rest_of_path or "index.html")
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    fallbacks = ["index.html", "dashboard.html", "landing.html"]
    for fb in fallbacks:
        fp = os.path.join(FRONTEND_DIR, fb)
        if os.path.exists(fp):
            return FileResponse(fp)
    return {"error": "Page not found"}

for _dir in ["css", "js", "fonts", "img", "images", "assets", "brain_viz", "thumbnails"]:
    _p = os.path.join(FRONTEND_DIR, _dir)
    if _dir == "thumbnails":
        os.makedirs(_p, exist_ok=True)
    if os.path.isdir(_p):
        try:
            app.mount(f"/{_dir}", StaticFiles(directory=_p), name=_dir)
        except Exception as e:
            logger.warning(f"Could not mount /{_dir}: {e}")
