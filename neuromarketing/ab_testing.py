import numpy as np
from typing import List, Optional, Dict, Any
import uuid
from scipy import stats
import logging

from .analyzer import NeuromarketingAnalyzer
from .models import ABTestResult, AnalysisResult, MediaType

logger = logging.getLogger(__name__)


class ABTestEngine:
    def __init__(self, analyzer: NeuromarketingAnalyzer):
        self.analyzer = analyzer

    def compare_videos(
        self,
        video_paths: List[str],
        variant_names: Optional[List[str]] = None,
        filenames: Optional[List[str]] = None,
    ) -> ABTestResult:
        results = []
        for i, path in enumerate(video_paths):
            fname = filenames[i] if filenames and i < len(filenames) else path
            logger.info(f"AB test video {i+1}/{len(video_paths)}: {fname}")
            result = self.analyzer.analyze_video(path, fname)
            if variant_names and i < len(variant_names):
                result.filename = variant_names[i]
            results.append(result)
        return self._compute_ab_test(results)

    def compare_texts(
        self,
        texts: List[str],
        variant_names: Optional[List[str]] = None,
    ) -> ABTestResult:
        results = []
        for i, text in enumerate(texts):
            name = variant_names[i] if variant_names and i < len(variant_names) else f"Variant {i+1}"
            logger.info(f"AB test text {i+1}/{len(texts)}: {name}")
            result = self.analyzer.analyze_text(text, name)
            results.append(result)
        return self._compute_ab_test(results)

    def compare_audio(
        self,
        audio_paths: List[str],
        variant_names: Optional[List[str]] = None,
    ) -> ABTestResult:
        results = []
        for i, path in enumerate(audio_paths):
            name = variant_names[i] if variant_names and i < len(variant_names) else f"Variant {i+1}"
            result = self.analyzer.analyze_audio(path, name)
            results.append(result)
        return self._compute_ab_test(results)

    def _compute_ab_test(self, results: List[AnalysisResult]) -> ABTestResult:
        if not results:
            return ABTestResult(id=str(uuid.uuid4())[:8])

        dims = {
            "attention": [r.brain_scores.attention.overall for r in results],
            "dopamine": [r.brain_scores.dopamine.overall for r in results],
            "memory": [r.brain_scores.memory.overall for r in results],
        }

        overall_scores = [
            (
                r.brain_scores.attention.overall * 0.35
                + r.brain_scores.dopamine.overall * 0.35
                + r.brain_scores.memory.overall * 0.30
            )
            for r in results
        ]

        if len(results) >= 2:
            max_idx = int(np.argmax(overall_scores))
            winning_variant = results[max_idx].filename
        else:
            winning_variant = results[0].filename if results else None

        significance_scores = {}
        if len(results) >= 2:
            for dim_name, dim_values in dims.items():
                if len(set(dim_values)) > 1:
                    try:
                        best = max(dim_values)
                        worst = min(dim_values)
                        t_stat, p_val = stats.ttest_ind(
                            [best] * len(dim_values),
                            [worst] * len(dim_values),
                            equal_var=False,
                        )
                        significance_scores[dim_name] = float(1 - p_val)
                    except Exception:
                        significance_scores[dim_name] = 0.5
                else:
                    significance_scores[dim_name] = 0.0

        recommendation = self._generate_ab_recommendation(
            results, dims, winning_variant
        )

        return ABTestResult(
            id=str(uuid.uuid4())[:8],
            variants=results,
            winning_variant=winning_variant,
            dimension_comparison=dims,
            significance_scores=significance_scores,
            recommendation=recommendation,
        )

    def _generate_ab_recommendation(
        self,
        results: List[AnalysisResult],
        dims: Dict[str, List[float]],
        winner: Optional[str],
    ) -> str:
        if not results:
            return "No data available."

        if len(results) < 2:
            return "Add more variants to perform A/B comparison."

        parts = []
        if winner:
            parts.append(f"Winner: '{winner}'")

        for dim_name, dim_values in dims.items():
            if len(dim_values) >= 2 and max(dim_values) - min(dim_values) > 0.05:
                best_idx = int(np.argmax(dim_values))
                parts.append(
                    f"Best {dim_name}: '{results[best_idx].filename}' "
                    f"({dim_values[best_idx]:.0%})"
                )

        best_overall = max(
            range(len(results)),
            key=lambda i: (
                dims["attention"][i] * 0.35
                + dims["dopamine"][i] * 0.35
                + dims["memory"][i] * 0.30
            ),
        )
        worst_overall = min(
            range(len(results)),
            key=lambda i: (
                dims["attention"][i] * 0.35
                + dims["dopamine"][i] * 0.35
                + dims["memory"][i] * 0.30
            ),
        )

        total_best = (
            dims["attention"][best_overall] * 0.35
            + dims["dopamine"][best_overall] * 0.35
            + dims["memory"][best_overall] * 0.30
        )
        total_worst = (
            dims["attention"][worst_overall] * 0.35
            + dims["dopamine"][worst_overall] * 0.35
            + dims["memory"][worst_overall] * 0.30
        )

        improvement = ((total_best - total_worst) / (total_worst + 1e-8)) * 100
        parts.append(
            f"Best variant outperforms worst by {improvement:.1f}% in neural engagement"
        )

        return " | ".join(parts)
