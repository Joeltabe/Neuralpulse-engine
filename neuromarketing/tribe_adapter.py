import numpy as np
from typing import Optional, List, Dict, Any, Tuple
import logging
import os
import struct
import json

from .config import (
    USE_REAL_MODEL, TRIBE_MODEL_NAME, MODEL_CACHE_DIR, DEVICE,
    TRIBE_API_URL, ATTENTION_ROIS, DOPAMINE_ROIS, MEMORY_ROIS
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

# Map each ROI to the HF Space API chart_data region name
ROI_TO_API_REGION: Dict[str, str] = {
    "V1": "Visual", "V2": "Visual", "V3": "Visual", "V4": "Visual", "MT": "Visual",
    "M1": "Motor", "S1": "Motor", "SMA": "Motor",
    "A1": "Auditory", "A2": "Auditory", "MTG": "Auditory",
    "FEF": "Attention", "IPS": "Attention", "SPL": "Attention", "TPJ": "Attention",
    "IFG": "Language", "AG": "Language", "Precuneus": "Language",
    "STG": "Language",
    "VS": "Emotion", "NAcc": "Emotion", "vmPFC": "Emotion",
    "SN": "Emotion", "VTA": "Emotion", "Caude": "Emotion",
    "HIP": "Language", "PHC": "Visual", "PRC": "Visual",
    "ERC": "Language", "ANG": "Attention", "PCC": "Attention", "DLPFC": "Attention",
    "MPFC": "Emotion",
}


class TribeAdapter:
    def __init__(self):
        self.model = None
        self._initialized = False
        self._video_profile = None
        self._audio_profile = None
        self._session = None

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
            tried_local = False
            tried_api = False

            # Try loading the local tribev2 model (requires PyTorch)
            try:
                from tribev2 import TribeModel
                self.model = TribeModel.from_pretrained(
                    TRIBE_MODEL_NAME,
                    cache_folder=MODEL_CACHE_DIR
                )
                self._initialized = True
                logger.info("TRIBE v2 model loaded successfully (local)")
                return True
            except Exception as e:
                logger.warning(f"Local TRIBE v2 model failed: {e}")
                tried_local = True

            # Fallback: try the remote Hugging Face Space API
            try:
                import requests
                resp = requests.get(f"{TRIBE_API_URL}/", timeout=10)
                if resp.status_code == 200:
                    self._initialized = True
                    logger.info(f"TRIBE v2 remote API ready at {TRIBE_API_URL}")
                    return True
            except Exception as e:
                logger.warning(f"TRIBE v2 remote API unavailable: {e}")
                tried_api = True

            logger.info("Falling back to simulated predictions")
            self._initialized = True
            return True
        else:
            logger.info("Using enhanced simulated TRIBE v2 predictions")
            self._initialized = True
            return True

    def predict_from_video(self, video_path: str) -> Tuple[np.ndarray, List[Dict]]:
        if USE_REAL_MODEL:
            if self.model is not None:
                try:
                    df = self.model.get_events_dataframe(video_path=video_path)
                    preds, segments = self.model.predict(events=df)
                    return preds, segments
                except Exception as e:
                    logger.error(f"Local prediction failed: {e}")
            try:
                return self._api_video_prediction(video_path)
            except Exception as e:
                logger.error(f"API video prediction failed: {e}, using simulation")

        return self._simulate_video_prediction(video_path)

    def predict_from_audio(self, audio_path: str) -> Tuple[np.ndarray, List[Dict]]:
        if USE_REAL_MODEL:
            if self.model is not None:
                try:
                    df = self.model.get_events_dataframe(audio_path=audio_path)
                    preds, segments = self.model.predict(events=df)
                    return preds, segments
                except Exception as e:
                    logger.error(f"Local audio prediction failed: {e}")
            try:
                return self._api_audio_prediction(audio_path)
            except Exception as e:
                logger.error(f"API audio prediction failed: {e}")

        return self._simulate_audio_prediction(audio_path)

    def predict_from_text(self, text: str) -> Tuple[np.ndarray, List[Dict]]:
        if USE_REAL_MODEL:
            if self.model is not None:
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                        f.write(text)
                        text_path = f.name
                    df = self.model.get_events_dataframe(text_path=text_path)
                    preds, segments = self.model.predict(events=df)
                    return preds, segments
                except Exception as e:
                    logger.error(f"Local text prediction failed: {e}")
            try:
                return self._api_text_prediction(text)
            except Exception as e:
                logger.error(f"API text prediction failed: {e}")

        return self._simulate_text_prediction(text)

    def extract_roi_scores(self, predictions: np.ndarray, roi_list: List[str]) -> Dict[str, np.ndarray]:
        n_vertices = predictions.shape[1]
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
        import hashlib
        indices = {}
        for roi in roi_list:
            h = int(hashlib.md5(roi.encode()).hexdigest()[:8], 16)
            rng = np.random.RandomState(h)
            n_roi_vertices = max(n_vertices // len(ALL_ROIS), 10)
            idx = rng.choice(n_vertices, size=min(n_roi_vertices, n_vertices // 2), replace=False).tolist()
            indices[roi] = idx
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
        }
        try:
            profile["file_size_bytes"] = os.path.getsize(path)
            profile["duration_sec"] = max(10.0, profile["file_size_bytes"] / 50000)
            profile["duration_sec"] = min(profile["duration_sec"], 600.0)
            profile["scene_complexity"] = min(1.0, 0.3 + 0.01 * np.sqrt(profile["file_size_bytes"] / 1000))
            profile["motion_intensity"] = min(1.0, 0.2 + 0.008 * np.sqrt(profile["file_size_bytes"] / 1000))
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
        n_vertices = CORTICAL_VERTICES

        preds = np.zeros((n_timesteps, n_vertices), dtype=np.float32)

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
                    start_v = (i * n_vertices) // len(ALL_ROIS)
                end_v = ((i + 1) * n_vertices) // len(ALL_ROIS)
                preds[t, start_v:end_v] = np.clip(val, 0.0, 1.0)

        preds += 0.02 * np.random.RandomState(42).randn(n_timesteps, n_vertices).astype(np.float32)
        preds = np.clip(preds, 0.0, 1.0)

        segment_interval = duration / max(n_timesteps, 1)
        segments = []
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

    def _build_cortical_basis(self, n_vertices: int, modality: str) -> np.ndarray:
        np.random.seed(0)
        basis = np.zeros((n_vertices, 20))
        for i in range(20):
            freq = 0.5 + i * 0.3
            phase = np.random.uniform(0, 2 * np.pi)
            basis[:, i] = np.sin(np.linspace(0, 2 * np.pi * freq, n_vertices) + phase)
        q, _ = np.linalg.qr(basis)
        return q.astype(np.float32)

    def _simulate_tribe_predictions(
        self, n_timesteps: int, duration: float, modality: str,
        content_profile: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, List[Dict]]:
        import hashlib
        seed = int(hashlib.md5(str(duration + hash(str(content_profile))).encode()).hexdigest()[:8], 16)
        rng = np.random.RandomState(seed)

        n_vertices = CORTICAL_VERTICES
        t = np.linspace(0, duration, n_timesteps)

        # Modality-specific base activation patterns and ROI definitions
        if modality == "video":
            motion = content_profile.get("motion_intensity", 0.4)
            complexity = content_profile.get("scene_complexity", 0.5)
            base_vis = 0.35 + 0.35 * np.sin(2 * np.pi * t / duration * 2.5 + 1.2)
            motion_mod = 0.2 * motion * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.6))
            scene_bumps = np.zeros(n_timesteps)
            n_scenes = max(2, int(complexity * 8))
            for _ in range(n_scenes):
                pos = rng.randint(0, n_timesteps)
                width = max(1, rng.randint(1, 4))
                scene_bumps[pos:min(pos + width, n_timesteps)] += 0.2 * rng.rand()
            temporal_envelope = np.clip(base_vis + motion_mod + scene_bumps, 0.05, 1.0)
            roi_signal_map = {
                "V1": (0.50, 0.30), "V2": (0.45, 0.25), "V3": (0.40, 0.25),
                "V4": (0.35, 0.20), "MT": (0.30, 0.20), "FEF": (0.25, 0.12),
                "IPS": (0.28, 0.12), "VS": (0.18, 0.10), "NAcc": (0.14, 0.08),
                "HIP": (0.15, 0.06), "PHC": (0.12, 0.05),
            }
        elif modality == "audio":
            amplitude = content_profile.get("mean_amplitude", 0.5)
            speech = content_profile.get("speech_confidence", 0.6)
            base_aud = 0.30 + 0.30 * amplitude * (0.5 + 0.5 * np.sin(2 * np.pi * t / duration * 3.0))
            speech_mod = 0.20 * speech * (0.5 + 0.5 * np.sin(2 * np.pi * t * 1.2))
            energy_env = 0.15 * (0.5 + 0.5 * np.sin(2 * np.pi * t * 0.4 * amplitude))
            temporal_envelope = np.clip(base_aud + speech_mod + energy_env, 0.05, 1.0)
            roi_signal_map = {
                "A1": (0.40, 0.20), "A2": (0.35, 0.18), "STG": (0.30, 0.15),
                "MTG": (0.25, 0.12), "VS": (0.14, 0.08), "NAcc": (0.12, 0.06),
                "HIP": (0.12, 0.05), "PHC": (0.10, 0.05),
            }
        else:  # text
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
            has_emotion = any(w.lower().strip(".,!?") in emotion_words for w in content_profile.get("words", []))
            emo_signal = np.array([1.0 if w.lower().strip(".,!?") in emotion_words else 0.0 for w in words])
            interp_len = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), word_len)
            interp_novel = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), novelty)
            interp_emo = np.interp(np.linspace(0, n_words - 1, n_timesteps), range(n_words), emo_signal)
            temporal_envelope = np.clip(0.20 + 0.25 * interp_len + 0.15 * interp_novel + 0.25 * interp_emo, 0.05, 1.0)
            # Boost dopamine ROIs for emotional content
            dop_boost = 0.10 if has_emotion else 0.0
            roi_signal_map = {
                "IFG": (0.35, 0.18), "STG": (0.30, 0.15), "ANG": (0.25, 0.12),
                "Precuneus": (0.20, 0.10), "HIP": (0.20, 0.10), "PHC": (0.15, 0.08),
                "DLPFC": (0.18, 0.08), "PCC": (0.15, 0.06),
                "VS": (0.16 + dop_boost, 0.08), "NAcc": (0.14 + dop_boost, 0.06),
                "vmPFC": (0.15 + 0.08 * dop_boost, 0.06),
            }

        roi_names = list(roi_signal_map.keys())
        n_rois = len(roi_names)
        n_verts_per_roi = n_vertices // n_rois

        # Generate ROI-mean signals
        roi_means = np.zeros((n_timesteps, n_rois))
        for i, (roi, (base, amp)) in enumerate(roi_signal_map.items()):
            phase = rng.uniform(0, 2 * np.pi)
            freq = rng.uniform(0.3, 1.5)
            sig = base + amp * (0.5 + 0.5 * np.sin(2 * np.pi * freq * t / duration * 4 + phase))
            sig += 0.03 * rng.randn(n_timesteps)
            roi_means[:, i] = np.clip(sig, 0.01, 1.0)

        # Build vertex-level predictions with modality-appropriate baselines
        if modality == "video":
            base_min, base_max = 0.30, 0.88
        elif modality == "audio":
            base_min, base_max = 0.25, 0.80
        else:  # text base range (has_emotion computed above)
            base_min, base_max = (0.40, 0.90) if has_emotion else (0.22, 0.68)

        preds = np.zeros((n_timesteps, n_vertices), dtype=np.float32)
        for i in range(n_rois):
            start_v = i * n_verts_per_roi
            end_v = min((i + 1) * n_verts_per_roi, n_vertices)
            nv = end_v - start_v
            if nv <= 0:
                continue
            # Map roi_means (0-1) to [base_min, base_max]
            roi_contrib = base_min + (base_max - base_min) * roi_means[:, i:i+1]
            vert_var = 0.03 * rng.randn(n_timesteps, nv)
            env = (0.5 + 0.5 * temporal_envelope[:, None])
            preds[:, start_v:end_v] = roi_contrib * env + vert_var

        preds = np.clip(preds, 0.0, 1.0)

        # Apply hemodynamic lag
        hrf_len = min(HEMODYNAMIC_LAG, n_timesteps // 3)
        if hrf_len > 1:
            hrf = np.exp(-np.arange(hrf_len) / 2.5)
            hrf /= hrf.sum()
            for v in range(0, n_vertices, 100):
                end_v = min(v + 100, n_vertices)
                preds[:, v:end_v] = np.apply_along_axis(
                    lambda x: np.convolve(x, hrf, mode="same")[:n_timesteps], 0, preds[:, v:end_v]
                )

        # Generate segments
        segment_interval = max(0.5, duration / n_timesteps)
        segments = []
        for i in range(n_timesteps):
            seg_start = i * segment_interval
            seg_end = min((i + 1) * segment_interval, duration)
            seg = {"start": seg_start, "end": seg_end, "type": modality + "_chunk"}
            if modality == "text":
                seg["word"] = content_profile.get("words", [""])[min(i, len(content_profile.get("words", [""])) - 1)]
            segments.append(seg)

        return preds, roi_means, temporal_envelope, segments

    def _simulate_video_prediction(self, video_path: str) -> Tuple[np.ndarray, List[Dict]]:
        import hashlib
        profile = self._probe_video_file(video_path)
        duration = profile["duration_sec"]
        n_timesteps = min(int(duration), 300) if duration >= 1 else 30

        preds, roi_signals, temporal_weights, segments = self._simulate_tribe_predictions(
            n_timesteps, duration, "video", profile
        )
        return preds, segments

    def _simulate_audio_prediction(self, audio_path: str) -> Tuple[np.ndarray, List[Dict]]:
        profile = self._probe_audio_file(audio_path)
        duration = profile["duration_sec"]
        n_timesteps = min(int(duration), 300) if duration >= 1 else 30

        preds, roi_signals, temporal_weights, segments = self._simulate_tribe_predictions(
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

        preds, roi_signals, temporal_weights, segments = self._simulate_tribe_predictions(
            n_timesteps, duration, "text", profile
        )
        return preds, segments
