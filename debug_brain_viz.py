import json
from neuromarketing import TribeAdapter, NeuromarketingAnalyzer
from neuromarketing.brain_viz import get_brain_viz_urls

tribe = TribeAdapter()
tribe.initialize()
analyzer = NeuromarketingAnalyzer(tribe)
result = analyzer.analyze_text("Test text for brain viz generation", "test.txt")
data = result.model_dump()
bs = data.get("brain_scores", {})
print("Brain scores keys:", list(bs.keys()))
for dim in ["attention", "dopamine", "memory"]:
    dim_data = bs.get(dim, {})
    print(f"{dim} roi_breakdown: {dim_data.get('roi_breakdown', {})}")

# Test ROI extraction
roi_scores = {}
for dim in ["attention", "dopamine", "memory"]:
    dim_data = bs.get(dim, {})
    roi_bd = dim_data.get("roi_breakdown", {})
    for roi, score in roi_bd.items():
        roi_scores[roi] = max(roi_scores.get(roi, 0), score)

print("\nCollected ROI scores:", json.dumps(roi_scores, indent=2))
print("\nTrying get_brain_viz_urls...")
urls = get_brain_viz_urls(roi_scores, "debug123")
print("URLs:", urls)
