from typing import List, Dict, Any
import logging

from .models import BrainScores, Recommendation

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def generate_video_recommendations(
        self,
        scores: BrainScores,
        dropoffs: List[Dict[str, Any]],
        scene_breaks: List[float],
        duration: float,
    ) -> List[Recommendation]:
        recommendations = []

        for drop in dropoffs:
            ts = drop["timestamp_sec"]
            if drop["severity"] == "critical":
                recommendations.append(
                    Recommendation(
                        timestamp_sec=ts,
                        severity="critical",
                        category="attention",
                        title="Critical Attention Drop",
                        description=f"Attention drops {drop['drop_magnitude']:.0%} at {ts:.1f}s. "
                                    f"Viewers are disengaging at this moment.",
                        suggestion="Cut or re-edit frames around this timestamp. "
                                   f"Consider adding a visual transition, changing scene, "
                                   f"or inserting an emotionally compelling element.",
                        expected_impact=0.7,
                    )
                )
            else:
                recommendations.append(
                    Recommendation(
                        timestamp_sec=ts,
                        severity="moderate",
                        category="attention",
                        title="Attention Dip Detected",
                        description=f"Moderate attention decline at {ts:.1f}s.",
                        suggestion="Consider shortening this segment or adding "
                                   f"a visual highlight to re-engage viewers.",
                        expected_impact=0.4,
                    )
                )

        if scores.attention.overall < 0.4:
            recommendations.append(
                Recommendation(
                    timestamp_sec=0,
                    severity="critical",
                    category="hook",
                    title="Weak Opening Hook",
                    description="The first 3 seconds show low attention. You're losing viewers immediately.",
                    suggestion="Front-load your strongest visual or message. "
                               "Use motion, contrast, or an emotionally provocative image "
                               "in the first frame.",
                    expected_impact=0.8,
                )
            )

        if scores.dopamine.overall < 0.4:
            recommendations.append(
                Recommendation(
                    timestamp_sec=duration * 0.5,
                    severity="moderate",
                    category="reward",
                    title="Low Dopamine Response",
                    description="The content does not trigger sufficient reward response.",
                    suggestion="Incorporate benefit-driven messaging. Show product benefits "
                               "with vibrant visuals. Use close-ups of satisfying interactions.",
                    expected_impact=0.6,
                )
            )

        if scores.memory.overall < 0.4:
            recommendations.append(
                Recommendation(
                    timestamp_sec=duration * 0.75,
                    severity="moderate",
                    category="memory",
                    title="Weak Memory Encoding",
                    description="Ending does not reinforce memorability.",
                    suggestion="Add a strong concluding visual, brand logo hold, "
                               "or repeating key message at the end to boost retention.",
                    expected_impact=0.5,
                )
            )

        for sb in scene_breaks:
            recommendations.append(
                Recommendation(
                    timestamp_sec=sb,
                    severity="suggestion",
                    category="pacing",
                    title="Scene Transition",
                    description=f"Scene change at {sb:.1f}s detected.",
                    suggestion="Ensure this transition is smooth. Abrupt cuts can "
                               "cause attention loss. Consider a fade or match cut.",
                    expected_impact=0.3,
                )
            )

        if len(scene_breaks) > 8 and duration > 15:
            avg_scene_len = duration / (len(scene_breaks) + 1)
            if avg_scene_len < 2.0:
                recommendations.append(
                    Recommendation(
                        timestamp_sec=duration * 0.3,
                        severity="moderate",
                        category="pacing",
                        title="Too Many Scene Changes",
                        description=f"Average scene length is {avg_scene_len:.1f}s. "
                                    f"Rapid cutting may overwhelm viewers.",
                        suggestion="Extend scenes to 3-5 seconds for better neural processing. "
                                   "Reduce total number of cuts.",
                        expected_impact=0.5,
                    )
                )

        recommendations.sort(key=lambda r: (
            {"critical": 0, "moderate": 1, "suggestion": 2}[r.severity],
            -r.expected_impact
        ))

        return recommendations

    def generate_audio_recommendations(
        self,
        scores: BrainScores,
        dropoffs: List[Dict[str, Any]],
    ) -> List[Recommendation]:
        recommendations = []

        for drop in dropoffs:
            ts = drop["timestamp_sec"]
            recommendations.append(
                Recommendation(
                    timestamp_sec=ts,
                    severity=drop["severity"],
                    category="audio_attention",
                    title="Auditory Attention Drop",
                    description=f"Listener attention drops at {ts:.1f}s.",
                    suggestion="Consider changing background music, adjusting voice "
                               "tone, or adding a sound effect at this point.",
                    expected_impact=0.6,
                )
            )

        if scores.attention.overall < 0.4:
            recommendations.append(
                Recommendation(
                    timestamp_sec=0,
                    severity="critical",
                    category="audio_hook",
                    title="Weak Audio Hook",
                    description="Opening audio fails to capture attention.",
                    suggestion="Start with a compelling sound, voice modulation, "
                               "or intriguing question. Avoid slow fades.",
                    expected_impact=0.75,
                )
            )

        if scores.dopamine.overall < 0.5:
            recommendations.append(
                Recommendation(
                    timestamp_sec=0,
                    severity="moderate",
                    category="audio_music",
                    title="Low Auditory Reward",
                    description="Background music or voice tone lacks reward triggers.",
                    suggestion="Use uplifting music in major key, vary pace, and "
                               "emphasize positive words with vocal warmth.",
                    expected_impact=0.5,
                )
            )

        return recommendations

    def generate_text_recommendations(
        self,
        scores: BrainScores,
        dropoffs: List[Dict[str, Any]],
        word_scores: List[Dict[str, Any]],
        sentences: List[Dict[str, Any]],
    ) -> List[Recommendation]:
        recommendations = []

        if scores.attention.overall < 0.5:
            recommendations.append(
                Recommendation(
                    timestamp_sec=0,
                    severity="critical",
                    category="copy_hook",
                    title="Weak Headline/Hook",
                    description="Opening words fail to capture neural attention.",
                    suggestion="Rewrite the opening to include power words, "
                               "curiosity gaps, or direct address to the reader. "
                               "Lead with benefit, not description.",
                    expected_impact=0.8,
                )
            )

        if sentences:
            mid_point = len(sentences) // 2
            first_half = sentences[:mid_point]
            second_half = sentences[mid_point:]

            if first_half and second_half:
                avg_first = np_mean([s["avg_attention"] for s in first_half])
                avg_second = np_mean([s["avg_attention"] for s in second_half])

                if avg_second < avg_first - 0.1:
                    recommendations.append(
                        Recommendation(
                            timestamp_sec=0,
                            severity="moderate",
                            category="copy_pacing",
                            title="Attention Fades Mid-Content",
                            description="Reader attention declines in the second half.",
                            suggestion="Break up text with subheadings, bullet points, "
                                       "or short paragraphs. Add emotional triggers throughout.",
                            expected_impact=0.5,
                        )
                    )

        if scores.dopamine.overall < 0.4:
            recommendations.append(
                Recommendation(
                    timestamp_sec=0,
                    severity="moderate",
                    category="copy_reward",
                    title="Low Dopamine Response in Copy",
                    description="Copy lacks reward-triggering language.",
                    suggestion="Emphasize customer benefits, use words like "
                               "'you', 'results', 'transform', 'exclusive', 'proven'. "
                               "Frame around gains rather than features.",
                    expected_impact=0.6,
                )
            )

        weak_memory_words = [
            w for w in word_scores
            if w.get("memory", 0.5) < 0.3
        ]
        if len(weak_memory_words) > len(word_scores) * 0.3:
            recommendations.append(
                Recommendation(
                    timestamp_sec=0,
                    severity="suggestion",
                    category="copy_memory",
                    title="Low Memorability Words",
                    description=f"{len(weak_memory_words)} words score low on memory encoding.",
                    suggestion="Replace abstract or generic words with concrete, "
                               "sensory-rich language. Use metaphors and analogies.",
                    expected_impact=0.4,
                )
            )

        return recommendations


def np_mean(values):
    import numpy as np
    return float(np.mean(values)) if values else 0.0
