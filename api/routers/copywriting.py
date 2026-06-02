from fastapi import APIRouter, HTTPException, Depends
import logging

from neuromarketing import TribeAdapter, NeuralCopyAnalyzer
from api.schemas import CopyAnalysisRequest, AnalysisResponse
from api.database import User
from api.auth import get_current_user
from api.billing import deduct_tokens

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copy", tags=["Neural Copywriting"])

tribe = TribeAdapter()
copy_analyzer = NeuralCopyAnalyzer(tribe)

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_copy(
    request: CopyAnalysisRequest,
    user: User = Depends(get_current_user),
):
    deduction = await deduct_tokens("copy", user)
    if not deduction.success:
        return AnalysisResponse(success=False, error=deduction.error)
    try:
        result = copy_analyzer.analyze_copy_variants(
            original_copy=request.original_copy,
            variants=request.variants,
            variant_names=request.variant_names,
            framing_types=request.framing_types,
        )
        data = result.model_dump()
        data["tokens_used"] = deduction.deduction
        data["token_balance_after"] = deduction.balance_after
        return AnalysisResponse(success=True, data=data)
    except Exception as e:
        logger.exception("Copy analysis failed")
        return AnalysisResponse(success=False, error=str(e))

@router.post("/framing-types", response_model=AnalysisResponse)
async def get_framing_types():
    from neuromarketing.copy_analyzer import FRAMING_PROMPTS
    return AnalysisResponse(success=True, data=FRAMING_PROMPTS)
