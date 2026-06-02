import os

MODEL_CACHE_DIR = os.getenv("TRIBE_CACHE_DIR", "./cache")
TRIBE_MODEL_NAME = os.getenv("TRIBE_MODEL_NAME", "facebook/tribev2")
USE_REAL_MODEL = os.getenv("USE_REAL_TRIBE", "false").lower() == "true"
DEVICE = os.getenv("DEVICE", "cpu")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

ATTENTION_ROIS = ["V1", "V2", "V3", "MT", "IPS", "FEF"]
DOPAMINE_ROIS = ["VS", "NAcc", "vmPFC", "SN", "VTA"]
MEMORY_ROIS = ["HIP", "PHC", "PRC", "ERC", "ANG", "PCC", "DLPFC", "MPFC"]

ATTENTION_WEIGHTS = {
    "visual_cortex": 0.30,
    "parietal": 0.25,
    "frontal_eye_fields": 0.20,
    "temporal": 0.15,
    "subcortical_attention": 0.10,
}

DOPAMINE_WEIGHTS = {
    "ventral_striatum": 0.30,
    "nucleus_accumbens": 0.25,
    "vmPFC": 0.20,
    "substantia_nigra": 0.15,
    "ventral_tegmental": 0.10,
}

MEMORY_WEIGHTS = {
    "hippocampus": 0.30,
    "parahippocampal": 0.20,
    "perirhinal": 0.15,
    "entorhinal": 0.10,
    "angular_gyrus": 0.10,
    "posterior_cingulate": 0.10,
    "dlPFC": 0.05,
}

ATTENTION_THRESHOLD_LOW = 0.35
ATTENTION_THRESHOLD_MED = 0.60
DOPAMINE_THRESHOLD_LOW = 0.30
DOPAMINE_THRESHOLD_MED = 0.55
MEMORY_THRESHOLD_LOW = 0.30
MEMORY_THRESHOLD_MED = 0.55
