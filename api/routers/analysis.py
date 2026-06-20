from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import List, Optional
import os
import json
import logging

from neuromarketing import (
    TribeAdapter, NeuromarketingAnalyzer, ABTestEngine
)
from api.dependencies import save_upload
from api.schemas import (
    AnalyzeTextRequest, ABTestTextRequest,
    AnalysisResponse, BatchAnalysisResponse,
)
from api.database import get_session_maker, AnalysisHistory, User, get_token_cost
from api.auth import get_current_user
from api.billing import deduct_tokens

# Try to import brain_viz, but fall back gracefully if heavy deps missing
try:
    from neuromarketing.brain_viz import get_brain_viz_urls
except (ImportError, ModuleNotFoundError):
    def get_brain_viz_urls(*args, **kwargs):
        """Stub: brain_viz visualization deps not available"""
        return {}

def get_session():
    return get_session_maker()()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Analysis"])

tribe = TribeAdapter()
analyzer = NeuromarketingAnalyzer(tribe)
ab_test = ABTestEngine(analyzer)

async def save_analysis_history(
    user_id: int,
    analysis_id: str,
    media_type: str,
    filename: str,
    result_data: dict,
    tokens_used: int,
):
    try:
        async with get_session() as session:
            bs = result_data.get("brain_scores", {})
            record = AnalysisHistory(
                user_id=user_id,
                analysis_id=analysis_id,
                media_type=media_type,
                filename=filename,
                overall_grade=result_data.get("overall_grade", ""),
                attention_score=bs.get("attention", {}).get("overall"),
                dopamine_score=bs.get("dopamine", {}).get("overall"),
                memory_score=bs.get("memory", {}).get("overall"),
                results_json=json.dumps(result_data),
                duration_sec=result_data.get("duration_sec", 0),
                tokens_used=tokens_used,
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.warning(f"Failed to save analysis history: {e}")

@router.post("/video", response_model=AnalysisResponse)
async def analyze_video(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("video", user)
    if not deduction.success:
        return AnalysisResponse(success=False, error=deduction.error)
    try:
        path = await save_upload(file)
        ext = os.path.splitext(file.filename)[1].lower()
        video_exts = {".mp4", ".mov", ".avi", ".webm", ".mkv"}
        if ext not in video_exts:
            os.remove(path)
            raise HTTPException(400, f"Not a video file: {ext}")

        result = analyzer.analyze_video(path, file.filename)
        os.remove(path)
        data = result.model_dump()
        brain_viz_urls = await _add_brain_viz(data, "video")
        if brain_viz_urls:
            data["brain_viz_urls"] = brain_viz_urls
        await save_analysis_history(user.id, data.get("id", ""), "video", file.filename, data, deduction.deduction or 50)
        data["tokens_used"] = deduction.deduction
        data["token_balance_after"] = deduction.balance_after
        return AnalysisResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Video analysis failed")
        return AnalysisResponse(success=False, error=str(e))

@router.post("/audio", response_model=AnalysisResponse)
async def analyze_audio(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("audio", user)
    if not deduction.success:
        return AnalysisResponse(success=False, error=deduction.error)
    try:
        path = await save_upload(file)
        ext = os.path.splitext(file.filename)[1].lower()
        audio_exts = {".mp3", ".wav", ".ogg", ".m4a", ".flac"}
        if ext not in audio_exts:
            os.remove(path)
            raise HTTPException(400, f"Not an audio file: {ext}")

        result = analyzer.analyze_audio(path, file.filename)
        os.remove(path)
        data = result.model_dump()
        brain_viz_urls = await _add_brain_viz(data, "audio")
        if brain_viz_urls:
            data["brain_viz_urls"] = brain_viz_urls
        await save_analysis_history(user.id, data.get("id", ""), "audio", file.filename, data, deduction.deduction or 30)
        data["tokens_used"] = deduction.deduction
        data["token_balance_after"] = deduction.balance_after
        return AnalysisResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Audio analysis failed")
        return AnalysisResponse(success=False, error=str(e))

@router.post("/text", response_model=AnalysisResponse)
async def analyze_text(
    request: AnalyzeTextRequest,
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("text", user)
    if not deduction.success:
        return AnalysisResponse(success=False, error=deduction.error)
    try:
        result = analyzer.analyze_text(request.text, request.filename)
        data = result.model_dump()
        brain_viz_urls = await _add_brain_viz(data, "text")
        if brain_viz_urls:
            data["brain_viz_urls"] = brain_viz_urls
        await save_analysis_history(user.id, data.get("id", ""), "text", request.filename, data, deduction.deduction or 10)
        data["tokens_used"] = deduction.deduction
        data["token_balance_after"] = deduction.balance_after
        return AnalysisResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Text analysis failed")
        return AnalysisResponse(success=False, error=str(e))


def _collect_roi_scores(analysis_data: dict) -> dict:
    """Extract all ROI scores from analysis result dict."""
    bs = analysis_data.get("brain_scores", {})
    roi_scores = {}
    for dim in ["attention", "dopamine", "memory"]:
        dim_data = bs.get(dim, {})
        roi_bd = dim_data.get("roi_breakdown", {})
        for roi, score in roi_bd.items():
            roi_scores[roi] = max(roi_scores.get(roi, 0), score)
    return roi_scores


async def _add_brain_viz(analysis_data: dict, media_type: str) -> dict:
    """Generate brain viz HTML and return URLs dict."""
    try:
        roi_scores = _collect_roi_scores(analysis_data)
        aid = analysis_data.get("id", "unknown")
        return await get_brain_viz_urls(roi_scores, aid)
    except Exception as e:
        logger.warning(f"Brain viz generation skipped: {e}")
        return {}

@router.post("/upload-text", response_model=AnalysisResponse)
async def analyze_text_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("text", user)
    if not deduction.success:
        return AnalysisResponse(success=False, error=deduction.error)
    try:
        path = await save_upload(file)
        ext = os.path.splitext(file.filename)[1].lower()
        text_exts = {".txt", ".md", ".html"}
        if ext not in text_exts:
            os.remove(path)
            raise HTTPException(400, f"Not a text file: {ext}")

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        os.remove(path)

        result = analyzer.analyze_text(text, file.filename)
        data = result.model_dump()
        brain_viz_urls = await _add_brain_viz(data, "text")
        if brain_viz_urls:
            data["brain_viz_urls"] = brain_viz_urls
        await save_analysis_history(user.id, data.get("id", ""), "text", file.filename, data, deduction.deduction or 10)
        data["tokens_used"] = deduction.deduction
        data["token_balance_after"] = deduction.balance_after
        return AnalysisResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Text file analysis failed")
        return AnalysisResponse(success=False, error=str(e))

@router.post("/ab-test/video", response_model=BatchAnalysisResponse)
async def ab_test_video(
    files: List[UploadFile] = File(...),
    variant_names: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("ab_test", user)
    if not deduction.success:
        return BatchAnalysisResponse(success=False, error=deduction.error)
    try:
        if len(files) < 2:
            raise HTTPException(400, "Need at least 2 files for A/B test")
        names = variant_names.split(",") if variant_names else None
        paths = []
        for f in files:
            paths.append(await save_upload(f))
        result = ab_test.compare_videos(paths, variant_names=names, filenames=[f.filename for f in files])
        for p in paths:
            try: os.remove(p)
            except OSError: pass
        return BatchAnalysisResponse(success=True, data=result.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Video AB test failed")
        return BatchAnalysisResponse(success=False, error=str(e))

@router.post("/ab-test/audio", response_model=BatchAnalysisResponse)
async def ab_test_audio(
    files: List[UploadFile] = File(...),
    variant_names: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("ab_test", user)
    if not deduction.success:
        return BatchAnalysisResponse(success=False, error=deduction.error)
    try:
        if len(files) < 2:
            raise HTTPException(400, "Need at least 2 files for A/B test")
        names = variant_names.split(",") if variant_names else None
        paths = []
        for f in files:
            paths.append(await save_upload(f))
        result = ab_test.compare_audio(paths, variant_names=names)
        for p in paths:
            try: os.remove(p)
            except OSError: pass
        return BatchAnalysisResponse(success=True, data=result.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Audio AB test failed")
        return BatchAnalysisResponse(success=False, error=str(e))

@router.post("/ab-test/text", response_model=BatchAnalysisResponse)
async def ab_test_text(
    request: ABTestTextRequest,
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("ab_test", user)
    if not deduction.success:
        return BatchAnalysisResponse(success=False, error=deduction.error)
    try:
        result = ab_test.compare_texts(request.texts, variant_names=request.variant_names)
        return BatchAnalysisResponse(success=True, data=result.model_dump())
    except Exception as e:
        logger.exception("Text AB test failed")
        return BatchAnalysisResponse(success=False, error=str(e))
