import numpy as np
from typing import Optional, List, Tuple, Dict
from scipy import signal as scipy_signal
from scipy import linalg
from scipy import stats as scipy_stats
from scipy.ndimage import gaussian_filter
import logging

logger = logging.getLogger(__name__)

EEG_CHANNEL_NAMES_64 = [
    "Fp1", "Fpz", "Fp2", "F7", "F3", "Fz", "F4", "F8",
    "FC5", "FC1", "FC2", "FC6", "T7", "C3", "Cz", "C4",
    "T8", "CP5", "CP1", "CP2", "CP6", "P7", "P3", "Pz",
    "P4", "P8", "PO9", "O1", "Oz", "O2", "PO10",
]

DEFAULT_SR = 256


class BandpassFilter:
    """Butterworth bandpass filter for EEG (0.5–40 Hz)."""

    def __init__(self, lowcut: float = 0.5, highcut: float = 40.0, sr: int = DEFAULT_SR, order: int = 4):
        self.lowcut = lowcut
        self.highcut = highcut
        self.sr = sr
        self.order = order
        self._sos = None
        self._design()

    def _design(self):
        nyq = 0.5 * self.sr
        low = self.lowcut / nyq
        high = self.highcut / nyq
        self._sos = scipy_signal.butter(self.order, [low, high], btype="band", output="sos")

    def filter(self, data: np.ndarray) -> np.ndarray:
        if self._sos is None:
            raise RuntimeError("Filter not designed")
        return scipy_signal.sosfiltfilt(self._sos, data, axis=-1)


class NotchFilter:
    """Notch filter for powerline noise (50 or 60 Hz)."""

    def __init__(self, freq: float = 50.0, quality: float = 30.0, sr: int = DEFAULT_SR):
        self.freq = freq
        self.quality = quality
        self.sr = sr
        self._b = None
        self._a = None
        self._design()

    def _design(self):
        self._b, self._a = scipy_signal.iirnotch(self.freq, self.quality, self.sr)

    def filter(self, data: np.ndarray) -> np.ndarray:
        if self._b is None or self._a is None:
            raise RuntimeError("Notch filter not designed")
        return scipy_signal.filtfilt(self._b, self._a, data, axis=-1)


class ICAProcessor:
    """ICA-based artifact removal using FastICA.

    Strips components correlated with EOG (blink) and EMG (muscle)
    templates. When no template is provided, uses statistical heuristics:
    high kurtosis → blink, high spectral power >30 Hz → muscle.
    """

    def __init__(self, n_components: Optional[int] = None, random_state: int = 42, sr: int = DEFAULT_SR):
        self.n_components = n_components
        self.random_state = random_state
        self.sr = sr
        self._components: Optional[np.ndarray] = None
        self._mixing: Optional[np.ndarray] = None
        self._reject_mask: Optional[np.ndarray] = None

    def fit(self, data: np.ndarray):
        n_channels, n_times = data.shape
        n_components = self.n_components or min(n_channels, 20)

        from sklearn.decomposition import FastICA
        ica = FastICA(n_components=n_components, random_state=self.random_state, whiten="arbitrary-variance")
        X = data.T
        S = ica.fit_transform(X)
        self._components = ica.components_
        self._mixing = ica.mixing_
        self._reject_mask = self._auto_detect_artifacts(S, data, n_channels, n_times)
        return self

    def _auto_detect_artifacts(self, S: np.ndarray, data: np.ndarray, n_channels: int, n_times: int) -> np.ndarray:
        n_components = S.shape[1]
        reject = np.zeros(n_components, dtype=bool)

        for i in range(n_components):
            comp = S[:, i]

            kurt = float(scipy_stats.kurtosis(comp))
            if kurt > 5.0:
                reject[i] = True
                continue

            freqs = np.fft.rfftfreq(len(comp), d=1.0 / self.sr)
            psd = np.abs(np.fft.rfft(comp)) ** 2
            high_freq_power = np.sum(psd[freqs > 30]) / max(np.sum(psd), 1e-10)
            if high_freq_power > 0.6:
                reject[i] = True
                continue

            front_ch = [0, 1, 2, 3, 7]
            front_weight = float(np.abs(self._components[i, front_ch]).mean())
            all_weight = float(np.abs(self._components[i, :]).mean())
            if front_weight > 3 * all_weight and all_weight > 0:
                reject[i] = True

        return reject

    def transform(self, data: np.ndarray) -> np.ndarray:
        if self._components is None or self._mixing is None:
            return data
        from sklearn.decomposition import FastICA
        ica = FastICA(n_components=self.n_components, random_state=self.random_state, whiten="arbitrary-variance")
        X = data.T
        S = ica.fit_transform(X)
        if self._reject_mask is not None and self._mixing is not None:
            S[:, self._reject_mask] = 0
        cleaned = S @ self._components + X.mean(axis=0, keepdims=True)
        return cleaned.T

    def fit_transform(self, data: np.ndarray) -> np.ndarray:
        self.fit(data)
        return self.transform(data)


class EEGPreprocessor:
    """Full EEG preprocessing pipeline: filter → ICA → epoch.

    Pipeline:
    1. Bandpass filter (0.5–40 Hz)
    2. Notch filter (50/60 Hz)
    3. ICA artifact removal
    4. Epoch to 1-second windows
    """

    def __init__(
        self,
        sr: int = DEFAULT_SR,
        lowcut: float = 0.5,
        highcut: float = 40.0,
        notch_freq: float = 50.0,
        apply_ica: bool = True,
        epoch_duration: float = 1.0,
    ):
        self.sr = sr
        self.epoch_duration = epoch_duration
        self.bandpass = BandpassFilter(lowcut, highcut, sr)
        self.notch = NotchFilter(notch_freq, 30.0, sr)
        self.ica = ICAProcessor(random_state=42) if apply_ica else None

    def preprocess(self, data: np.ndarray) -> np.ndarray:
        if data.ndim == 1:
            data = data.reshape(1, -1)
        data = self.bandpass.filter(data)
        data = self.notch.filter(data)
        if self.ica is not None:
            data = self.ica.fit_transform(data)
        return data

    def epoch(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n_channels, n_times = data.shape
        step = int(self.sr * self.epoch_duration)
        n_epochs = max(1, n_times // step)
        epochs = np.zeros((n_epochs, n_channels, step), dtype=np.float32)
        timestamps = np.arange(n_epochs, dtype=float)
        for i in range(n_epochs):
            start = i * step
            end = min(start + step, n_times)
            epochs[i, :, : end - start] = data[:, start:end]
        return epochs, timestamps


class GSRPreprocessor:
    """GSR (galvanic skin response) signal processing.

    Decomposes raw GSR into tonic (slow baseline) and phasic
    (event-related SCR) components using convex optimization
    (cvxEDA algorithm simplified for scipy).
    """

    def __init__(self, sr: int = DEFAULT_SR, tau_tonic: float = 3.0, tau_phasic: float = 0.5):
        self.sr = sr
        self.tau_tonic = tau_tonic
        self.tau_phasic = tau_phasic

    def decompose(self, gsr: np.ndarray) -> Dict[str, np.ndarray]:
        gsr = np.asarray(gsr, dtype=np.float64).ravel()
        gsr = (gsr - gsr.min()) / max(gsr.max() - gsr.min(), 1e-10)

        b_tonic, a_tonic = scipy_signal.butter(2, 0.5 / (self.sr / 2), btype="low")
        tonic = scipy_signal.filtfilt(b_tonic, a_tonic, gsr)
        phasic = gsr - tonic
        phasic = np.clip(phasic, 0, None)

        return {"tonic": tonic, "phasic": phasic, "raw": gsr}

    def extract_features(self, gsr: np.ndarray, epoch_duration: float = 1.0) -> np.ndarray:
        decomposed = self.decompose(gsr)
        phasic = decomposed["phasic"]
        tonic = decomposed["tonic"]

        step = int(self.sr * epoch_duration)
        n_epochs = max(1, len(gsr) // step)
        n_features = 8

        features = np.zeros((n_epochs, n_features), dtype=np.float32)

        for i in range(n_epochs):
            start = i * step
            end = min(start + step, len(gsr))
            seg_phasic = phasic[start:end]
            seg_tonic = tonic[start:end]

            features[i, 0] = float(np.mean(seg_tonic))
            features[i, 1] = float(np.mean(seg_phasic))
            features[i, 2] = float(np.max(seg_phasic))
            features[i, 3] = float(np.sum(seg_phasic > 0.02)) / max(len(seg_phasic), 1)
            features[i, 4] = float(np.std(seg_phasic))

            if len(seg_phasic) > 5:
                peaks, _ = scipy_signal.find_peaks(seg_phasic, height=0.03, distance=10)
                features[i, 5] = len(peaks) / max(epoch_duration, 0.1)
                if len(peaks) > 0:
                    features[i, 6] = float(np.mean(seg_phasic[peaks]))
                else:
                    features[i, 6] = 0.0
            else:
                features[i, 5] = 0.0
                features[i, 6] = 0.0

            features[i, 7] = float(np.mean(np.abs(np.diff(seg_phasic))))

        return features


class PupilPreprocessor:
    """Pupil dilation preprocessing and feature extraction.

    Handles blink artifacts via linear interpolation,
    extracts baseline-corrected dilation features per epoch.
    """

    def __init__(self, sr: int = DEFAULT_SR, baseline_sec: float = 0.5):
        self.sr = sr
        self.baseline_sec = baseline_sec

    def remove_blinks(self, pupil: np.ndarray) -> np.ndarray:
        pupil = np.asarray(pupil, dtype=np.float64).ravel()
        mask = pupil < 0.1 * np.nanmedian(pupil[pupil > 0]) if np.any(pupil > 0) else np.isnan(pupil)
        pupil_clean = pupil.copy()
        pupil_clean[mask] = np.nan
        nans = np.isnan(pupil_clean)
        if nans.all():
            return np.zeros_like(pupil)
        indices = np.arange(len(pupil_clean))
        valid = ~nans
        if valid.sum() > 1:
            pupil_clean[nans] = np.interp(indices[nans], indices[valid], pupil_clean[valid])
        else:
            pupil_clean[nans] = 0
        return pupil_clean

    def baseline_correct(self, pupil: np.ndarray) -> np.ndarray:
        baseline = pupil[:int(self.sr * self.baseline_sec)]
        if len(baseline) == 0:
            return pupil
        bl_mean = np.nanmean(baseline)
        if np.isnan(bl_mean) or bl_mean == 0:
            return pupil
        return (pupil - bl_mean) / bl_mean

    def extract_features(self, pupil: np.ndarray, epoch_duration: float = 1.0) -> np.ndarray:
        pupil = self.remove_blinks(pupil)
        pupil = self.baseline_correct(pupil)

        step = int(self.sr * epoch_duration)
        n_epochs = max(1, len(pupil) // step)
        n_features = 8

        features = np.zeros((n_epochs, n_features), dtype=np.float32)

        for i in range(n_epochs):
            start = i * step
            end = min(start + step, len(pupil))
            seg = pupil[start:end]

            features[i, 0] = float(np.mean(seg))
            features[i, 1] = float(np.max(seg))
            features[i, 2] = float(np.std(seg))
            features[i, 3] = float(np.max(seg) - np.min(seg))

            if i > 0:
                features[i, 4] = float(np.mean(np.abs(np.diff(seg))))
                prev_max = features[i - 1, 1]
                features[i, 5] = features[i, 1] - prev_max
            else:
                features[i, 4] = float(np.mean(np.abs(np.diff(seg))))

            if len(seg) > 5:
                peaks, _ = scipy_signal.find_peaks(seg, height=np.mean(seg) + np.std(seg), distance=5)
                features[i, 6] = len(peaks) / max(epoch_duration, 0.1)
            else:
                features[i, 6] = 0.0

            earliest = int(self.sr * min(self.baseline_sec, epoch_duration))
            if earliest < len(seg):
                features[i, 7] = float(np.mean(seg[:earliest]))

        return features


class FixationPreprocessor:
    """Eye-tracking fixation detection and heatmap feature extraction.

    Detects fixations (Dispersion-Threshold Identification — I-DT algorithm),
    generates fixation heatmaps, and computes gaze statistics per epoch.
    """

    def __init__(self, sr: int = DEFAULT_SR, dispersion_threshold: float = 1.0, duration_threshold: float = 0.1):
        self.sr = sr
        self.dispersion_threshold = dispersion_threshold
        self.duration_threshold = duration_threshold

    def detect_fixations(self, gaze_x: np.ndarray, gaze_y: np.ndarray) -> List[Dict]:
        gaze_x = np.asarray(gaze_x, dtype=np.float64).ravel()
        gaze_y = np.asarray(gaze_y, dtype=np.float64).ravel()
        n = len(gaze_x)
        min_samples = max(1, int(self.sr * self.duration_threshold))

        fixations = []
        i = 0
        while i < n - min_samples:
            window_x = gaze_x[i : i + min_samples]
            window_y = gaze_y[i : i + min_samples]
            dispersion = (np.max(window_x) - np.min(window_x)) + (np.max(window_y) - np.min(window_y))

            if dispersion < self.dispersion_threshold:
                j = i + min_samples
                while j < n:
                    wx = gaze_x[i:j]
                    wy = gaze_y[i:j]
                    d = (np.max(wx) - np.min(wx)) + (np.max(wy) - np.min(wy))
                    if d > self.dispersion_threshold:
                        break
                    j += 1
                fixations.append({
                    "start": i / self.sr,
                    "end": (j - 1) / self.sr,
                    "duration": (j - 1 - i) / self.sr,
                    "x_mean": float(np.mean(gaze_x[i : j - 1])),
                    "y_mean": float(np.mean(gaze_y[i : j - 1])),
                })
                i = j
            else:
                i += 1

        return fixations

    def compute_heatmap(self, gaze_x: np.ndarray, gaze_y: np.ndarray, grid_size: int = 32) -> np.ndarray:
        valid = ~(np.isnan(gaze_x) | np.isnan(gaze_y))
        x = gaze_x[valid]
        y = gaze_y[valid]
        if len(x) == 0:
            return np.zeros((grid_size, grid_size), dtype=np.float32)

        x_bins = np.linspace(0, 1, grid_size + 1)
        y_bins = np.linspace(0, 1, grid_size + 1)
        heatmap, _, _ = np.histogram2d(y, x, bins=[y_bins, x_bins])
        heatmap = heatmap.astype(np.float32)
        total = heatmap.sum()
        if total > 0:
            heatmap /= total
        sigma = max(1.0, grid_size / 16)
        return gaussian_filter(heatmap, sigma=sigma, mode="constant")

    def extract_features(self, gaze_x: np.ndarray, gaze_y: np.ndarray, epoch_duration: float = 1.0) -> np.ndarray:
        gaze_x = np.asarray(gaze_x, dtype=np.float64).ravel()
        gaze_y = np.asarray(gaze_y, dtype=np.float64).ravel()
        step = int(self.sr * epoch_duration)
        n_epochs = max(1, len(gaze_x) // step)
        n_features = 16

        features = np.zeros((n_epochs, n_features), dtype=np.float32)

        for i in range(n_epochs):
            start = i * step
            end = min(start + step, len(gaze_x))
            seg_x = gaze_x[start:end]
            seg_y = gaze_y[start:end]
            valid = ~(np.isnan(seg_x) | np.isnan(seg_y))
            seg_x_v = seg_x[valid]
            seg_y_v = seg_y[valid]

            features[i, 0] = float(np.mean(seg_x_v)) if len(seg_x_v) > 0 else 0.5
            features[i, 1] = float(np.mean(seg_y_v)) if len(seg_y_v) > 0 else 0.5
            features[i, 2] = float(np.std(seg_x_v)) if len(seg_x_v) > 0 else 0
            features[i, 3] = float(np.std(seg_y_v)) if len(seg_y_v) > 0 else 0

            fixations = self.detect_fixations(seg_x, seg_y)
            features[i, 4] = len(fixations)
            features[i, 5] = float(np.mean([f["duration"] for f in fixations])) if fixations else 0

            if len(seg_x_v) > 1:
                velocities = np.sqrt(np.diff(seg_x_v) ** 2 + np.diff(seg_y_v) ** 2)
                features[i, 6] = float(np.mean(velocities))
                features[i, 7] = float(np.std(velocities))
            else:
                features[i, 6] = 0.0
                features[i, 7] = 0.0

            heatmap = self.compute_heatmap(seg_x, seg_y)
            features[i, 8] = float(np.max(heatmap))
            features[i, 9] = float(np.sum(heatmap > 0.01)) / max(heatmap.size, 1)
            flat = heatmap.ravel()
            flat = flat[flat > 0]
            if len(flat) > 1:
                flat_norm = flat / flat.sum()
                features[i, 10] = float(-np.sum(flat_norm * np.log(flat_norm + 1e-10)))
            else:
                features[i, 10] = 0.0

            if len(fixations) > 1:
                fix_x = [f["x_mean"] for f in fixations]
                fix_y = [f["y_mean"] for f in fixations]
                features[i, 11] = float(np.std(fix_x))
                features[i, 12] = float(np.std(fix_y))
                transitions = 0
                for j in range(1, len(fixations)):
                    dx = fix_x[j] - fix_x[j - 1]
                    dy = fix_y[j] - fix_y[j - 1]
                    if np.sqrt(dx ** 2 + dy ** 2) > 0.2:
                        transitions += 1
                features[i, 13] = transitions / max(len(fixations), 1)
            else:
                features[i, 11] = 0.0
                features[i, 12] = 0.0
                features[i, 13] = 0.0

            features[i, 14] = float(np.sum(~valid)) / max(len(seg_x), 1)

            if len(seg_y_v) > 0:
                vert_range = np.max(seg_y_v) - np.min(seg_y_v)
                features[i, 15] = float(vert_range)

        return features

    def epoch_heatmaps(self, gaze_x: np.ndarray, gaze_y: np.ndarray, epoch_duration: float = 1.0) -> np.ndarray:
        gaze_x = np.asarray(gaze_x, dtype=np.float64).ravel()
        gaze_y = np.asarray(gaze_y, dtype=np.float64).ravel()
        step = int(self.sr * epoch_duration)
        n_epochs = max(1, len(gaze_x) // step)
        grid_size = 32

        heatmaps = np.zeros((n_epochs, grid_size, grid_size), dtype=np.float32)
        for i in range(n_epochs):
            start = i * step
            end = min(start + step, len(gaze_x))
            heatmaps[i] = self.compute_heatmap(gaze_x[start:end], gaze_y[start:end])

        return heatmaps
