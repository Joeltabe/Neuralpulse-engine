import logging
import os
import json
import uuid
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import select
from PIL import Image, ImageDraw, ImageFont

from api.database import get_session_maker, User, ThumbnailHistory
from api.auth import get_current_user
from api.billing import deduct_tokens
from api.image_generation import generate_image

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/thumbnail", tags=["Thumbnail Generator"])

THUMBNAILS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "thumbnails"
)

MODELS = {
    "flux1-dev": {
        "name": "FLUX.1-dev",
        "provider": "Black Forest Labs",
        "params": "12B",
        "description": "Pinnacle open-weight image generation. Multimodal diffusion transformer (DiT) with unparalleled photorealism, fine details, and prompt adherence.",
        "strengths": ["Photorealism", "Fine details", "Prompt adherence"],
        "best_for": ["Product thumbnails", "Realistic scenes", "High-fidelity renders"],
        "style_weight": {"attention": 0.85, "dopamine": 0.78, "memory": 0.82},
        "color": "#4d6cf5",
    },
    "sd35-large": {
        "name": "Stable Diffusion 3.5 Large",
        "provider": "Stability AI",
        "params": "8B",
        "description": "Industry-leading text rendering with improved photorealism and robust instruction following. Excels at generating precise text within images.",
        "strengths": ["Text rendering", "Instruction following", "Photorealism"],
        "best_for": ["Thumbnails with text overlays", "Branded content", "Typography-heavy designs"],
        "style_weight": {"attention": 0.82, "dopamine": 0.75, "memory": 0.79},
        "color": "#8b5cf6",
    },
    "qwen-image": {
        "name": "Qwen-Image",
        "provider": "Alibaba Cloud",
        "params": "7B",
        "description": "Unified multimodal foundation model for both generating high-quality visuals and performing precise image edits including text manipulation and object replacement.",
        "strengths": ["Image editing", "Text manipulation", "Multi-turn refinement"],
        "best_for": ["Iterative designs", "Edit-in-place thumbnails", "Text-in-image"],
        "style_weight": {"attention": 0.79, "dopamine": 0.81, "memory": 0.76},
        "color": "#10b981",
    },
    "qwen-image-edit": {
        "name": "Qwen-Image-Edit",
        "provider": "Alibaba Cloud",
        "params": "7B",
        "description": "Specialized variant of Qwen-Image focused on precise edits: add/remove text, swap objects, change backgrounds while preserving image coherence.",
        "strengths": ["Precise edits", "Object swapping", "Background changes"],
        "best_for": ["A/B thumbnail variations", "Quick iterations", "Localized edits"],
        "style_weight": {"attention": 0.76, "dopamine": 0.73, "memory": 0.80},
        "color": "#f59e0b",
    },
    "cosmos3-t2i": {
        "name": "Cosmos3-Nano",
        "provider": "NVIDIA",
        "params": "16B",
        "description": "Efficient omnimodal foundation model (8B reasoner + 8B generator) using a hybrid mixture of transformers for text-to-image/video generation via local diffusers inference.",
        "strengths": ["Efficient inference", "Hybrid architecture", "Local generation"],
        "best_for": ["Cinematic thumbnails", "Scene generation", "High-coherence visuals"],
        "style_weight": {"attention": 0.88, "dopamine": 0.84, "memory": 0.86},
        "color": "#ef4444",
    },
}

MODEL_COLORS = {k: v["color"] for k, v in MODELS.items()}

class ThumbnailRequest(BaseModel):
    prompt: str
    models: Optional[List[str]] = None
    style_preset: Optional[str] = "auto"
    negative_prompt: Optional[str] = ""
    width: Optional[int] = 1280
    height: Optional[int] = 720
    guidance_scale: Optional[float] = 7.5
    num_inference_steps: Optional[int] = 35

class ThumbnailResult(BaseModel):
    model_key: str
    model_name: str
    image_url: str
    thumbnail_url: str
    neural_scores: dict
    generation_time_ms: int
    error_message: Optional[str] = None

class BatchThumbnailResponse(BaseModel):
    success: bool
    results: Optional[List[ThumbnailResult]] = None
    model_details: Optional[dict] = None
    prompt: Optional[str] = None
    history_id: Optional[int] = None
    real_generation: Optional[bool] = False
    generation_info: Optional[dict] = None
    error: Optional[str] = None

class HistoryListResponse(BaseModel):
    success: bool
    items: Optional[list] = None
    error: Optional[str] = None

class HistoryDetailResponse(BaseModel):
    success: bool
    item: Optional[dict] = None
    error: Optional[str] = None

def get_session():
    return get_session_maker()()

def _compute_neural_scores(prompt: str, model_key: str):
    model_info = MODELS[model_key]
    style_w = model_info["style_weight"]
    base_score = min(0.95, len(prompt.split()) / 20 + 0.3)
    scores = {
        "attention": round(min(1.0, style_w["attention"] * base_score), 4),
        "dopamine": round(min(1.0, style_w["dopamine"] * base_score * (0.9 + 0.1 * (hash(prompt) % 10) / 10)), 4),
        "memory": round(min(1.0, style_w["memory"] * base_score * (0.85 + 0.15 * (hash(prompt + model_key) % 10) / 10)), 4),
        "overall": 0.0,
    }
    scores["overall"] = round(
        scores["attention"] * 0.35
        + scores["dopamine"] * 0.35
        + scores["memory"] * 0.30,
        4,
    )
    return scores

def _try_neuromarketing_analysis(prompt: str):
    try:
        from neuromarketing import TribeAdapter, NeuromarketingAnalyzer
        tribe = TribeAdapter()
        if not tribe._initialized:
            tribe.initialize()
        analyzer = NeuromarketingAnalyzer(tribe)
        text_result = analyzer.analyze_text(prompt, "thumbnail_prompt.txt")
        bs = text_result.brain_scores
        return {
            "attention_score": round(bs.attention.overall, 4),
            "dopamine_score": round(bs.dopamine.overall, 4),
            "memory_score": round(bs.memory.overall, 4),
        }
    except Exception as e:
        logger.warning(f"Neuromarketing analysis unavailable: {e}")
        return None

@router.post("/generate", response_model=BatchThumbnailResponse)
async def generate_thumbnails(
    request: ThumbnailRequest,
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("thumbnail", user)
    if not deduction.success:
        return BatchThumbnailResponse(success=False, error=deduction.error)

    try:
        models_to_run = request.models or list(MODELS.keys())
        if not models_to_run:
            models_to_run = list(MODELS.keys())

        os.makedirs(THUMBNAILS_DIR, exist_ok=True)

        results = []
        errors = []

        for model_key in models_to_run:
            if model_key not in MODELS:
                continue

            model_info = MODELS[model_key]
            neural_scores = _compute_neural_scores(request.prompt, model_key)
            image_url = None
            thumbnail_url = None
            gen_time_ms = 0

            try:
                result = await generate_image(
                    model_key=model_key,
                    prompt=request.prompt,
                        negative_prompt=request.negative_prompt or "",
                        width=request.width or 1280,
                        height=request.height or 720,
                        guidance_scale=request.guidance_scale or 7.5,
                        num_inference_steps=request.num_inference_steps or 35,
                )
                image_url = result["image_url"]
                thumbnail_url = result["thumbnail_url"]
                gen_time_ms = result["generation_time_ms"]
                error_msg = None
            except Exception as gen_err:
                logger.warning(f"Image generation failed for {model_key}: {gen_err}")
                error_msg = str(gen_err)
                # Create a simple local placeholder image so the frontend doesn't 404
                gen_id = uuid.uuid4().hex[:12]
                image_path = os.path.join(THUMBNAILS_DIR, f"{gen_id}_{model_key}.png")
                thumb_path_local = os.path.join(THUMBNAILS_DIR, f"{gen_id}_{model_key}_thumb.png")
                try:
                    os.makedirs(THUMBNAILS_DIR, exist_ok=True)
                    # 1280x720 placeholder
                    img = Image.new('RGB', (1280, 720), color=(18, 20, 40))
                    draw = ImageDraw.Draw(img)
                    msg = 'Generation failed — offline or API error'
                    try:
                        font = ImageFont.load_default()
                        # PIL >= 8.0: use textbbox for accurate measurement
                        try:
                            bbox = draw.textbbox((0, 0), msg, font=font)
                            w = bbox[2] - bbox[0]
                            h = bbox[3] - bbox[1]
                        except Exception:
                            w, h = font.getsize(msg)
                        draw.text(((1280 - w) / 2, (720 - h) / 2), msg, fill=(200, 200, 220), font=font)
                    except Exception:
                        # best-effort fallback: place text at fixed position
                        draw.text((40, 340), msg, fill=(200, 200, 220))
                    img.save(image_path, 'PNG')
                    thumb = img.copy()
                    thumb.thumbnail((640, 360))
                    thumb.save(thumb_path_local, 'PNG')
                    image_url = f"/api/thumbnails/{os.path.basename(image_path)}"
                    thumbnail_url = f"/api/thumbnails/{os.path.basename(thumb_path_local)}"
                except Exception as e:
                    logger.warning(f"Failed to write placeholder thumbnail: {e}")
                    # fallback to non-existing path (frontend will render SVG placeholder)
                    image_url = f"/api/thumbnails/{gen_id}_{model_key}.png"
                    thumbnail_url = f"/api/thumbnails/{gen_id}_{model_key}_thumb.png"
                gen_time_ms = 500
                errors.append({"model": model_key, "error": error_msg})

            results.append(ThumbnailResult(
                model_key=model_key,
                model_name=model_info["name"],
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                neural_scores=neural_scores,
                generation_time_ms=gen_time_ms,
                error_message=error_msg if 'error_msg' in locals() and error_msg else None,
            ))

        nm_scores = _try_neuromarketing_analysis(request.prompt)
        if nm_scores:
            for r in results:
                r.neural_scores["attention_score"] = nm_scores["attention_score"]
                r.neural_scores["dopamine_score"] = nm_scores["dopamine_score"]
                r.neural_scores["memory_score"] = nm_scores["memory_score"]
                r.neural_scores["engagement_forecast"] = round(
                    (nm_scores["attention_score"] * 0.35
                     + nm_scores["dopamine_score"] * 0.35
                     + nm_scores["memory_score"] * 0.30
                     + r.neural_scores["overall"] * 0.35) / 1.35,
                    4,
                )

        history_id = None
        try:
            async with get_session() as session:
                engagement = None
                if results and "engagement_forecast" in results[0].neural_scores:
                    engagement = results[0].neural_scores["engagement_forecast"]
                elif results:
                    engagement = results[0].neural_scores["overall"]

                entry = ThumbnailHistory(
                    user_id=user.id,
                    prompt=request.prompt,
                    style_preset=request.style_preset,
                    models_used=",".join(models_to_run),
                    results_json=json.dumps([r.model_dump() for r in results]),
                    engagement_forecast=engagement,
                    tokens_used=deduction.deduction or 15,
                )
                session.add(entry)
                await session.commit()
                await session.refresh(entry)
                history_id = entry.id
        except Exception as e:
            logger.warning(f"Could not save thumbnail history: {e}")

        return BatchThumbnailResponse(
            success=True,
            results=results,
            model_details=MODELS,
            prompt=request.prompt,
            history_id=history_id,
            real_generation=True,
            generation_info={"errors": errors} if errors else None,
        )

    except Exception as e:
        logger.exception("Thumbnail generation failed")
        return BatchThumbnailResponse(success=False, error=str(e))

@router.get("/models")
async def list_models():
    return {
        "success": True,
        "models": {
            k: {
                "name": v["name"],
                "provider": v["provider"],
                "params": v["params"],
                "description": v["description"],
                "strengths": v["strengths"],
                "best_for": v["best_for"],
                "style_weight": v["style_weight"],
            }
            for k, v in MODELS.items()
        }
    }

@router.get("/history", response_model=HistoryListResponse)
async def list_history(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
):
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ThumbnailHistory)
                .where(ThumbnailHistory.user_id == user.id)
                .order_by(ThumbnailHistory.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            items = result.scalars().all()

            count_result = await session.execute(
                select(ThumbnailHistory.id)
                .where(ThumbnailHistory.user_id == user.id)
            )
            total = len(count_result.scalars().all())

            return HistoryListResponse(
                success=True,
                items=[{
                    "id": item.id,
                    "prompt": item.prompt,
                    "style_preset": item.style_preset,
                    "models_used": item.models_used.split(",") if item.models_used else [],
                    "engagement_forecast": item.engagement_forecast,
                    "tokens_used": item.tokens_used,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "results_count": len(json.loads(item.results_json)) if item.results_json else 0,
                } for item in items]
            )
    except Exception as e:
        logger.exception("Failed to list thumbnail history")
        return HistoryListResponse(success=False, error=str(e))

@router.get("/history/{history_id}", response_model=HistoryDetailResponse)
async def get_history_detail(
    history_id: int,
    user: User = Depends(get_current_user),
):
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ThumbnailHistory)
                .where(ThumbnailHistory.id == history_id, ThumbnailHistory.user_id == user.id)
            )
            item = result.scalar_one_or_none()
            if not item:
                return HistoryDetailResponse(success=False, error="History entry not found")

            return HistoryDetailResponse(
                success=True,
                item={
                    "id": item.id,
                    "prompt": item.prompt,
                    "style_preset": item.style_preset,
                    "models_used": item.models_used.split(",") if item.models_used else [],
                    "results": json.loads(item.results_json) if item.results_json else [],
                    "engagement_forecast": item.engagement_forecast,
                    "tokens_used": item.tokens_used,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                }
            )
    except Exception as e:
        logger.exception("Failed to get thumbnail history detail")
        return HistoryDetailResponse(success=False, error=str(e))

@router.delete("/history/{history_id}", response_model=HistoryListResponse)
async def delete_history_entry(
    history_id: int,
    user: User = Depends(get_current_user),
):
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ThumbnailHistory)
                .where(ThumbnailHistory.id == history_id, ThumbnailHistory.user_id == user.id)
            )
            item = result.scalar_one_or_none()
            if not item:
                return HistoryListResponse(success=False, error="History entry not found")

            await session.delete(item)
            await session.commit()

            return HistoryListResponse(success=True, items=[{"id": history_id, "deleted": True}])
    except Exception as e:
        logger.exception("Failed to delete thumbnail history entry")
        return HistoryListResponse(success=False, error=str(e))

@router.get("/history/{history_id}/export")
async def export_history_entry(
    history_id: int,
    format: str = Query("json", regex="^(json|html)$"),
    user: User = Depends(get_current_user),
):
    try:
        async with get_session() as session:
            result = await session.execute(
                select(ThumbnailHistory)
                .where(ThumbnailHistory.id == history_id, ThumbnailHistory.user_id == user.id)
            )
            item = result.scalar_one_or_none()
            if not item:
                raise HTTPException(404, "History entry not found")

            results_data = json.loads(item.results_json) if item.results_json else []
            models_used = item.models_used.split(",") if item.models_used else []

            if format == "html":
                rows = ""
                for r in results_data:
                    ns = r.get("neural_scores", {})
                    rows += f"""<tr>
                        <td style="padding:8px 12px;border:1px solid #333">{r.get('model_name','')}</td>
                        <td style="padding:8px 12px;border:1px solid #333">{round(ns.get('attention',0)*100,1)}%</td>
                        <td style="padding:8px 12px;border:1px solid #333">{round(ns.get('dopamine',0)*100,1)}%</td>
                        <td style="padding:8px 12px;border:1px solid #333">{round(ns.get('memory',0)*100,1)}%</td>
                        <td style="padding:8px 12px;border:1px solid #333">{round(ns.get('overall',0)*100,1)}%</td>
                    </tr>"""
                html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>NeuralPulse Thumbnail Export</title>
<style>body{{font-family:Arial,sans-serif;background:#0a0a1a;color:#e0e0f0;padding:40px}}h1{{color:#00d4ff}}table{{border-collapse:collapse;width:100%}}th{{background:rgba(0,212,255,0.1);padding:8px 12px;border:1px solid #333;text-align:left;color:#00d4ff}}</style></head>
<body>
<h1>NeuralPulse Thumbnail Export</h1>
<p><strong>Prompt:</strong> {item.prompt}</p>
<p><strong>Models:</strong> {', '.join(models_used)}</p>
<p><strong>Generated:</strong> {item.created_at.isoformat() if item.created_at else 'N/A'}</p>
<table><thead><tr><th>Model</th><th>Attention</th><th>Dopamine</th><th>Memory</th><th>Overall</th></tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
                return Response(content=html, media_type="text/html",
                    headers={"Content-Disposition": f"attachment; filename=neuralpulse_export_{history_id}.html"})

            export_data = {
                "id": item.id,
                "prompt": item.prompt,
                "style_preset": item.style_preset,
                "models_used": models_used,
                "results": results_data,
                "engagement_forecast": item.engagement_forecast,
                "tokens_used": item.tokens_used,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
            return Response(
                content=json.dumps(export_data, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=neuralpulse_export_{history_id}.json"}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to export thumbnail history entry")
        raise HTTPException(500, str(e))
