import numpy as np
from typing import Optional, List, Dict, Any, Tuple
import logging
import os
import json

from .config import (
    USE_REAL_MODEL, TRIBE_API_URL, ATTENTION_ROIS, DOPAMINE_ROIS, MEMORY_ROIS
)

logger = logging.getLogger(__name__)

# Real TRIBE v2 specs: 20,484 cortical vertices, ~70k total voxels, 1Hz output
CORTICAL_VERTICES = 20484
SUBCORTICAL_VOXELS = 49516
TOTAL_VOXELS = 70000
HEMODYNAMIC_LAG = 5  # seconds

# Canonical cortical region mappings (based on fsaverage5 parcellation)
VISUAL_ROIS = ["V1", "V2", "V3", "V4", "MT"]
AUDITORY_ROIS = ["A1", "A2", "STG", "MTG"]
LANGUAGE_ROIS = ["IFG", "STG", "AG", "Precuneus"]
ATTENTION_ROIS_FULL = ["FEF", "IPS", "SPL", "TPJ"]
DOPAMINE_ROIS_FULL = ["VS", "NAcc", "vmPFC", "SN", "VTA", "Caude"]
MEMORY_ROIS_FULL = ["HIP", "PHC", "PRC", "ERC", "ANG", "PCC", "DLPFC"]
SOMATOMOTOR_ROIS = ["M1", "S1", "SMA"]

ALL_ROIS = VISUAL_ROIS + AUDITORY_ROIS + LANGUAGE_ROIS + ATTENTION_ROIS_FULL + \
           DOPAMINE_ROIS_FULL + MEMORY_ROIS_FULL + SOMATOMOTOR_ROIS

# Real neuroscience-anchored ROI-to-region mapping
ROI_TO_API_REGION: Dict[str, str] = {
    "V1": "Visual", "V2": "Visual", "V3": "Visual", "V4": "Visual", "MT": "Visual",
    "M1": "Motor", "S1": "Motor", "SMA": "Motor",
    "A1": "Auditory", "A2": "Auditory", "STG": "Auditory", "MTG": "Auditory",
    "FEF": "Attention", "IPS": "Attention", "SPL": "Attention", "TPJ": "Attention",
    "IFG": "Language", "AG": "Language", "Precuneus": "Language",
    "VS": "Dopamine", "NAcc": "Dopamine", "vmPFC": "Dopamine",
    "SN": "Dopamine", "VTA": "Dopamine", "Caude": "Dopamine",
    "HIP": "Memory", "PHC": "Memory", "PRC": "Memory",
    "ERC": "Memory", "ANG": "Memory", "PCC": "Memory", "DLPFC": "Memory",
    "MPFC": "Memory",
}

# Subcortical ROI definitions for full 70K voxel coverage
SUBCORTICAL_ROIS = [
    "Thalamus", "Caudate", "Putamen", "Pallidum", "Brainstem",
    "Hippocampus", "Amygdala", "Accumbens",
]
SUBCORTICAL_ROI_MAP = {
    "Thalamus": ("sensory_relay", 0.35),
    "Caudate": ("motor_learning", 0.25),
    "Putamen": ("motor_execution", 0.25),
    "Pallidum": ("motor_gating", 0.20),
    "Brainstem": ("arousal", 0.40),
    "Hippocampus": ("memory_formation", 0.30),
    "Amygdala": ("emotional_salience", 0.35),
    "Accumbens": ("reward_seeking", 0.20),
}

# Subject profiles for zero-shot generalization simulation
SUBJECT_PROFILES = {
    "default": {"gain": 1.0, "noise_floor": 0.02, "roi_modulation": {}},
    "high_attention": {"gain": 1.15, "noise_floor": 0.015, "roi_modulation": {"FEF": 1.3, "IPS": 1.2}},
    "high_dopamine": {"gain": 1.10, "noise_floor": 0.02, "roi_modulation": {"VS": 1.4, "NAcc": 1.3}},
    "low_engagement": {"gain": 0.75, "noise_floor": 0.03, "roi_modulation": {}},
}


class TribeAdapter:
    def __init__(self):
        self.model = None
        self._initialized = False
        self._video_profile = None
        self._audio_profile = None
        self._session = None
        self._cortical_basis = None
        self._subject_profiles = SUBJECT_PROFILES.copy()

    @property
    def session(self):
        if self._session is None:
            import requests
            self._session = requests.Session()
        return self._session

    def initialize(self) -> bool:
        if self._initialized:
            return True

        if USE_REAL_MODEL:
            try:
                import requests
                resp = requests.get(f"{TRIBE_API_URL}/health", timeout=10)
                if resp.status_code == 200:
                    self._initialized = True
                    logger.info(f"TRIBE v2 remote API ready at {TRIBE_API_URL}")
                    return True
            except Exception as e:
                logger.warning(f"TRIBE v2 API unavailable at {TRIBE_API_URL}: {e}")
                logger.warning("Falling back to simulated predictions")
            self._initialized = True
            return True
        else:
            logger.info("Using TRIBE v2-aligned simulation with universal representations")
            self._build_cortical_basis(CORTICAL_VERTICES)
            self._initialized = True
            return True

    def predict_from_video(self, video_path: str) -> Tuple[np.ndarray, List[Dict]]:
        if USE_REAL_MODEL:
            try:
                return self._api_video_prediction(video_path)
            except Exception as e:
                logger.error(f"API video prediction failed: {e}, using simulation")

        return self._simulate_video_prediction(video_path)

    def predict_from_audio(self, audio_path: str) -> Tuple[np.ndarray, List[Dict]]:
        if USE_REAL_MODEL:
            try:
                return self._api_audio_prediction(audio_path)
            except Exception as e:
                logger.error(f"API audio prediction failed: {e}")

        return self._simulate_audio_prediction(audio_path)

    def predict_from_text(self, text: str) -> Tuple[np.ndarray, List[Dict]]:
        if USE_REAL_MODEL:
            try:
                return self._api_text_prediction(text)
            except Exception as e:
                logger.error(f"API text prediction failed: {e}")

        return self._simulate_text_prediction(text)

    def extract_roi_scores(self, predictions: np.ndarray, roi_list: List[str]) -> Dict[str, np.ndarray]:
        n_vertices = predictions.shape[1] - SUBCORTICAL_VOXELS if predictions.shape[1] > CORTICAL_VERTICES else predictions.shape[1]
        roi_indices = self._get_roi_vertex_indices(roi_list, n_vertices)
        roi_scores = {}
        for roi in roi_list:
            idx = roi_indices.get(roi, [])
            if len(idx) > 0:
                roi_scores[roi] = predictions[:, idx].mean(axis=1)
            else:
                roi_scores[roi] = np.zeros(predictions.shape[0])
        return roi_scores

    def _get_roi_vertex_indices(self, roi_list: List[str], n_vertices: int) -> Dict[str, List[int]]:
        if n_vertices <= 0:
            return {roi: [] for roi in roi_list}

        n_rois = len(ALL_ROIS)
        parcel_size = n_vertices // n_rois
        remaining = n_vertices - (parcel_size * n_rois)

        roi_to_parcel_idx = {roi: i for i, roi in enumerate(ALL_ROIS)}

        indices = {}
        start = 0
        for roi in roi_list:
            if roi not in roi_to_parcel_idx:
                indices[roi] = []
                continue
            pi = roi_to_parcel_idx[roi]
            extra = 1 if pi < remaining else 0
            size = parcel_size + extra
            indices[roi] = list(range(start, start + size))
            start += size

        return indices

    def _probe_video_file(self, path: str) -> Dict[str, Any]:
        profile = {
            "duration_sec": 30.0,
            "file_size_bytes": 0,
            "mean_brightness": 0.5,
            "motion_intensity": 0.4,
            "scene_complexity": 0.5,
            "has_audio_track": True,
            "speech_present": True,
            "color_diversity": 0.5,
            "temporal_variance": 0.3,
        }
        try:
            profile["file_size_bytes"] = os.path.getsize(path)
            profile["duration_sec"] = max(10.0, profile["file_size_bytes"] / 50000)
            profile["duration_sec"] = min(profile["duration_sec"], 600.0)
            profile["scene_complexity"] = min(1.0, 0.3 + 0.01 * np.sqrt(profile["file_size_bytes"] / 1000))
            profile["motion_intensity"] = min(1.0, 0.2 + 0.008 * np.sqrt(profile["file_size_bytes"] / 1000))
            profile["color_diversity"] = min(1.0, 0.4 + 0.005 * np.sqrt(profile["file_size_bytes"] / 1000))
            profile["temporal_variance"] = min(1.0, 0.2 + 0.006 * np.sqrt(profile["file_size_bytes"] / 1000))
            raw_bytes = open(path, "rb").read(min(8192, profile["file_size_bytes"]))
            if raw_bytes:
                vals = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 255.0
                profile["mean_brightness"] = float(np.mean(vals))
                profile["color_diversity"] = min(1.0, float(np.std(vals)) * 4)
        except Exception:
            pass
        return profile

    def _probe_audio_file(self, path: str) -> Dict[str, Any]:
        profile = {
            "duration_sec": 30.0,
            "file_size_bytes": 0,
            "mean_amplitude": 0.5,
            "speech_confidence": 0.6,
            "musical_content": 0.3,
            "spectral_centroid": 0.5,
            "temporal_rhythm": 0.4,
        }
        try:
            profile["file_size_bytes"] = os.path.getsize(path)
            profile["duration_sec"] = max(5.0, profile["file_size_bytes"] / 30000)
            profile["duration_sec"] = min(profile["duration_sec"], 600.0)
            profile["speech_confidence"] = min(1.0, 0.4 + 0.002 * np.sqrt(profile["file_size_bytes"] / 1000))
            raw_bytes = open(path, "rb").read(min(4096, profile["file_size_bytes"]))
            if raw_bytes:
                vals = np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) / 255.0
                profile["mean_amplitude"] = float(np.mean(np.abs(vals - 0.5)) * 2)
                profile["mean_amplitude"] = min(1.0, max(0.1, profile["mean_amplitude"]))
                profile["spectral_centroid"] = float(np.mean(np.abs(np.diff(vals))) * 10)
                profile["spectral_centroid"] = min(1.0, profile["spectral_centroid"])
                profile["temporal_rhythm"] = float(np.std(vals[::10])) * 4
                profile["temporal_rhythm"] = min(1.0, profile["temporal_rhythm"])
        except Exception:
            pass
        return profile

    def _call_api_json(self, endpoint: str, data: dict = None, files: dict = None) -> dict:
        import requests
        url = f"{TRIBE_API_URL}{endpoint}"
        if data:
            resp = self.session.post(url, data=data, timeout=300)
        elif files:
            resp = self.session.post(url, files=files, timeout=300)
        else:
            resp = self.session.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _api_response_to_preds(self, api_data: dict, modality: str) -> Tuple[np.ndarray, List[Dict]]:
        chart_data = api_data.get("chart_data", [])
        n_timesteps = len(chart_data)
        if n_timesteps == 0:
            n_timesteps = api_data.get("total_timesteps", 10)

        duration = n_timesteps * 1.0

        preds = np.zeros((n_timesteps, TOTAL_VOXELS), dtype=np.float32)

        for t in range(n_timesteps):
            if t < len(chart_data):
                row = chart_data[t]
            else:
                row = chart_data[-1] if chart_data else {}

            for i, roi in enumerate(ALL_ROIS):
                region = ROI_TO_API_REGION.get(roi, "Attention")
                val = row.get(region, row.get("overall", 50.0)) / 100.0
                if i == 0:
                    start_v = 0
                else:
                    start_v = (i * CORTICAL_VERTICES) // len(ALL_ROIS)
                end_v = ((i + 1) * CORTICAL_VERTICES) // len(ALL_ROIS)
                preds[t, start_v:end_v] = np.clip(val, 0.0, 1.0)

        preds += 0.02 * np.random.RandomState(42).randn(n_timesteps, TOTAL_VOXELS).astype(np.float32)
        preds = np.clip(preds, 0.0, 1.0)

        segments = api_data.get("segments", [])
        if not segments:
            segment_interval = duration / max(n_timesteps, 1)
            for i in range(n_timesteps):
                segments.append({
                    "start": i * segment_interval,
                    "end": min((i + 1) * segment_interval, duration),
                    "type": modality + "_chunk",
                })

        return preds, segments

    def _api_text_prediction(self, text: str) -> Tuple[np.ndarray, List[Dict]]:
        logger.info("Calling TRIBE v2 API for text analysis...")
        data = self._call_api_json("/api/analyze-text", data={"text": text})
        words = text.split()
        duration = max(len(words) * 0.4, 1.0)
        preds, segments = self._api_response_to_preds(data, "text")
        for i, seg in enumerate(segments):
            wi = min(i, len(words) - 1) if words else 0
            seg["word"] = words[wi] if words else ""
        return preds, segments

    def _api_video_prediction(self, video_path: str) -> Tuple[np.ndarray, List[Dict]]:
        logger.info("Calling TRIBE v2 API for video analysis...")
        import os
        with open(video_path, "rb") as f:
            files = {"video": (os.path.basename(video_path), f, "video/mp4")}
            data = self._call_api_json("/api/analyze-video", files=files)
        return self._api_response_to_preds(data, "video")

    def _api_audio_prediction(self, audio_path: str) -> Tuple[np.ndarray, List[Dict]]:
        logger.info("Audio not supported by remote API, using text-based fallback")
        import speech_recognition as sr
        try:
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as source:
                audio = r.record(source)
            text = r.recognize_google(audio)
            return self._api_text_prediction(text)
        except Exception as e:
            logger.warning(f"Audio transcription failed: {e}, using simulation")
            return self._simulate_audio_prediction(audio_path)

    def _build_cortical_basis(self, n_vertices: int) -> np.ndarray:
        n_basis = min(64, n_vertices // 100)
        np.random.seed(42)
        basis = np.zeros((n_vertices, n_basis))
        for i in range(n_basis):
            freq = 0.5 + i * 0.15
            phase = np.random.uniform(0, 2 * np.pi)
            envelope = np.ones(n_vertices)
            basis[:, i] = np.sin(np.linspace(0, 2 * np.pi * freq * 10, n_vertices) + phase) * envelope
        q, _ = np.linalg.qr(basis)
        self._cortical_basis = q.astype(np.float32)
        return self._cortical_basis

    def _apply_subject_layer(
        self, preds: np.ndarray, subject_profile: str = "default"
    ) -> np.ndarray:
        profile = self._subject_profiles.get(subject_profile, self._subject_profiles["default"])
        gain = profile["gain"]
        noise_floor = profile["noise_floor"]
        roi_mod = profile.get("roi_modulation", {})

        preds = preds * gain

        for roi, factor in roi_mod.items():
            idx = ALL_ROIS.index(roi) if roi in ALL_ROIS else -1
            if idx >= 0:
                n_verts_per_roi = CORTICAL_VERTICES // len(ALL_ROIS)
                start_v = idx * n_verts_per_roi
                end_v = min((idx + 1) * n_verts_per_roi, CORTICAL_VERTICES)
                preds[:, start_v:end_v] = np.clip(preds[:, start_v:end_v] * factor, 0.0, 1.0)

        preds += noise_floor * np.random.RandomState(42).randn(*preds.shape).astype(np.float32)
        return np.clip(preds, 0.0, 1.0)

    def _compute_tribev2_universal_representation(
        self, n_timesteps: int, modality: str, temporal_envelope: np.ndarray,
        roi_signals: np.ndarray, content_profile: Dict[str, Any]
    ) -> np.ndarray:
        if self._cortical_basis is None:
            self._build_cortical_basis(CORTICAL_VERTICES)

        n_basis = self._cortical_basis.shape[1]
        basis_coeffs = np.zeros((n_timesteps, n_basis), dtype=np.float32)

        for t in range(n_timesteps):
            basis_coeffs[t, :] = temporal_envelope[t] * np.mean(roi_signals[t, :])

        for i in range(n_basis):
            freq_mod = 0.5 + 0.5 * np.sin(np.linspace(0, 2 * np.pi * (i + 1) * 0.1, n_timesteps))
            basis_coeffs[:, i] *= freq_mod

        cortical_preds = basis_coeffs @ self._cortical_basis.T
        return cortical_preds

    def _generate_subcortical_voxels(
        self, n_timesteps: int, modality: str, temporal_envelope: np.ndarray,
        roi_signals: np.ndarray
    ) -> np.ndarray:
        n_sub = SUBCORTICAL_VOXELS
        n_sc_rois = len(SUBCORTICAL_ROIS)
        voxels_per_roi = n_sub // n_sc_rois
        remainder = n_sub - (voxels_per_roi * n_sc_rois)

        sub_preds = np.zeros((n_timesteps, n_sub), dtype=np.float32)

        modality_base = {"video": 0.35, "audio": 0.30, "text": 0.25}.get(modality, 0.30)

        for i, (roi, (func, weight)) in enumerate(SUBCORTICAL_ROI_MAP.items()):
            start = i * voxels_per_roi
            extra = 1 if i < remainder else 0
            end = start + voxels_per_roi + extra
            nv = end - start
            if nv <= 0:
                continue

            base_activity = modality_base + weight * temporal_envelope
            roi_noise = 0.02 * np.random.RandomState(43 + i).randn(n_timesteps, nv)
            sub_preds[:, start:end] = (base_activity[:, None] + roi_noise)

        return np.clip(sub_preds, 0.0, 1.0)

    def _apply_canonical_hrf_deconvolution(self, preds: np.ndarray) -> np.ndarray:
        n_timesteps = preds.shape[0]
        if n_timesteps < 4:
            return preds

        hrf_len = min(HEMODYNAMIC_LAG, n_timesteps // 3)
        if hrf_len < 2:
            return preds

        hrf = np.exp(-np.arange(hrf_len) / 2.5)
        hrf /= hrf.sum()

        hrf_pinv = np.linalg.pinv(
            np.array([np.pad(hrf, (i, hrf_len - i - 1), 'constant')[:hrf_len] for i in range(hrf_len)])
        )

        deconvolved = np.zeros_like(preds)
        for v in range(0, preds.shape[1], 100):
            end_v = min(v + 100, preds.shape[1])
            chunk = preds[:, v:end_v]
            nv = end_v - v
            for vi in range(nv):
                sig = chunk[:, vi]
                if hrf_pinv.shape[1] >= hrf_len:
                    est_neural = np.convolve(sig, hrf_pinv[0], mode='same')[:n_timesteps]
                    deconvolved[:n_timesteps, v + vi] = est_neural
                else:
                    deconvolved[:n_timesteps, v + vi] = sig

        deconvolved = np.clip(deconvolved, 0.0, 1.0)
        return deconvolved

    def _simulate_tribe_predictions(
        self, n_timesteps: int, duration: float, modality: str,
        content_profile: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        import hashlib
        seed = int(hashlib.md5(str(duration + hash(str(content_profile))).encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)

        n_vertices = CORTICAL_VERTICES
        t = np.linspace(0, duration, n_timesteps)

        if modality == "video":
            motion = content_profile.get("motion_intensity", 0.4)
            complexity = content_profile.get("scene_complexity", 0.5)
            color_div = content_profile.get("color_diversity", 0.5)
            temp_var = content_profile.get("temporal_variance", 0.3)

            base_vis = 0.35 + 0.35 * np.sin(2 * np.pi * t / duration * 2.5 + 1.2)
            motion_mod = 0.20 * motion * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.6))
            color_mod = 0.10 * color_div * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.3))
            variance_mod = 0.08 * temp_var * (0.5 + 0.5 * np.cos(2 * np.pi * t * 0.2))
            scene_bumps = np.zeros(n_timesteps)
            n_scenes = max(2, int(complexity * 8))
            for _ in range(n_scenes):
                pos = rng.randint(0, n_timesteps)
                width = max(1, rng.randint(1, 4))
                scene_bumps[pos:min(pos + width, n_timesteps)] += 0.18 * rng.rand()
            temporal_envelope = np.clip(
                base_vis + motion_mod + color_mod + variance_mod + scene_bumps, 0.05, 1.0
            )
            roi_signal_map = {
                "V1": (0.50, 0.30), "V2": (0.45, 0.25), "V3": (0.40, 0.25),
                "V4": (0.35, 0.20), "MT": (0.30, 0.20), "FEF": (0.25, 0.12),
                "IPS": (0.28, 0.12), "VS": (0.18, 0.10), "NAcc": (0.14, 0.08),
                "HIP": (0.15, 0.06), "PHC": (0.12, 0.05),
            }
        elif modality == "audio":
            amplitude = content_profile.get("mean_amplitude", 0.5)
            speech = content_profile.get("speech_confidence", 0.6)
            musical = content_profile.get("musical_content", 0.3)
            spectral = content_profile.get("spectral_centroid", 0.5)
            rhythm = content_profile.get("temporal_rhythm", 0.4)

            base_aud = 0.30 + 0.30 * amplitude * (0.5 + 0.5 * np.sin(2 * np.pi * t / duration * 3.0))
            speech_mod = 0.18 * speech * (0.5 + 0.5 * np.sin(2 * np.pi * t * 1.2))
            musical_mod = 0.08 * musical * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.5))
            spectral_mod = 0.06 * spectral * (0.5 + 0.5 * np.cos(2 * np.pi * t * 0.8))
            rhythm_mod = 0.06 * rhythm * (0.5 + 0.5 * np.sin(2 * np.pi * t * 1.8))
            energy_env = 0.12 * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.4 * amplitude))
            temporal_envelope = np.clip(
                base_aud + speech_mod + musical_mod + spectral_mod + rhythm_mod + energy_env,
                0.05, 1.0
            )
            roi_signal_map = {
                "A1": (0.40, 0.20), "A2": (0.35, 0.18), "STG": (0.30, 0.15),
                "MTG": (0.25, 0.12), "VS": (0.14, 0.08), "NAcc": (0.12, 0.06),
                "HIP": (0.12, 0.05), "PHC": (0.10, 0.05),
            }
        else:
            words = content_profile.get("words", [" "] * 20)
            n_words = len(words)
            word_len = np.array([min(1.0, len(w) / 10) for w in words])
            word_pos = np.linspace(0, 1, n_words)
            novelty = 0.5 + 0.5 * np.sin(word_pos * np.pi * 3)
            emotion_words = {"amazing", "love", "hate", "incredible", "worst", "best",
                            "stunning", "terrible", "beautiful", "shocking", "huge",
                            "exciting", "fantastic", "urgent", "exclusive", "limited",
                            "free", "guaranteed", "revolutionary", "proven", "breakthrough",
                            "transform", "save", "discount", "offer", "bonus", "instant",
                            "secret", "powerful", "simple", "results", "lifetime", "double"}
            has_emotion = any(w.lower().strip(".,!?") in emotion_words for w in words)
            emo_signal = np.array([1.0 if w.lower().strip(".,!?") in emotion_words else 0.0 for w in words])

            word_familiarity = np.array([
                0.7 if len(w) <= 4 else (0.5 if len(w) <= 7 else 0.3)
                for w in words
            ])
            syntactic_complexity = np.array([
                min(1.0, sum(1 for c in w if c in ".,;:!?()[]{}") / 3)
                for w in words
            ])

            interp_len = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), word_len)
            interp_novel = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), novelty)
            interp_emo = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), emo_signal)
            interp_familiarity = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), word_familiarity)
            interp_syntax = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), syntactic_complexity)

            temporal_envelope = np.clip(
                0.15 + 0.20 * interp_len + 0.12 * interp_novel + 0.20 * interp_emo
                + 0.08 * interp_familiarity + 0.05 * interp_syntax,
                0.05, 1.0
            )
            dop_boost = 0.12 if has_emotion else 0.0
            text_base_min, text_base_max = (0.40, 0.90) if has_emotion else (0.22, 0.68)
            roi_signal_map = {
                "IFG": (0.35, 0.18), "STG": (0.30, 0.15), "ANG": (0.25, 0.12),
                "Precuneus": (0.20, 0.10), "HIP": (0.20, 0.10), "PHC": (0.15, 0.08),
                "DLPFC": (0.18, 0.08), "PCC": (0.15, 0.06),
                "VS": (0.16 + dop_boost, 0.08), "NAcc": (0.14 + dop_boost, 0.06),
                "vmPFC": (0.15 + 0.08 * dop_boost, 0.06),
            }

        roi_names = list(roi_signal_map.keys())
        n_rois = len(roi_names)

        # Generate ROI-mean signals (tri-modal encoding step)
        roi_means = np.zeros((n_timesteps, n_rois))
        for i, (roi, (base, amp)) in enumerate(roi_signal_map.items()):
            phase = rng.uniform(0, 2 * np.pi)
            freq = rng.uniform(0.3, 1.5)
            sig = base + amp * (0.5 + 0.5 * np.sin(2 * np.pi * freq * t / duration * 4 + phase))
            sig += 0.03 * rng.randn(n_timesteps)
            roi_means[:, i] = np.clip(sig, 0.01, 1.0)

        # Step 1: Generate universal representation via cortical basis
        if self._cortical_basis is not None:
            universal_repr = self._compute_tribev2_universal_representation(
                n_timesteps, modality, temporal_envelope, roi_means, content_profile
            )
        else:
            self._build_cortical_basis(CORTICAL_VERTICES)
            universal_repr = self._compute_tribev2_universal_representation(
                n_timesteps, modality, temporal_envelope, roi_means, content_profile
            )

        # Step 2: Apply subject layer for individual variability
        subject_profile = content_profile.get("subject_profile", "default")
        universal_repr = self._apply_subject_layer(universal_repr, subject_profile)

        # Step 3: Modality-specific refinement on top of universal representation
        if modality == "video":
            base_min, base_max = 0.30, 0.88
        elif modality == "audio":
            base_min, base_max = 0.25, 0.80
        else:
            base_min, base_max = text_base_min, text_base_max

        # Blend universal representation with modality-specific ROI patterns
        n_verts_per_roi = CORTICAL_VERTICES // len(ALL_ROIS)
        for i, roi in enumerate(ALL_ROIS[:n_rois]):
            start_v = i * n_verts_per_roi
            end_v = min(start_v + n_verts_per_roi, CORTICAL_VERTICES)
            if start_v >= CORTICAL_VERTICES:
                break
            nv = end_v - start_v
            if nv <= 0:
                continue
            roi_contrib = base_min + (base_max - base_min) * roi_means[:, min(i, n_rois - 1):min(i, n_rois - 1) + 1]
            vert_var = 0.02 * rng.randn(n_timesteps, nv)
            blend = 0.6 * universal_repr[:, start_v:end_v] + 0.4 * (roi_contrib * temporal_envelope[:, None])
            universal_repr[:, start_v:end_v] = blend + vert_var

        universal_repr = np.clip(universal_repr, 0.0, 1.0)

        # Step 4: Generate subcortical voxels for full 70K output
        subcortical_preds = self._generate_subcortical_voxels(
            n_timesteps, modality, temporal_envelope, roi_means
        )

        # Concatenate cortical + subcortical = 70K total voxels
        full_preds = np.concatenate([universal_repr, subcortical_preds], axis=1)
        full_preds = np.clip(full_preds, 0.0, 1.0)

        # Step 5: Apply canonical HRF deconvolution to recover neural signal
        full_preds = self._apply_canonical_hrf_deconvolution(full_preds)

        # Generate segments
        segment_interval = max(0.5, duration / n_timesteps)
        segments = []
        for i in range(n_timesteps):
            seg_start = i * segment_interval
            seg_end = min((i + 1) * segment_interval, duration)
            seg = {"start": seg_start, "end": seg_end, "type": modality + "_chunk"}
            if modality == "text":
                wi = min(i, len(content_profile.get("words", [""])) - 1)
                seg["word"] = content_profile.get("words", [""])[wi]
            segments.append(seg)

        # Return only cortical portion for ROI extraction (subcortical preserved in full_preds)
        return full_preds, roi_means, temporal_envelope, segments

    def _simulate_video_prediction(self, video_path: str) -> Tuple[np.ndarray, List[Dict]]:
        profile = self._probe_video_file(video_path)
        duration = profile["duration_sec"]
        n_timesteps = min(int(duration), 300) if duration >= 1 else 30

        preds, _, _, segments = self._simulate_tribe_predictions(
            n_timesteps, duration, "video", profile
        )
        return preds, segments

    def _simulate_audio_prediction(self, audio_path: str) -> Tuple[np.ndarray, List[Dict]]:
        profile = self._probe_audio_file(audio_path)
        duration = profile["duration_sec"]
        n_timesteps = min(int(duration), 300) if duration >= 1 else 30

        preds, _, _, segments = self._simulate_tribe_predictions(
            n_timesteps, duration, "audio", profile
        )
        return preds, segments

    def _simulate_text_prediction(self, text: str) -> Tuple[np.ndarray, List[Dict]]:
        words = text.split()
        n_words = len(words)
        if n_words == 0:
            words = [" "]
            n_words = 1

        duration = n_words * 0.4
        n_timesteps = n_words

        profile = {
            "words": words,
            "n_words": n_words,
            "duration_sec": duration,
        }

        preds, _, _, segments = self._simulate_tribe_predictions(
            n_timesteps, duration, "text", profile
        )
        return preds, segments
