from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    video = "video"
    audio = "audio"
    text = "text"


class DopamineTrigger(BaseModel):
    timestamp_sec: float
    trigger_type: str
    intensity: float = Field(..., ge=0, le=1)
    description: str = ""


class VisualDropoff(BaseModel):
    timestamp_sec: float
    drop_magnitude: float = Field(..., ge=0, le=1)
    score_before: float = Field(..., ge=0, le=1)
    score_after: float = Field(..., ge=0, le=1)
    severity: str = "moderate"
    frame_description: str = ""


class Directive(BaseModel):
    priority: str  # "P0", "P1", "P2"
    category: str
    title: str
    action: str
    expected_impact: str
    implementation: str = ""


class FrameAnalysis(BaseModel):
    frame_index: int
    timestamp_sec: float
    attention_score: float
    dopamine_score: float
    memory_score: float
    is_dropoff: bool = False
    is_dopamine_trigger: bool = False
    trigger_type: Optional[str] = None


class AttentionScore(BaseModel):
    overall: float = Field(..., ge=0, le=1)
    temporal_scores: List[float] = Field(default_factory=list)
    peak_moments: List[Dict[str, Any]] = Field(default_factory=list)
    dropoff_moments: List[Dict[str, Any]] = Field(default_factory=list)
    roi_breakdown: Dict[str, float] = Field(default_factory=dict)
    label: str = ""


class DopamineScore(BaseModel):
    overall: float = Field(..., ge=0, le=1)
    temporal_scores: List[float] = Field(default_factory=list)
    reward_peaks: List[Dict[str, Any]] = Field(default_factory=list)
    dopamine_triggers: List[DopamineTrigger] = Field(default_factory=list)
    roi_breakdown: Dict[str, float] = Field(default_factory=dict)
    label: str = ""


class MemoryScore(BaseModel):
    overall: float = Field(..., ge=0, le=1)
    temporal_scores: List[float] = Field(default_factory=list)
    encoding_strength: List[float] = Field(default_factory=list)
    consolidation_potential: float = 0.0
    roi_breakdown: Dict[str, float] = Field(default_factory=dict)
    label: str = ""


class BrainScores(BaseModel):
    attention: AttentionScore
    dopamine: DopamineScore
    memory: MemoryScore


class Recommendation(BaseModel):
    timestamp_sec: float
    severity: str
    category: str
    title: str
    description: str
    suggestion: str
    expected_impact: float = Field(..., ge=0, le=1)


class BenchmarkComparison(BaseModel):
    industry_average: float = 0.0
    top_percentile: float = 0.0
    percentile_rank: Optional[float] = None
    benchmark_label: str = "General Ads"


class AnalysisResult(BaseModel):
    id: str = ""
    filename: str = ""
    media_type: MediaType
    duration_sec: float = 0.0
    brain_scores: BrainScores
    recommendations: List[Recommendation] = Field(default_factory=list)
    directives: List[Directive] = Field(default_factory=list)
    frame_analysis: List[FrameAnalysis] = Field(default_factory=list)
    visual_dropoffs: List[VisualDropoff] = Field(default_factory=list)
    dopamine_triggers: List[DopamineTrigger] = Field(default_factory=list)
    benchmark: Optional[BenchmarkComparison] = None
    engagement_curve: List[float] = Field(default_factory=list)
    timestamp_axis: List[float] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    summary: str = ""
    overall_grade: str = ""


class VideoAnalysisResult(AnalysisResult):
    media_type: MediaType = MediaType.video
    keyframes: List[Dict[str, Any]] = Field(default_factory=list)
    scene_breaks: List[float] = Field(default_factory=list)


class AudioAnalysisResult(AnalysisResult):
    media_type: MediaType = MediaType.audio
    transcript_segments: List[Dict[str, Any]] = Field(default_factory=list)


class TextAnalysisResult(AnalysisResult):
    media_type: MediaType = MediaType.text
    word_level_scores: List[Dict[str, Any]] = Field(default_factory=list)
    sentence_breakdown: List[Dict[str, Any]] = Field(default_factory=list)


class CopyVariant(BaseModel):
    id: str = ""
    name: str = ""
    content: str = ""
    framing_type: str = ""
    brain_scores: Optional[BrainScores] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class CopyAnalysisResult(BaseModel):
    original: CopyVariant
    variants: List[CopyVariant] = []
    comparison: Dict[str, Any] = Field(default_factory=dict)
    winning_variant: Optional[str] = None
    recommendations: List[str] = Field(default_factory=list)


class ABTestResult(BaseModel):
    id: str = ""
    variants: List[AnalysisResult] = Field(default_factory=list)
    winning_variant: Optional[str] = None
    dimension_comparison: Dict[str, List[float]] = Field(default_factory=dict)
    significance_scores: Dict[str, float] = Field(default_factory=dict)
    recommendation: str = ""


class AnalysisRequest(BaseModel):
    media_type: MediaType
    filename: str
    options: Dict[str, Any] = Field(default_factory=dict)


class ABTestRequest(BaseModel):
    variant_files: List[str]
    media_type: MediaType
    variant_names: Optional[List[str]] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class CopyAnalysisRequest(BaseModel):
    original_copy: str
    variants: List[str]
    variant_names: Optional[List[str]] = None
    framing_types: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str = "1.0.0"
