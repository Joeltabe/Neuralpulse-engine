import numpy as np
from typing import Dict, List, Optional, Any
import logging

from .models import (
    BrainScores, AttentionScore, DopamineScore, MemoryScore,
    EmotionState, EmotionTimeline, EmotionalEvent,
)
from .emotion_classifier import compute_emotion_labels, detect_emotional_events, EMOTION_DIMENSIONS

logger = logging.getLogger(__name__)


def engagement_vector_to_brain_scores(
    engagement_vectors: np.ndarray,
    timestamps: np.ndarray,
) -> BrainScores:
    if engagement_vectors.ndim == 1:
        engagement_vectors = engagement_vectors.reshape(1, -1)

    dim_128 = engagement_vectors.shape[1]
    proj = engagement_vectors[:, :min(dim_128, 48)]
    if proj.shape[1] < 48:
        proj = np.pad(proj, ((0, 0), (0, 48 - proj.shape[1])), mode="constant")
    proj = proj.reshape(proj.shape[0], 3, 16).mean(axis=2)

    temporal = np.clip(proj, 0, 1)
    temporal_scores = {
        "attention": temporal[:, 0],
        "dopamine": temporal[:, 1],
        "memory": temporal[:, 2],
    }

    attn_scores = temporal_scores["attention"]
    dop_scores = temporal_scores["dopamine"]
    mem_scores = temporal_scores["memory"]

    def find_peaks(scores, min_h=0.6):
        from scipy import signal as scipy_signal
        try:
            peaks, props = scipy_signal.find_peaks(scores, height=min_h, distance=3)
            return [{"index": int(p), "value": float(scores[p]), "timestamp": float(p)} for p in peaks]
        except Exception:
            return []

    def find_dropoffs(scores, thresh=0.3):
        dropoffs = []
        for i in range(1, len(scores)):
            if scores[i] < thresh and scores[i - 1] >= thresh:
                dropoffs.append({
                    "index": i, "value_before": float(scores[i - 1]),
                    "value_after": float(scores[i]), "timestamp": float(i),
                })
        return dropoffs

    attention = AttentionScore(
        overall=float(np.mean(attn_scores)),
        temporal_scores=attn_scores.tolist(),
        peak_moments=find_peaks(attn_scores),
        dropoff_moments=find_dropoffs(attn_scores),
        label="High Attention" if np.mean(attn_scores) >= 0.6 else
              "Moderate Attention" if np.mean(attn_scores) >= 0.35 else "Low Attention",
    )

    dopamine = DopamineScore(
        overall=float(np.mean(dop_scores)),
        temporal_scores=dop_scores.tolist(),
        reward_peaks=find_peaks(dop_scores, 0.65),
        label="High Dopamine Response" if np.mean(dop_scores) >= 0.55 else
              "Moderate Dopamine Response" if np.mean(dop_scores) >= 0.3 else "Low Dopamine Response",
    )

    memory = MemoryScore(
        overall=float(np.mean(mem_scores)),
        temporal_scores=mem_scores.tolist(),
        encoding_strength=mem_scores.tolist(),
        consolidation_potential=float(np.mean(mem_scores[-max(1, len(mem_scores) // 3):])),
        label="High Memory Encoding" if np.mean(mem_scores) >= 0.55 else
              "Moderate Memory Encoding" if np.mean(mem_scores) >= 0.3 else "Low Memory Encoding",
    )

    return BrainScores(attention=attention, dopamine=dopamine, memory=memory)


def engagement_vector_to_emotion_timeline(
    engagement_vectors: np.ndarray,
    timestamps: np.ndarray,
) -> EmotionTimeline:
    if engagement_vectors.ndim == 1:
        engagement_vectors = engagement_vectors.reshape(1, -1)

    dim_128 = engagement_vectors.shape[1]
    preds: Dict[str, np.ndarray] = {}
    for i, dim in enumerate(EMOTION_DIMENSIONS):
        if i < dim_128:
            preds[dim] = engagement_vectors[:, i]
        else:
            preds[dim] = np.full(engagement_vectors.shape[0], 0.5)

    labels = compute_emotion_labels(preds)
    events_raw = detect_emotional_events(preds, timestamps)
    events = [EmotionalEvent(**e) if isinstance(e, dict) else e for e in events_raw]

    scores = {dim: vals.tolist() for dim, vals in preds.items()}
    labels_out = {dim: list(vals) for dim, vals in labels.items()}

    return EmotionTimeline(
        timestamps=timestamps.tolist(),
        scores=scores,
        labels=labels_out,
        events=events,
    )


def engagement_vector_to_emotion_states(
    engagement_vectors: np.ndarray,
    timestamps: np.ndarray,
) -> List[EmotionState]:
    if engagement_vectors.ndim == 1:
        engagement_vectors = engagement_vectors.reshape(1, -1)

    dim_128 = engagement_vectors.shape[1]
    states = []

    for i in range(engagement_vectors.shape[0]):
        state_kwargs = {dim: float(engagement_vectors[i, min(j, dim_128 - 1)])
                        for j, dim in enumerate(EMOTION_DIMENSIONS[:6])}

        for j, dim in enumerate(EMOTION_DIMENSIONS[:6]):
            val = engagement_vectors[i, min(j, dim_128 - 1)]
            label = _emotion_label(dim, float(val))
            state_kwargs[f"{dim}_label"] = label

        states.append(EmotionState(**state_kwargs))

    return states


def _emotion_label(dim: str, value: float) -> str:
    from .emotion_classifier import EMOTION_LABELS
    buckets = EMOTION_LABELS.get(dim, [])
    for lo, hi, label in buckets:
        if lo <= value < hi:
            return label
    return buckets[-1][2] if buckets else ""


def trim_engagement_vector(
    engagement_vectors: np.ndarray,
    target_dim: int = 128,
) -> np.ndarray:
    current = engagement_vectors.shape[-1]
    if current == target_dim:
        return engagement_vectors
    if current > target_dim:
        return engagement_vectors[..., :target_dim]
    padded = np.zeros((*engagement_vectors.shape[:-1], target_dim), dtype=engagement_vectors.dtype)
    padded[..., :current] = engagement_vectors
    return padded
