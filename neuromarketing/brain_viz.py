import numpy as np
import os
import logging
from nilearn import datasets, plotting

logger = logging.getLogger(__name__)

# MNI coordinates for each ROI (x, y, z) in MNI152 space
# Bilateral ROIs are defined with Left (negative x) and Right (positive x)
ROI_COORDS = {
    # Visual cortex / Attention ROIs
    "V1":   [(-8, -82, -4),    (8, -82, -4)],
    "V2":   [(-14, -78, 0),    (14, -78, 0)],
    "V3":   [(-20, -74, 4),    (20, -74, 4)],
    "MT":   [(-44, -68, 2),    (44, -68, 2)],
    "IPS":  [(-24, -58, 48),   (24, -58, 48)],
    "FEF":  [(-24, -8, 54),    (24, -8, 54)],
    # Dopamine / Reward ROIs
    "VS":   [(-10, 10, -4),    (10, 10, -4)],
    "NAcc": [(-10, 12, -6),    (10, 12, -6)],
    "vmPFC":[(-4, 44, -8),     (4, 44, -8)],
    "SN":   [(-8, -18, -12),   (8, -18, -12)],
    "VTA":  [(0, -18, -12),    (0, -18, -12)],
    # Memory / Medial Temporal ROIs
    "HIP":  [(-24, -20, -18),  (24, -20, -18)],
    "PHC":  [(-26, -30, -14),  (26, -30, -14)],
    "PRC":  [(-34, -14, -28),  (34, -14, -28)],
    "ERC":  [(-24, -8, -30),   (24, -8, -30)],
    "ANG":  [(-48, -58, 28),   (48, -58, 28)],
    "PCC":  [(-4, -48, 24),    (4, -48, 24)],
    "DLPFC":[(-38, 34, 28),    (38, 34, 28)],
}

# All ROIs by dimension
ATTENTION_ROIS = ["V1", "V2", "V3", "MT", "IPS", "FEF"]
DOPAMINE_ROIS = ["VS", "NAcc", "vmPFC", "SN", "VTA"]
MEMORY_ROIS = ["HIP", "PHC", "PRC", "ERC", "ANG", "PCC", "DLPFC"]

BRAIN_VIZ_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "brain_viz")


def _gaussian_volume(shape, affine, coords, intensities, sigma_mm=6):
    """Create a 3D volume with Gaussian blobs at given coordinates."""
    vol = np.zeros(shape, dtype=np.float64)
    from nilearn.image import get_data
    i_vals = np.arange(shape[0])
    j_vals = np.arange(shape[1])
    k_vals = np.arange(shape[2])
    I, J, K = np.meshgrid(i_vals, j_vals, k_vals, indexing='ij', sparse=True)

    # Convert voxel indices to MNI coordinates
    X = affine[0, 0] * I + affine[0, 1] * J + affine[0, 2] * K + affine[0, 3]
    Y = affine[1, 0] * I + affine[1, 1] * J + affine[1, 2] * K + affine[1, 3]
    Z = affine[2, 0] * I + affine[2, 1] * J + affine[2, 2] * K + affine[2, 3]

    sigma_vox = sigma_mm / abs(affine[0, 0])
    for (cx, cy, cz), intensity in zip(coords, intensities):
        if intensity <= 0:
            continue
        dist2 = (X - cx)**2 + (Y - cy)**2 + (Z - cz)**2
        vol += intensity * np.exp(-dist2 / (2 * sigma_vox**2))

    return vol


async def generate_brain_html(roi_scores, analysis_id, mode="attention"):
    """
    Generate interactive 3D brain visualization using nilearn.

    Parameters
    ----------
    roi_scores : dict
        Dict of ROI name -> score (0-1) for all ROIs.
        E.g. {"V1": 0.6, "NAcc": 0.8, "HIP": 0.4, ...}
    analysis_id : str
        Unique ID to name the output file.
    mode : str
        "attention", "dopamine", or "memory" — determines which ROIs to highlight.

    Returns
    -------
    str or None
        The URL path to the generated HTML file (relative to /app),
        or None on failure.
    """
    try:
        os.makedirs(BRAIN_VIZ_DIR, exist_ok=True)

        # Choose ROIs based on mode
        if mode == "attention":
            primary_rois = ATTENTION_ROIS
        elif mode == "dopamine":
            primary_rois = DOPAMINE_ROIS
        else:
            primary_rois = MEMORY_ROIS

        # Build coordinate + intensity list for all ROIs
        all_coords = []
        all_intensities = []
        for roi_name, coord_pairs in ROI_COORDS.items():
            score = roi_scores.get(roi_name, 0.0)
            if score <= 0:
                score = 0.05

            if roi_name in primary_rois:
                display_score = score
            else:
                display_score = score * 0.3

            for coord in coord_pairs:
                all_coords.append(coord)
                all_intensities.append(display_score)

        if not all_coords:
            logger.warning("No ROIs with scores for brain viz")
            return None

        # Create an MNI-space volume
        shape = (91, 109, 91)
        affine = np.array([
            [-2, 0, 0, 90],
            [0, 2, 0, -126],
            [0, 0, 2, -72],
            [0, 0, 0, 1],
        ], dtype=np.float64)

        vol_data = _gaussian_volume(shape, affine, all_coords, all_intensities, sigma_mm=8)
        vol_data = np.clip(vol_data, 0, None)

        from nibabel import Nifti1Image
        nifti_img = Nifti1Image(vol_data, affine)

        # Generate interactive surface plot
        fsaverage = datasets.fetch_surf_fsaverage(mesh="fsaverage5")
        view = plotting.view_img_on_surf(
            stat_map_img=nifti_img,
            surf_mesh="fsaverage5",
            threshold=0.01,
            cmap="inferno",
            colorbar=True,
            symmetric_cmap=False,
            title="",
        )

        # Save HTML
        mode_label = mode.capitalize()
        view._title = f"Brain Activity — {mode_label}"
        html_path = os.path.join(BRAIN_VIZ_DIR, f"{analysis_id}_{mode}.html")
        view.save_as_html(html_path)
        logger.info(f"Brain viz saved to {html_path}")

        return f"/brain_viz/{analysis_id}_{mode}.html"

    except Exception as e:
        logger.exception(f"Failed to generate brain viz: {e}")
        return None


async def get_brain_viz_urls(roi_scores, analysis_id):
    """Generate brain viz HTML for all three modes, returning URLs."""
    urls = {}
    for mode in ["attention", "dopamine", "memory"]:
        url = await generate_brain_html(roi_scores, analysis_id, mode)
        if url:
            urls[mode] = url
    return urls
