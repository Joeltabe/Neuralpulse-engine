import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from scipy import signal as scipy_signal
from scipy.ndimage import gaussian_filter1d
from PIL import Image
import logging
import os
import tempfile
import subprocess
import struct
import wave
from io import BytesIO

from .emotion_classifier import EmotionClassifier, compute_emotion_labels, detect_emotional_events

logger = logging.getLogger(__name__)

VIDEO_FEATURE_NAMES = [
    "motion_energy",
    "color_variance",
    "brightness",
    "color_warmth",
    "scene_change",
]

AUDIO_FEATURE_NAMES = [
    "audio_energy",
    "spectral_centroid",
    "spectral_rolloff",
    "zero_crossing_rate",
    "silence_ratio",
    "audio_emotional_intensity",
]

ALL_FEATURE_NAMES = VIDEO_FEATURE_NAMES + AUDIO_FEATURE_NAMES


def _check_ffmpeg() -> bool:
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.SubprocessError):
        return False


_HAS_FFMPEG = None


def has_ffmpeg() -> bool:
    global _HAS_FFMPEG
    if _HAS_FFMPEG is None:
        _HAS_FFMPEG = _check_ffmpeg()
    return _HAS_FFMPEG


class VideoFeatureExtractor:
    """Extracts per-frame visual features from video using ffmpeg + Pillow.

    Falls back to simulated features when ffmpeg is unavailable.
    """

    def __init__(self, target_fps: int = 30, resize_width: int = 224):
        self.target_fps = target_fps
        self.resize_width = resize_width

    def extract(self, video_path: str) -> np.ndarray:
        if has_ffmpeg():
            return self._extract_ffmpeg(video_path)
        logger.warning("ffmpeg not found. Using simulated video features.")
        return self._simulate_features(video_path)

    def _extract_ffmpeg(self, video_path: str) -> np.ndarray:
        frames = self._read_frames(video_path)
        if len(frames) == 0:
            logger.warning("No frames extracted from video, using simulation")
            return self._simulate_features(video_path)

        n_frames = len(frames)
        features = np.zeros((n_frames, len(VIDEO_FEATURE_NAMES)), dtype=np.float32)

        prev_gray = None
        for i, frame in enumerate(frames):
            gray = np.mean(frame, axis=2) if frame.ndim == 3 else frame

            brightness = float(np.mean(gray)) / 255.0
            features[i, 2] = brightness

            color_var = float(np.std(frame, axis=(0, 1)).mean()) / 255.0
            features[i, 1] = color_var

            if frame.ndim == 3:
                r_mean = float(np.mean(frame[:, :, 0]))
                total = float(np.mean(frame.sum(axis=2)))
                warmth = r_mean / total if total > 0 else 0.5
            else:
                warmth = 0.5
            features[i, 3] = np.clip(warmth, 0, 1)

            if prev_gray is not None:
                diff = np.mean(np.abs(gray.astype(float) - prev_gray.astype(float)))
                motion = np.clip(diff / 255.0, 0, 1)
                scene_change = 1.0 if diff > 30 else 0.0
            else:
                motion = 0.0
                scene_change = 0.0
            features[i, 0] = motion
            features[i, 4] = scene_change

            prev_gray = gray

        features[:, 0] = gaussian_filter1d(features[:, 0], sigma=1.0, mode="nearest")
        return features

    def _read_frames(self, video_path: str) -> List[np.ndarray]:
        frames = []
        try:
            import subprocess
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-vf", f"fps={self.target_fps},scale={self.resize_width}:-1",
                "-f", "image2pipe",
                "-pix_fmt", "rgb24",
                "-vcodec", "rawvideo",
                "-",
            ]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8
            )
            width = self.resize_width
            while True:
                raw_bytes = proc.stdout.read(width * width * 3)
                if len(raw_bytes) < width * width * 3:
                    break
                frame = np.frombuffer(raw_bytes, dtype=np.uint8).reshape((width, width, 3))
                frames.append(frame)
            proc.wait()
        except Exception as e:
            logger.warning(f"Frame extraction failed: {e}")
        return frames

    def _simulate_features(self, video_path: str) -> np.ndarray:
        duration = 30.0
        try:
            duration = max(10.0, os.path.getsize(video_path) / 50000)
            duration = min(duration, 600.0)
        except Exception:
            pass

        n_frames = int(duration * self.target_fps)
        t = np.linspace(0, duration, n_frames)
        features = np.zeros((n_frames, len(VIDEO_FEATURE_NAMES)), dtype=np.float32)

        features[:, 0] = 0.3 + 0.2 * np.sin(2 * np.pi * t / duration * 3) + 0.05 * np.random.randn(n_frames)
        features[:, 1] = 0.4 + 0.15 * np.sin(2 * np.pi * t / duration * 2 + 0.5) + 0.03 * np.random.randn(n_frames)
        features[:, 2] = 0.5 + 0.1 * np.sin(2 * np.pi * t / duration * 1.5) + 0.02 * np.random.randn(n_frames)
        features[:, 3] = 0.5 + 0.1 * np.sin(2 * np.pi * t / duration * 2.5) + 0.03 * np.random.randn(n_frames)
        features[:, 4] = 0.0

        n_scenes = max(2, int(duration / 5))
        rng = np.random.RandomState(42)
        for _ in range(n_scenes):
            pos = rng.randint(0, n_frames)
            features[min(pos, n_frames - 1), 4] = 1.0

        features = np.clip(features, 0.0, 1.0)
        return features


class AudioFeatureExtractor:
    """Extracts per-second audio features from audio/WAV files.

    Uses scipy.signal for spectral analysis.
    Works with WAV files natively; requires ffmpeg for other formats.
    """

    def __init__(self, sr: int = 22050, n_fft: int = 1024, hop_length: int = 512):
        self.sr = sr
        self.n_fft = n_fft
        self.hop_length = hop_length

    def extract(self, audio_path: str) -> np.ndarray:
        audio, sr = self._load_audio(audio_path)
        if audio is None or len(audio) == 0:
            logger.warning("Could not load audio, using simulated features")
            return self._simulate_features(audio_path)

        return self._extract_from_wave(audio, sr)

    def _load_audio(self, path: str) -> Tuple[Optional[np.ndarray], int]:
        ext = os.path.splitext(path)[1].lower()
        if ext == ".wav":
            return self._load_wav(path)
        if has_ffmpeg():
            return self._load_with_ffmpeg(path)
        logger.warning(f"Cannot decode {ext} without ffmpeg")
        return None, self.sr

    def _load_wav(self, path: str) -> Tuple[Optional[np.ndarray], int]:
        try:
            with wave.open(path, "rb") as wf:
                sr = wf.getframerate()
                n_frames = wf.getnframes()
                n_channels = wf.getnchannels()
                raw = wf.readframes(n_frames)
                if wf.getsampwidth() == 2:
                    dtype = np.int16
                elif wf.getsampwidth() == 4:
                    dtype = np.int32
                else:
                    dtype = np.uint8
                audio = np.frombuffer(raw, dtype=dtype).astype(np.float32)
                if n_channels > 1:
                    audio = audio.reshape(-1, n_channels).mean(axis=1)
                max_val = np.iinfo(dtype).max if dtype in (np.int16, np.int32) else 255.0
                audio = audio / max_val
                if sr != self.sr:
                    from scipy.signal import resample
                    n_target = int(len(audio) * self.sr / sr)
                    audio = resample(audio, n_target)
                return audio, self.sr
        except Exception as e:
            logger.warning(f"WAV load failed: {e}")
            return None, self.sr

    def _load_with_ffmpeg(self, path: str) -> Tuple[Optional[np.ndarray], int]:
        try:
            cmd = [
                "ffmpeg", "-i", path,
                "-f", "wav",
                "-acodec", "pcm_s16le",
                "-ar", str(self.sr),
                "-ac", "1",
                "-",
            ]
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 8
            )
            raw, _ = proc.communicate()
            proc.wait()
            if len(raw) < 44:
                return None, self.sr
            audio = np.frombuffer(raw[44:], dtype=np.int16).astype(np.float32) / 32768.0
            return audio, self.sr
        except Exception as e:
            logger.warning(f"FFmpeg audio extraction failed: {e}")
            return None, self.sr

    def _extract_from_wave(self, audio: np.ndarray, sr: int) -> np.ndarray:
        duration = len(audio) / sr
        n_seconds = max(1, int(np.ceil(duration)))
        hop = int(sr / 2)
        window = int(sr)
        n_frames = max(1, 1 + (len(audio) - window) // hop)
        features = np.zeros((n_frames, len(AUDIO_FEATURE_NAMES)), dtype=np.float32)

        for i in range(n_frames):
            start = i * hop
            end = min(start + window, len(audio))
            segment = audio[start:end]
            if len(segment) < sr // 4:
                segment = np.pad(segment, (0, max(0, sr // 4 - len(segment))))

            rms = float(np.sqrt(np.mean(segment ** 2)))
            features[i, 0] = np.clip(rms * 5, 0, 1)

            zcr = float(np.mean(np.abs(np.diff(np.sign(segment))))) / 2.0
            features[i, 3] = np.clip(zcr, 0, 1)

            silence = float(np.mean(np.abs(segment) < 0.02))
            features[i, 4] = silence

            freqs, psd = self._compute_spectrum(segment, sr)
            if len(freqs) > 0 and len(psd) > 0:
                centroid = float(np.sum(freqs * psd) / np.sum(psd)) if np.sum(psd) > 0 else 0
                features[i, 1] = np.clip(centroid / (sr / 2), 0, 1)

                cumsum = np.cumsum(psd)
                total = cumsum[-1] if cumsum[-1] > 0 else 1
                rolloff_idx = np.searchsorted(cumsum, 0.85 * total)
                rolloff = freqs[rolloff_idx] / (sr / 2) if rolloff_idx < len(freqs) else 0.5
                features[i, 2] = np.clip(rolloff, 0, 1)
            else:
                features[i, 1] = 0.5
                features[i, 2] = 0.5

            energy_ratio = float(np.sum(psd[5:]) / max(np.sum(psd), 1e-10)) if len(psd) > 5 else 0.5
            emo = 0.5 + 0.3 * (features[i, 0] - 0.5) + 0.2 * (energy_ratio - 0.5)
            features[i, 5] = np.clip(emo, 0, 1)

        features[:, 0] = gaussian_filter1d(features[:, 0], sigma=0.5, mode="nearest")
        return features

    def _compute_spectrum(
        self, segment: np.ndarray, sr: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        n = len(segment)
        if n < 4:
            return np.array([]), np.array([])
        windowed = segment * np.hanning(n)
        spectrum = np.fft.rfft(windowed)
        psd = np.abs(spectrum) ** 2
        freqs = np.fft.rfftfreq(n, d=1.0 / sr)
        return freqs, psd

    def _simulate_features(self, audio_path: str) -> np.ndarray:
        duration = 30.0
        try:
            duration = max(5.0, os.path.getsize(audio_path) / 30000)
            duration = min(duration, 600.0)
        except Exception:
            pass

        n_frames = max(1, int(duration / 0.5))
        t = np.linspace(0, duration, n_frames)
        features = np.zeros((n_frames, len(AUDIO_FEATURE_NAMES)), dtype=np.float32)

        features[:, 0] = 0.3 + 0.2 * np.sin(2 * np.pi * t / duration * 4) + 0.05 * np.random.randn(n_frames)
        features[:, 1] = 0.4 + 0.15 * np.sin(2 * np.pi * t / duration * 2) + 0.03 * np.random.randn(n_frames)
        features[:, 2] = 0.5 + 0.1 * np.sin(2 * np.pi * t / duration * 3) + 0.03 * np.random.randn(n_frames)
        features[:, 3] = 0.3 + 0.1 * np.sin(2 * np.pi * t / duration * 5) + 0.02 * np.random.randn(n_frames)
        features[:, 4] = 0.2 + 0.1 * np.sin(2 * np.pi * t / duration * 1.5) + 0.03 * np.random.randn(n_frames)
        features[:, 5] = 0.5 + 0.15 * np.sin(2 * np.pi * t / duration * 2.5) + 0.03 * np.random.randn(n_frames)

        features = np.clip(features, 0.0, 1.0)
        return features


class TimelineAligner:
    """Orchestrates video/audio feature extraction and timeline alignment.

    Pipeline:
    1. Extract visual features (frame-level) via VideoFeatureExtractor
    2. Extract audio features (frame-level) via AudioFeatureExtractor
    3. Align both to 1-second timeline bins
    4. Return aligned feature matrix + timestamp array
    """

    def __init__(
        self,
        video_extractor: Optional[VideoFeatureExtractor] = None,
        audio_extractor: Optional[AudioFeatureExtractor] = None,
        classifier: Optional[EmotionClassifier] = None,
    ):
        self.video_extractor = video_extractor or VideoFeatureExtractor()
        self.audio_extractor = audio_extractor or AudioFeatureExtractor()
        self.classifier = classifier

    def extract_features(self, video_path: str) -> Tuple[np.ndarray, np.ndarray]:
        video_feats = self.video_extractor.extract(video_path)
        audio_feats = self.audio_extractor.extract(video_path)

        aligned, timestamps = self._align_to_seconds(video_feats, audio_feats)
        return aligned, timestamps

    def _align_to_seconds(
        self,
        video_feats: np.ndarray,
        audio_feats: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        n_video = video_feats.shape[0]
        n_audio = audio_feats.shape[0]

        video_fps = max(n_video / 30.0, 1.0)
        audio_fps = max(n_audio / 30.0, 1.0)

        n_seconds = max(n_video, n_audio)
        if n_seconds == 0:
            n_seconds = 30

        video_per_sec = max(1, int(video_fps))
        audio_per_sec = max(1, int(audio_fps))

        aligned = np.zeros((n_seconds, len(ALL_FEATURE_NAMES)), dtype=np.float32)

        for s in range(n_seconds):
            v_start = int(s * video_fps)
            v_end = min(int((s + 1) * video_fps), n_video)
            if v_end > v_start:
                aligned[s, :len(VIDEO_FEATURE_NAMES)] = video_feats[v_start:v_end].mean(axis=0)
            elif v_start < n_video:
                aligned[s, :len(VIDEO_FEATURE_NAMES)] = video_feats[v_start]

            a_start = int(s * audio_fps)
            a_end = min(int((s + 1) * audio_fps), n_audio)
            if a_end > a_start:
                aligned[s, len(VIDEO_FEATURE_NAMES):] = audio_feats[a_start:a_end].mean(axis=0)
            elif a_start < n_audio:
                aligned[s, len(VIDEO_FEATURE_NAMES):] = audio_feats[a_start]

        timestamps = np.arange(n_seconds, dtype=float)
        return aligned, timestamps

    def analyze(
        self, video_path: str
    ) -> Dict[str, Any]:
        features, timestamps = self.extract_features(video_path)

        if self.classifier and self.classifier.is_fitted():
            predictions = self.classifier.predict(features)
            confidence = self.classifier.predict_with_confidence(features)
        else:
            predictions = self._predict_simulated(features, timestamps)
            confidence = {
                dim: {"mean": predictions[dim], "std": np.full(len(timestamps), 0.1)}
                for dim in predictions
            }

        labels = compute_emotion_labels(predictions)
        events = detect_emotional_events(predictions, timestamps)

        return {
            "features": features,
            "timestamps": timestamps,
            "predictions": predictions,
            "confidence": confidence,
            "labels": labels,
            "events": events,
            "feature_names": ALL_FEATURE_NAMES,
        }

    def _predict_simulated(
        self, features: np.ndarray, timestamps: np.ndarray
    ) -> Dict[str, np.ndarray]:
        n = len(timestamps)
        t = timestamps / max(timestamps[-1], 1)
        results = {}

        results["attention"] = np.clip(
            0.4 + 0.3 * np.sin(2 * np.pi * t * 2.5 + 1.2)
            + 0.1 * features[:, 0]  # motion energy
            + 0.05 * features[:, 5]  # audio energy
            - 0.15 * features[:, 9],  # silence ratio
            0, 1,
        )

        results["arousal"] = np.clip(
            0.3 + 0.3 * np.sin(2 * np.pi * t * 3.0)
            + 0.2 * features[:, 10]  # audio emotional intensity
            + 0.1 * features[:, 5],  # audio energy
            0, 1,
        )

        results["valence"] = np.clip(
            0.5 + 0.15 * np.sin(2 * np.pi * t * 1.5 + 0.8)
            + 0.1 * features[:, 3]  # color warmth
            - 0.1 * features[:, 4],  # scene change
            0, 1,
        )

        attn = results["attention"]
        aro = results["arousal"]
        results["engagement"] = np.clip(0.5 * attn + 0.3 * aro + 0.2 * features[:, 0], 0, 1)

        results["cognitive_load"] = np.clip(
            0.3 + 0.2 * features[:, 1]  # color variance
            + 0.15 * (1 - features[:, 9])  # audio complexity (1 - silence ratio)
            + 0.1 * np.abs(np.diff(attn, prepend=attn[0])),
            0, 1,
        )

        results["emotional_disengagement"] = np.clip(
            0.2 + 0.25 * (1 - results["engagement"])
            + 0.15 * features[:, 9]  # silence ratio
            + 0.1 * np.abs(np.diff(valence := results["valence"], prepend=valence[0])),
            0, 1,
        )

        return results

    def get_feature_names(self) -> List[str]:
        return ALL_FEATURE_NAMES
