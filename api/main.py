import logging
import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from neuromarketing import TribeAdapter
from api.routers import analysis, copywriting, history
from api.auth import router as auth_router
from api.billing import router as billing_router
from api.database import init_db, ensure_database
from neuromarketing.models import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

tribe = TribeAdapter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TRIBE v2 adapter...")
    ok = tribe.initialize()
    logger.info(f"TRIBE v2 initialized: {ok}")

    logger.info("Connecting to database...")
    db_ok = await ensure_database()
    if db_ok:
        await init_db()
        logger.info("Database initialized")
    else:
        logger.warning("Database unavailable - running without persistence")

    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="NeuralPulse Engine - Neuromarketing API",
    description="Brain-validated ad optimization using simulated fMRI responses via TRIBE v2",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis.router)
app.include_router(copywriting.router)
app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(history.router)

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=tribe._initialized,
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
        }
    }

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

for _dir in ["css", "js", "fonts", "img", "images", "assets", "brain_viz"]:
    _p = os.path.join(FRONTEND_DIR, _dir)
    if os.path.isdir(_p):
        try:
            app.mount(f"/{_dir}", StaticFiles(directory=_p), name=_dir)
        except Exception as e:
            logger.warning(f"Could not mount /{_dir}: {e}")
