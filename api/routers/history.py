import logging
import json
from fastapi import APIRouter, Depends
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from api.database import get_session_maker, AnalysisHistory, User
from api.auth import get_current_user

def get_session():
    return get_session_maker()()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["History"])

class HistoryResponse(BaseModel):
    success: bool
    analyses: Optional[list] = None
    error: Optional[str] = None

@router.get("/analyses", response_model=HistoryResponse)
async def get_analysis_history(user: User = Depends(get_current_user)):
    async with get_session() as session:
        result = await session.execute(
            select(AnalysisHistory)
            .where(AnalysisHistory.user_id == user.id)
            .order_by(AnalysisHistory.created_at.desc())
            .limit(50)
        )
        analyses = result.scalars().all()
        return HistoryResponse(
            success=True,
            analyses=[{
                "id": a.analysis_id,
                "media_type": a.media_type,
                "filename": a.filename,
                "overall_grade": a.overall_grade,
                "attention_score": a.attention_score,
                "dopamine_score": a.dopamine_score,
                "memory_score": a.memory_score,
                "duration_sec": a.duration_sec,
                "tokens_used": a.tokens_used,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "results": json.loads(a.results_json) if a.results_json else None,
            } for a in analyses]
        )

@router.get("/stats", response_model=HistoryResponse)
async def get_usage_stats(user: User = Depends(get_current_user)):
    async with get_session() as session:
        result = await session.execute(
            select(AnalysisHistory)
            .where(AnalysisHistory.user_id == user.id)
        )
        analyses = result.scalars().all()

        total_analyses = len(analyses)
        total_tokens = sum(a.tokens_used for a in analyses)
        by_type = {}
        for a in analyses:
            by_type[a.media_type] = by_type.get(a.media_type, 0) + 1

        return HistoryResponse(
            success=True,
            analyses=[{
                "total_analyses": total_analyses,
                "total_tokens_used": total_tokens,
                "by_type": by_type,
                "token_balance": user.token_balance,
            }]
        )
