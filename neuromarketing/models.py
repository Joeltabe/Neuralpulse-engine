from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    video = "video"
    audio = "audio"
    text = "text"


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
    severity: str  # "critical", "moderate", "suggestion"
    category: str  # "visual", "audio", "pacing", "copy", "emotional"
    title: str
    description: str
    suggestion: str
    expected_impact: float = Field(..., ge=0, le=1)


class EmotionState(BaseModel):
    attention: float = Field(..., ge=0, le=1)
    arousal: float = Field(..., ge=0, le=1)
    valence: float = Field(..., ge=0, le=1)
    engagement: float = Field(..., ge=0, le=1)
    cognitive_load: float = Field(..., ge=0, le=1)
    emotional_disengagement: float = Field(..., ge=0, le=1)
    attention_label: str = ""
    arousal_label: str = ""
    valence_label: str = ""
    engagement_label: str = ""
    cognitive_load_label: str = ""
    emotional_disengagement_label: str = ""


class EmotionalEvent(BaseModel):
    timestamp: float
    type: str
    severity: str
    value: Optional[float] = None
    value_before: Optional[float] = None
    value_after: Optional[float] = None
    description: str = ""


class EmotionTimeline(BaseModel):
    dimensions: List[str] = Field(default_factory=lambda: [
        "attention", "arousal", "valence", "engagement",
        "cognitive_load", "emotional_disengagement",
    ])
    timestamps: List[float] = Field(default_factory=list)
    scores: Dict[str, List[float]] = Field(default_factory=dict)
    labels: Dict[str, List[str]] = Field(default_factory=dict)
    events: List[EmotionalEvent] = Field(default_factory=list)
    confidence: Dict[str, Dict[str, List[float]]] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    id: str = ""
    filename: str = ""
    media_type: MediaType
    duration_sec: float = 0.0
    brain_scores: BrainScores
    recommendations: List[Recommendation] = Field(default_factory=list)
    engagement_curve: List[float] = Field(default_factory=list)
    timestamp_axis: List[float] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    summary: str = ""
    overall_grade: str = ""


class VideoAnalysisResult(AnalysisResult):
    media_type: MediaType = MediaType.video
    keyframes: List[Dict[str, Any]] = Field(default_factory=list)
    scene_breaks: List[float] = Field(default_factory=list)
    emotion_timeline: Optional[EmotionTimeline] = None


class AudioAnalysisResult(AnalysisResult):
    media_type: MediaType = MediaType.audio
    transcript_segments: List[Dict[str, Any]] = Field(default_factory=list)
    emotion_timeline: Optional[EmotionTimeline] = None


class TextAnalysisResult(AnalysisResult):
    media_type: MediaType = MediaType.text
    word_level_scores: List[Dict[str, Any]] = Field(default_factory=list)
    sentence_breakdown: List[Dict[str, Any]] = Field(default_factory=list)


class CopyVariant(BaseModel):
    id: str = ""
    name: str = ""
    content: str = ""
    framing_type: str = ""  # "gain", "loss", "urgency", "social_proof", etc.
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


class TimelineFeatures(BaseModel):
    feature_matrix: List[List[float]] = Field(default_factory=list)
    timestamps: List[float] = Field(default_factory=list)
    feature_names: List[str] = Field(default_factory=list)
    video_duration: float = 0.0


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    status: str
    model_loaded: bool
    version: str = "1.0.0"
