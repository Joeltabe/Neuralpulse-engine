from .analyzer import NeuromarketingAnalyzer
from .tribe_adapter import TribeAdapter
from .copy_analyzer import NeuralCopyAnalyzer
from .recommendations import RecommendationEngine
from .ab_testing import ABTestEngine
from .emotion_classifier import EmotionClassifier, compute_emotion_labels, detect_emotional_events
from .video_timeline import TimelineAligner, VideoFeatureExtractor, AudioFeatureExtractor
from .models import (
    AnalysisResult, VideoAnalysisResult, TextAnalysisResult,
    AudioAnalysisResult, ABTestResult, BrainScores,
    AttentionScore, DopamineScore, MemoryScore,
    Recommendation, CopyVariant, CopyAnalysisResult,
    EmotionState, EmotionalEvent, EmotionTimeline, TimelineFeatures
)

try:
    from .signal_processing import (
        EEGPreprocessor, GSRPreprocessor, PupilPreprocessor,
        FixationPreprocessor, BandpassFilter, ICAProcessor,
    )
    _SIGNAL_PROC_AVAILABLE = True
except ImportError as e:
    _SIGNAL_PROC_AVAILABLE = False

try:
    from .eegnet import EEGNet, EEGNetMultiTask, EEGNetFeatureExtractor, EEGClassifier
    _EEGNET_AVAILABLE = True
except ImportError as e:
    _EEGNET_AVAILABLE = False

try:
    from .multimodal_fusion import (
        MultiModalFusion, EngagementVectorPipeline,
        EngagementContrastiveLoss, build_engagement_vector_pipeline,
    )
    _FUSION_AVAILABLE = True
except ImportError as e:
    _FUSION_AVAILABLE = False

try:
    from .engagement_bridge import (
        engagement_vector_to_brain_scores,
        engagement_vector_to_emotion_timeline,
        engagement_vector_to_emotion_states,
        trim_engagement_vector,
    )
    _BRIDGE_AVAILABLE = True
except ImportError as e:
    _BRIDGE_AVAILABLE = False
