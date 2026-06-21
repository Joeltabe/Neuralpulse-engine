from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from neuromarketing.models import MediaType


class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50000)
    filename: str = "text_input"


class CopyAnalysisRequest(BaseModel):
    original_copy: str = Field(..., min_length=1)
    variants: List[str] = Field(..., min_items=1)
    variant_names: Optional[List[str]] = None
    framing_types: Optional[List[str]] = None


class ABTestTextRequest(BaseModel):
    texts: List[str] = Field(..., min_items=2)
    variant_names: Optional[List[str]] = None


class ABTestFilesRequest(BaseModel):
    media_type: MediaType
    variant_names: Optional[List[str]] = None


class AnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BatchAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None
    error: Optional[str] = None
