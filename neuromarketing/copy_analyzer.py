import numpy as np
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import logging

from .tribe_adapter import TribeAdapter
from .analyzer import NeuromarketingAnalyzer
from .models import (
    CopyAnalysisResult, CopyVariant, BrainScores, AttentionScore,
    DopamineScore, MemoryScore, Recommendation, TextAnalysisResult
)

logger = logging.getLogger(__name__)


FRAMING_PROMPTS = {
    "gain": "Focus on what the customer gains, benefits, and positive outcomes.",
    "loss": "Focus on what the customer might miss out on or lose.",
    "urgency": "Focus on scarcity, limited time, and immediate action.",
    "social_proof": "Focus on what others are doing, endorsements, and popularity.",
    "authority": "Focus on expertise, credentials, and authoritative sources.",
    "reciprocity": "Focus on what is being given freely before asking.",
    "curiosity": "Focus on gaps in knowledge, intrigue, and悬念.",
    "pain_point": "Focus on the problem the customer is experiencing.",
    "aspirational": "Focus on the ideal future state and identity.",
}


class NeuralCopyAnalyzer:
    def __init__(self, tribe_adapter: TribeAdapter):
        self.tribe = tribe_adapter
        self.analyzer = NeuromarketingAnalyzer(tribe_adapter)

    def analyze_copy_variants(
        self,
        original_copy: str,
        variants: List[str],
        variant_names: Optional[List[str]] = None,
        framing_types: Optional[List[str]] = None,
    ) -> CopyAnalysisResult:
        logger.info(f"Analyzing {len(variants)+1} copy variants")

        original_result = self.analyzer.analyze_text(original_copy, "original")
        original_variant = CopyVariant(
            id=str(uuid.uuid4())[:8],
            name="Original",
            content=original_copy,
            framing_type="original",
            brain_scores=original_result.brain_scores,
        )

        variant_results = []
        for i, var_text in enumerate(variants):
            name = variant_names[i] if variant_names and i < len(variant_names) else f"Variant {i+1}"
            ftype = framing_types[i] if framing_types and i < len(framing_types) else "unknown"
            result = self.analyzer.analyze_text(var_text, name)
            variant_results.append(
                CopyVariant(
                    id=str(uuid.uuid4())[:8],
                    name=name,
                    content=var_text,
                    framing_type=ftype,
                    brain_scores=result.brain_scores,
                )
            )

        all_variants = [original_variant] + variant_results
        comparison = self._build_comparison(all_variants)
        winner = self._determine_winner(all_variants)
        recommendations = self._generate_copy_recommendations(
            all_variants, comparison
        )

        return CopyAnalysisResult(
            original=original_variant,
            variants=variant_results,
            comparison=comparison,
            winning_variant=winner,
            recommendations=recommendations,
        )

    def _build_comparison(
        self, variants: List[CopyVariant]
    ) -> Dict[str, Any]:
        comparison = {
            "dimensions": ["attention", "dopamine", "memory"],
            "scores": {},
        }
        for v in variants:
            if v.brain_scores:
                comparison["scores"][v.name] = {
                    "attention": v.brain_scores.attention.overall,
                    "dopamine": v.brain_scores.dopamine.overall,
                    "memory": v.brain_scores.memory.overall,
                    "overall": (
                        v.brain_scores.attention.overall * 0.35
                        + v.brain_scores.dopamine.overall * 0.35
                        + v.brain_scores.memory.overall * 0.30
                    ),
                    "framing": v.framing_type,
                }

        if len(variants) >= 2:
            dims = ["attention", "dopamine", "memory"]
            comparison["wins"] = {d: self._count_wins(variants, d) for d in dims}

        return comparison

    def _count_wins(self, variants: List[CopyVariant], dimension: str) -> Dict[str, int]:
        counts = {}
        for v in variants:
            if v.brain_scores:
                score = getattr(v.brain_scores, dimension).overall
                counts[v.name] = sum(
                    1 for v2 in variants
                    if v2.brain_scores
                    and getattr(v2.brain_scores, dimension).overall < score
                )
        return counts

    def _determine_winner(self, variants: List[CopyVariant]) -> Optional[str]:
        if not variants:
            return None
        best = None
        best_score = -1
        for v in variants:
            if v.brain_scores:
                overall = (
                    v.brain_scores.attention.overall * 0.35
                    + v.brain_scores.dopamine.overall * 0.35
                    + v.brain_scores.memory.overall * 0.30
                )
                if overall > best_score:
                    best_score = overall
                    best = v.name
        return best

    def _generate_copy_recommendations(
        self,
        variants: List[CopyVariant],
        comparison: Dict[str, Any],
    ) -> List[str]:
        recommendations = []

        if not variants or not variants[0].brain_scores:
            return ["No data available for recommendations."]

        baseline = variants[0]

        if baseline.brain_scores.attention.overall < 0.5:
            recommendations.append(
                "Lead with a stronger hook in the first 3 seconds to capture attention. "
                "Consider a surprising statistic, bold claim, or emotionally charged question."
            )

        if baseline.brain_scores.dopamine.overall < 0.4:
            recommendations.append(
                "Incorporate reward-triggering language by emphasizing benefits, "
                "positive outcomes, and what the user gains."
            )

        if baseline.brain_scores.memory.overall < 0.4:
            recommendations.append(
                "Use concrete examples, metaphors, and vivid imagery to improve "
                "memory encoding. Avoid abstract language."
            )

        if len(variants) > 1:
            dims = ["attention", "dopamine", "memory"]
            best_variant = max(
                variants[1:],
                key=lambda v: (
                    v.brain_scores.attention.overall * 0.35
                    + v.brain_scores.dopamine.overall * 0.35
                    + v.brain_scores.memory.overall * 0.30
                ) if v.brain_scores else 0,
                default=None,
            )
            if best_variant and best_variant.framing_type:
                recommendations.append(
                    f"The '{best_variant.framing_type}' framing variant "
                    f"({best_variant.name}) showed the strongest neural response. "
                    f"Consider adopting this framing approach for your primary copy."
                )

        scores = comparison.get("scores", {})
        if scores:
            for dim in ["attention", "dopamine", "memory"]:
                dim_scores = {
                    name: s[dim] for name, s in scores.items()
                }
                if dim_scores:
                    best_name = max(dim_scores, key=dim_scores.get)
                    worst_name = min(dim_scores, key=dim_scores.get)
                    if dim_scores[best_name] - dim_scores[worst_name] > 0.1:
                        recommendations.append(
                            f"For {dim}, '{best_name}' outperforms '{worst_name}' by "
                            f"{dim_scores[best_name] - dim_scores[worst_name]:.0%}. "
                            f"Apply '{best_name}' approach to improve {dim}."
                        )

        return recommendations
