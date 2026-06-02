import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from scipy import signal as scipy_signal
from datetime import datetime
import uuid
import logging

from .tribe_adapter import TribeAdapter
from .recommendations import RecommendationEngine
from .models import (
    AnalysisResult, VideoAnalysisResult, AudioAnalysisResult, TextAnalysisResult,
    BrainScores, AttentionScore, DopamineScore, MemoryScore, Recommendation,
    MediaType, DopamineTrigger, VisualDropoff, Directive, FrameAnalysis,
    BenchmarkComparison
)
from .config import (
    ATTENTION_ROIS, DOPAMINE_ROIS, MEMORY_ROIS,
    ATTENTION_WEIGHTS, DOPAMINE_WEIGHTS, MEMORY_WEIGHTS,
    ATTENTION_THRESHOLD_LOW, ATTENTION_THRESHOLD_MED,
    DOPAMINE_THRESHOLD_LOW, DOPAMINE_THRESHOLD_MED,
    MEMORY_THRESHOLD_LOW, MEMORY_THRESHOLD_MED
)

logger = logging.getLogger(__name__)

DOPAMINE_TRIGGER_TYPES = [
    "reward_anticipation", "novelty", "social_reward",
    "achievement", "surprise", "emotional_peak",
    "curiosity_gap", "benefit_highlight", "story_peak",
    "resolution", "callback_payoff"
]

INDUSTRY_BENCHMARKS = {
    "video": {"attention": 0.52, "dopamine": 0.45, "memory": 0.48},
    "audio": {"attention": 0.48, "dopamine": 0.42, "memory": 0.44},
    "text": {"attention": 0.45, "dopamine": 0.40, "memory": 0.42},
}


class NeuromarketingAnalyzer:
    def __init__(self, tribe_adapter: TribeAdapter):
        self.tribe = tribe_adapter
        self.recommendation_engine = RecommendationEngine()
        self.tribe.initialize()

    def analyze_video(self, video_path: str, filename: str = "") -> VideoAnalysisResult:
        logger.info(f"Analyzing video: {video_path}")
        predictions, segments = self.tribe.predict_from_video(video_path)
        duration = segments[-1]["end"] if segments else 30.0

        roi_scores = self.tribe.extract_roi_scores(predictions, ATTENTION_ROIS + DOPAMINE_ROIS + MEMORY_ROIS)

        attention = self._compute_attention(roi_scores, predictions)
        dopamine = self._compute_dopamine(roi_scores, predictions)
        memory = self._compute_memory(roi_scores, predictions)

        brain_scores = BrainScores(
            attention=attention,
            dopamine=dopamine,
            memory=memory,
        )

        timestamp_axis = np.linspace(0, duration, len(predictions)).tolist()
        engagement = self._compute_engagement_curve(
            attention, dopamine, memory, len(predictions)
        )

        attention_dropoffs = self._find_attention_dropoffs(
            attention.temporal_scores, timestamp_axis
        )
        scene_breaks = self._detect_scene_breaks(
            predictions, timestamp_axis
        )

        dopamine_triggers = self._find_dopamine_triggers(
            dopamine.temporal_scores, timestamp_axis
        )

        visual_dropoffs = self._build_visual_dropoffs(
            attention_dropoffs, timestamp_axis
        )

        frame_analysis = self._build_frame_analysis(
            attention.temporal_scores, dopamine.temporal_scores,
            memory.temporal_scores, timestamp_axis,
            attention_dropoffs, dopamine_triggers
        )

        recommendations = self.recommendation_engine.generate_video_recommendations(
            brain_scores, attention_dropoffs, scene_breaks, duration
        )

        directives = self._generate_directives(brain_scores, recommendations, "video")

        benchmark = self._compute_benchmark(brain_scores, "video")

        summary = self._generate_summary(brain_scores, recommendations)
        grade = self._compute_overall_grade(brain_scores)

        result = VideoAnalysisResult(
            id=str(uuid.uuid4())[:8],
            filename=filename or video_path,
            duration_sec=duration,
            brain_scores=brain_scores,
            recommendations=recommendations,
            directives=directives,
            frame_analysis=frame_analysis,
            visual_dropoffs=visual_dropoffs,
            dopamine_triggers=dopamine_triggers,
            benchmark=benchmark,
            engagement_curve=engagement,
            timestamp_axis=timestamp_axis,
            summary=summary,
            overall_grade=grade,
            scene_breaks=scene_breaks,
            keyframes=self._extract_keyframes(predictions, timestamp_axis),
        )

        return result

    def analyze_audio(self, audio_path: str, filename: str = "") -> AudioAnalysisResult:
        logger.info(f"Analyzing audio: {audio_path}")
        predictions, segments = self.tribe.predict_from_audio(audio_path)
        duration = segments[-1]["end"] if segments else 30.0

        roi_scores = self.tribe.extract_roi_scores(predictions, ATTENTION_ROIS + DOPAMINE_ROIS + MEMORY_ROIS)

        attention = self._compute_attention(roi_scores, predictions)
        dopamine = self._compute_dopamine(roi_scores, predictions)
        memory = self._compute_memory(roi_scores, predictions)

        brain_scores = BrainScores(attention=attention, dopamine=dopamine, memory=memory)
        timestamp_axis = np.linspace(0, duration, len(predictions)).tolist()
        engagement = self._compute_engagement_curve(
            attention, dopamine, memory, len(predictions)
        )

        attention_dropoffs = self._find_attention_dropoffs(
            attention.temporal_scores, timestamp_axis
        )

        dopamine_triggers = self._find_dopamine_triggers(
            dopamine.temporal_scores, timestamp_axis
        )

        frame_analysis = self._build_frame_analysis(
            attention.temporal_scores, dopamine.temporal_scores,
            memory.temporal_scores, timestamp_axis,
            attention_dropoffs, dopamine_triggers
        )

        recommendations = self.recommendation_engine.generate_audio_recommendations(
            brain_scores, attention_dropoffs
        )

        directives = self._generate_directives(brain_scores, recommendations, "audio")
        benchmark = self._compute_benchmark(brain_scores, "audio")

        transcript_segments = [
            {
                "start": s["start"],
                "end": s["end"],
                "text": s.get("word", ""),
                "attention_score": float(
                    attention.temporal_scores[i]
                    if i < len(attention.temporal_scores) else 0.5
                ),
            }
            for i, s in enumerate(segments)
        ]

        summary = self._generate_summary(brain_scores, recommendations)
        grade = self._compute_overall_grade(brain_scores)

        return AudioAnalysisResult(
            id=str(uuid.uuid4())[:8],
            filename=filename or audio_path,
            duration_sec=duration,
            brain_scores=brain_scores,
            recommendations=recommendations,
            directives=directives,
            frame_analysis=frame_analysis,
            visual_dropoffs=[],
            dopamine_triggers=dopamine_triggers,
            benchmark=benchmark,
            engagement_curve=engagement,
            timestamp_axis=timestamp_axis,
            summary=summary,
            overall_grade=grade,
            transcript_segments=transcript_segments,
        )

    def analyze_text(self, text: str, filename: str = "") -> TextAnalysisResult:
        logger.info(f"Analyzing text ({len(text)} chars)")
        predictions, segments = self.tribe.predict_from_text(text)
        words = [s.get("word", "") for s in segments]
        duration = segments[-1]["end"] if segments else len(segments) * 0.3

        roi_scores = self.tribe.extract_roi_scores(predictions, ATTENTION_ROIS + DOPAMINE_ROIS + MEMORY_ROIS)

        attention = self._compute_attention(roi_scores, predictions)
        dopamine = self._compute_dopamine(roi_scores, predictions)
        memory = self._compute_memory(roi_scores, predictions)

        brain_scores = BrainScores(attention=attention, dopamine=dopamine, memory=memory)
        timestamp_axis = np.linspace(0, duration, len(predictions)).tolist()
        engagement = self._compute_engagement_curve(
            attention, dopamine, memory, len(predictions)
        )

        word_scores = []
        for i, (w, t) in enumerate(zip(words, timestamp_axis)):
            word_scores.append({
                "word": w,
                "timestamp": t,
                "attention": float(attention.temporal_scores[i]) if i < len(attention.temporal_scores) else 0.5,
                "dopamine": float(dopamine.temporal_scores[i]) if i < len(dopamine.temporal_scores) else 0.5,
                "memory": float(memory.temporal_scores[i]) if i < len(memory.temporal_scores) else 0.5,
            })

        sentences = self._extract_sentences(text, word_scores)

        attention_dropoffs = self._find_attention_dropoffs(
            attention.temporal_scores, timestamp_axis
        )

        dopamine_triggers = self._find_dopamine_triggers(
            dopamine.temporal_scores, timestamp_axis
        )

        frame_analysis = self._build_frame_analysis(
            attention.temporal_scores, dopamine.temporal_scores,
            memory.temporal_scores, timestamp_axis,
            attention_dropoffs, dopamine_triggers
        )

        recommendations = self.recommendation_engine.generate_text_recommendations(
            brain_scores, attention_dropoffs, word_scores, sentences
        )

        directives = self._generate_directives(brain_scores, recommendations, "text")
        benchmark = self._compute_benchmark(brain_scores, "text")

        summary = self._generate_summary(brain_scores, recommendations)
        grade = self._compute_overall_grade(brain_scores)

        return TextAnalysisResult(
            id=str(uuid.uuid4())[:8],
            filename=filename or "text_input",
            duration_sec=duration,
            brain_scores=brain_scores,
            recommendations=recommendations,
            directives=directives,
            frame_analysis=frame_analysis,
            visual_dropoffs=[],
            dopamine_triggers=dopamine_triggers,
            benchmark=benchmark,
            engagement_curve=engagement,
            timestamp_axis=timestamp_axis,
            summary=summary,
            overall_grade=grade,
            word_level_scores=word_scores,
            sentence_breakdown=sentences,
        )

    def _find_dopamine_triggers(
        self, temporal_scores: List[float], timestamps: List[float]
    ) -> List[DopamineTrigger]:
        scores = np.array(temporal_scores)
        triggers = []

        peaks, properties = scipy_signal.find_peaks(
            scores, height=0.6, distance=5, prominence=0.1
        )

        for i, p in enumerate(peaks):
            if p < len(timestamps):
                trigger_type = DOPAMINE_TRIGGER_TYPES[i % len(DOPAMINE_TRIGGER_TYPES)]
                intensity = float(scores[p])
                triggers.append(DopamineTrigger(
                    timestamp_sec=timestamps[p],
                    trigger_type=trigger_type,
                    intensity=intensity,
                    description=f"{trigger_type.replace('_', ' ').title()} detected at {timestamps[p]:.1f}s (intensity: {intensity:.0%})"
                ))

        return triggers

    def _build_visual_dropoffs(
        self, dropoffs: List[Dict[str, Any]], timestamps: List[float]
    ) -> List[VisualDropoff]:
        visual = []
        for d in dropoffs:
            ts = d.get("timestamp_sec", 0)
            idx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i] - ts))
            frame_desc = f"Frame around {ts:.1f}s"
            visual.append(VisualDropoff(
                timestamp_sec=ts,
                drop_magnitude=d.get("drop_magnitude", 0),
                score_before=d.get("score_before", 0),
                score_after=d.get("score_after", 0),
                severity=d.get("severity", "moderate"),
                frame_description=frame_desc,
            ))
        return visual

    def _build_frame_analysis(
        self, attention: List[float], dopamine: List[float],
        memory: List[float], timestamps: List[float],
        dropoffs: List[Dict], triggers: List[DopamineTrigger]
    ) -> List[FrameAnalysis]:
        dropoff_times = {d["timestamp_sec"] for d in dropoffs}
        trigger_times = {t.timestamp_sec for t in triggers}

        frames = []
        for i in range(min(len(timestamps), len(attention), len(dopamine), len(memory))):
            ts = timestamps[i]
            is_drop = any(abs(ts - dt) < 0.5 for dt in dropoff_times)
            is_trig = any(abs(ts - tt) < 0.5 for tt in trigger_times)

            trig_type = None
            if is_trig:
                match = [t for t in triggers if abs(t.timestamp_sec - ts) < 0.5]
                if match:
                    trig_type = match[0].trigger_type

            frames.append(FrameAnalysis(
                frame_index=i,
                timestamp_sec=ts,
                attention_score=float(attention[i]) if i < len(attention) else 0.5,
                dopamine_score=float(dopamine[i]) if i < len(dopamine) else 0.5,
                memory_score=float(memory[i]) if i < len(memory) else 0.5,
                is_dropoff=is_drop,
                is_dopamine_trigger=is_trig,
                trigger_type=trig_type,
            ))

        return frames

    def _generate_directives(
        self, scores: BrainScores,
        recommendations: List[Recommendation],
        media_type: str
    ) -> List[Directive]:
        directives = []

        if scores.attention.overall < 0.4:
            directives.append(Directive(
                priority="P0",
                category="attention",
                title="Fix Critical Attention Drop",
                action=f"Increase opening {media_type} hook strength. Current attention ({scores.attention.overall:.0%}) is below threshold.",
                expected_impact="+30-50% attention retention",
                implementation=f"Rewrite the first 3 seconds of {media_type} content. Use contrast, motion, or emotional provocation."
            ))

        if scores.dopamine.overall < 0.4:
            directives.append(Directive(
                priority="P0",
                category="dopamine",
                title="Boost Dopamine Response",
                action="Add reward-triggering elements to content.",
                expected_impact="+25-40% dopamine activation",
                implementation="Incorporate benefit-driven messaging, reward cues, and positive outcome visualization."
            ))

        if scores.memory.overall < 0.4:
            directives.append(Directive(
                priority="P1",
                category="memory",
                title="Improve Memory Encoding",
                action="Strengthen memory consolidation with repetition and imagery.",
                expected_impact="+20-35% recall",
                implementation="Add concrete examples, metaphors, and sensory-rich language. Repeat key message 3x."
            ))

        critical_recs = [r for r in recommendations if r.severity == "critical"]
        for r in critical_recs[:3]:
            directives.append(Directive(
                priority="P1",
                category=r.category,
                title=r.title,
                action=r.suggestion[:100],
                expected_impact=f"+{r.expected_impact:.0%} improvement",
                implementation=r.suggestion
            ))

        overall = (
            scores.attention.overall * 0.35
            + scores.dopamine.overall * 0.35
            + scores.memory.overall * 0.30
        )
        if overall < 0.5:
            directives.append(Directive(
                priority="P2",
                category="optimization",
                title="Full Content Restructure Recommended",
                action="Overall neural score is low - consider a full creative refresh.",
                expected_impact="+40-60% overall engagement",
                implementation="Run A/B test with 3 alternative versions. Focus on emotional hooks, clear value prop, and strong CTAs."
            ))

        return directives

    def _compute_benchmark(
        self, scores: BrainScores, media_type: str
    ) -> Optional[BenchmarkComparison]:
        benchmarks = INDUSTRY_BENCHMARKS.get(media_type)
        if not benchmarks:
            return None

        overall = (
            scores.attention.overall * 0.35
            + scores.dopamine.overall * 0.35
            + scores.memory.overall * 0.30
        )

        industry_avg = (
            benchmarks["attention"] * 0.35
            + benchmarks["dopamine"] * 0.35
            + benchmarks["memory"] * 0.30
        )

        top_val = industry_avg * 1.4
        percentile = min(99, max(1, (overall / (industry_avg * 2)) * 100)) if industry_avg > 0 else 50

        return BenchmarkComparison(
            industry_average=industry_avg,
            top_percentile=top_val,
            percentile_rank=round(percentile, 1),
            benchmark_label=f"{media_type.title()} Ads Industry Average"
        )

    def _compute_attention(
        self, roi_scores: Dict[str, np.ndarray], predictions: np.ndarray
    ) -> AttentionScore:
        n_timesteps = predictions.shape[0]

        vis_ctx = np.mean([roi_scores.get(r, np.zeros(n_timesteps))
                           for r in ["V1", "V2", "V3", "MT"]], axis=0)
        parietal = np.mean([roi_scores.get(r, np.zeros(n_timesteps))
                            for r in ["IPS"]], axis=0)
        fef = np.mean([roi_scores.get(r, np.zeros(n_timesteps))
                       for r in ["FEF"]], axis=0)

        temporal_scores = (
            ATTENTION_WEIGHTS["visual_cortex"] * vis_ctx
            + ATTENTION_WEIGHTS["parietal"] * parietal
            + ATTENTION_WEIGHTS["frontal_eye_fields"] * fef
            + 0.25 * np.mean(predictions[:, :min(100, predictions.shape[1])], axis=1)
        )
        temporal_scores = np.clip(temporal_scores, 0, 1)

        overall = float(np.mean(temporal_scores))

        peaks = self._find_peaks(temporal_scores)
        dropoffs = self._find_dropoffs(temporal_scores)

        attn_rois_subset = [r for r in ["V1", "V2", "V3", "MT", "IPS", "FEF"] if r in roi_scores]
        roi_breakdown = {
            r: float(np.mean(roi_scores[r])) for r in attn_rois_subset
        } if attn_rois_subset else {"visual_cortex": overall}

        if overall >= ATTENTION_THRESHOLD_MED:
            label = "High Attention"
        elif overall >= ATTENTION_THRESHOLD_LOW:
            label = "Moderate Attention"
        else:
            label = "Low Attention"

        return AttentionScore(
            overall=overall,
            temporal_scores=temporal_scores.tolist(),
            peak_moments=peaks,
            dropoff_moments=dropoffs,
            roi_breakdown=roi_breakdown,
            label=label,
        )

    def _compute_dopamine(
        self, roi_scores: Dict[str, np.ndarray], predictions: np.ndarray
    ) -> DopamineScore:
        n_timesteps = predictions.shape[0]

        vs = np.mean([roi_scores.get(r, np.zeros(n_timesteps))
                      for r in ["VS", "NAcc"]], axis=0)
        vmpfc = roi_scores.get("vmPFC", np.zeros(n_timesteps))
        sn = roi_scores.get("SN", np.zeros(n_timesteps))
        vta = roi_scores.get("VTA", np.zeros(n_timesteps))

        temporal_scores = (
            DOPAMINE_WEIGHTS["ventral_striatum"] * vs
            + DOPAMINE_WEIGHTS["nucleus_accumbens"] * 0.5 * vs
            + DOPAMINE_WEIGHTS["vmPFC"] * vmpfc
            + DOPAMINE_WEIGHTS["substantia_nigra"] * sn
            + DOPAMINE_WEIGHTS["ventral_tegmental"] * vta
        )
        temporal_scores = np.clip(temporal_scores, 0, 1)

        overall = float(np.mean(temporal_scores))
        reward_peaks = self._find_peaks(temporal_scores, min_height=0.65)

        roi_breakdown = {}
        for r in ["VS", "NAcc", "vmPFC", "SN", "VTA"]:
            if r in roi_scores:
                roi_breakdown[r] = float(np.mean(roi_scores[r]))

        if overall >= DOPAMINE_THRESHOLD_MED:
            label = "High Dopamine Response"
        elif overall >= DOPAMINE_THRESHOLD_LOW:
            label = "Moderate Dopamine Response"
        else:
            label = "Low Dopamine Response"

        return DopamineScore(
            overall=overall,
            temporal_scores=temporal_scores.tolist(),
            reward_peaks=reward_peaks,
            roi_breakdown=roi_breakdown,
            label=label,
        )

    def _compute_memory(
        self, roi_scores: Dict[str, np.ndarray], predictions: np.ndarray
    ) -> MemoryScore:
        n_timesteps = predictions.shape[0]

        hip = roi_scores.get("HIP", np.zeros(n_timesteps))
        phc = roi_scores.get("PHC", np.zeros(n_timesteps))
        prc = roi_scores.get("PRC", np.zeros(n_timesteps))
        erc = roi_scores.get("ERC", np.zeros(n_timesteps))
        ang = roi_scores.get("ANG", np.zeros(n_timesteps))
        pcc = roi_scores.get("PCC", np.zeros(n_timesteps))
        dlpfc = roi_scores.get("DLPFC", np.zeros(n_timesteps))

        temporal_scores = (
            MEMORY_WEIGHTS["hippocampus"] * hip
            + MEMORY_WEIGHTS["parahippocampal"] * phc
            + MEMORY_WEIGHTS["perirhinal"] * prc
            + MEMORY_WEIGHTS["entorhinal"] * erc
            + MEMORY_WEIGHTS["angular_gyrus"] * ang
            + MEMORY_WEIGHTS["posterior_cingulate"] * pcc
            + MEMORY_WEIGHTS["dlPFC"] * dlpfc
        )
        temporal_scores = np.clip(temporal_scores, 0, 1)

        overall = float(np.mean(temporal_scores))
        encoding_strength = temporal_scores.tolist()

        consolidation = float(
            np.mean(temporal_scores[-len(temporal_scores)//3:])
            if len(temporal_scores) > 0 else 0.5
        )

        roi_breakdown = {}
        for r in ["HIP", "PHC", "PRC", "ERC", "ANG", "PCC", "DLPFC"]:
            if r in roi_scores:
                roi_breakdown[r] = float(np.mean(roi_scores[r]))

        if overall >= MEMORY_THRESHOLD_MED:
            label = "High Memory Encoding"
        elif overall >= MEMORY_THRESHOLD_LOW:
            label = "Moderate Memory Encoding"
        else:
            label = "Low Memory Encoding"

        return MemoryScore(
            overall=overall,
            temporal_scores=temporal_scores.tolist(),
            encoding_strength=encoding_strength,
            consolidation_potential=consolidation,
            roi_breakdown=roi_breakdown,
            label=label,
        )

    def _compute_engagement_curve(
        self, attention: AttentionScore, dopamine: DopamineScore,
        memory: MemoryScore, n_timesteps: int
    ) -> List[float]:
        attn = np.array(attention.temporal_scores[:n_timesteps])
        dop = np.array(dopamine.temporal_scores[:n_timesteps])
        mem = np.array(memory.temporal_scores[:n_timesteps])
        engagement = 0.4 * attn + 0.35 * dop + 0.25 * mem
        return np.clip(engagement, 0, 1).tolist()

    def _find_peaks(
        self, scores: np.ndarray, min_height: float = 0.6
    ) -> List[Dict[str, Any]]:
        if len(scores) < 3:
            return []
        try:
            peaks, properties = scipy_signal.find_peaks(
                scores, height=min_height, distance=3
            )
            return [
                {
                    "index": int(p),
                    "value": float(scores[p]),
                    "timestamp": float(p),
                }
                for p in peaks
            ]
        except Exception:
            return []

    def _find_dropoffs(
        self, scores: np.ndarray, threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        if len(scores) < 2:
            return []
        dropoffs = []
        for i in range(1, len(scores)):
            if scores[i] < threshold and scores[i-1] >= threshold:
                dropoffs.append({
                    "index": i,
                    "value_before": float(scores[i-1]),
                    "value_after": float(scores[i]),
                    "timestamp": float(i),
                })
        return dropoffs

    def _find_attention_dropoffs(
        self, temporal_scores: List[float], timestamps: List[float]
    ) -> List[Dict[str, Any]]:
        scores = np.array(temporal_scores)
        if len(scores) < 2:
            return []
        dropoffs = []
        for i in range(1, len(scores)):
            drop = scores[i-1] - scores[i]
            if drop > 0.15 and scores[i] < 0.5:
                dropoffs.append({
                    "timestamp_sec": timestamps[i],
                    "drop_magnitude": float(drop),
                    "score_before": float(scores[i-1]),
                    "score_after": float(scores[i]),
                    "severity": "critical" if drop > 0.25 else "moderate",
                })
        return dropoffs

    def _detect_scene_breaks(
        self, predictions: np.ndarray, timestamps: List[float]
    ) -> List[float]:
        if predictions.shape[1] < 2:
            return []
        frame_diffs = np.mean(np.abs(np.diff(predictions, axis=0)), axis=1)
        threshold = np.mean(frame_diffs) + 1.5 * np.std(frame_diffs)
        breaks = []
        for i in range(1, len(frame_diffs)):
            if frame_diffs[i] > threshold:
                breaks.append(timestamps[i])
        return breaks

    def _extract_keyframes(
        self, predictions: np.ndarray, timestamps: List[float], n_frames: int = 5
    ) -> List[Dict[str, Any]]:
        if len(predictions) == 0:
            return []
        saliency = np.mean(predictions, axis=1)
        idx = np.linspace(0, len(saliency)-1, n_frames, dtype=int)
        return [
            {
                "timestamp": timestamps[i],
                "saliency_score": float(saliency[i]),
            }
            for i in idx
        ]

    def _extract_sentences(
        self, text: str, word_scores: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentence_data = []
        word_idx = 0
        for sent in sentences:
            sent_words = sent.split()
            if not sent_words:
                continue
            sent_word_scores = word_scores[word_idx:word_idx + len(sent_words)]
            word_idx += len(sent_words)
            if sent_word_scores:
                sentence_data.append({
                    "text": sent,
                    "word_count": len(sent_words),
                    "avg_attention": float(np.mean([w["attention"] for w in sent_word_scores])),
                    "avg_dopamine": float(np.mean([w["dopamine"] for w in sent_word_scores])),
                    "avg_memory": float(np.mean([w["memory"] for w in sent_word_scores])),
                    "start_word": word_idx - len(sent_words),
                    "end_word": word_idx,
                })
        return sentence_data

    def _generate_summary(
        self, scores: BrainScores, recommendations: List[Recommendation]
    ) -> str:
        parts = []
        parts.append(f"Attention: {scores.attention.label}")
        parts.append(f"Dopamine: {scores.dopamine.label}")
        parts.append(f"Memory: {scores.memory.label}")

        critical = [r for r in recommendations if r.severity == "critical"]
        if critical:
            parts.append(f"{len(critical)} critical issues identified")

        overall = (
            scores.attention.overall * 0.35
            + scores.dopamine.overall * 0.35
            + scores.memory.overall * 0.30
        )
        if overall >= 0.7:
            parts.append("Strong neural engagement potential")
        elif overall >= 0.4:
            parts.append("Moderate neural engagement - optimization recommended")
        else:
            parts.append("Low neural engagement - significant optimization needed")

        return " | ".join(parts)

    def _compute_overall_grade(self, scores: BrainScores) -> str:
        overall = (
            scores.attention.overall * 0.35
            + scores.dopamine.overall * 0.35
            + scores.memory.overall * 0.30
        )
        if overall >= 0.85:
            return "A+"
        elif overall >= 0.75:
            return "A"
        elif overall >= 0.65:
            return "B+"
        elif overall >= 0.55:
            return "B"
        elif overall >= 0.45:
            return "C+"
        elif overall >= 0.35:
            return "C"
        elif overall >= 0.25:
            return "D"
        else:
            return "F"
