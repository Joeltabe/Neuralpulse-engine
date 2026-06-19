import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import cross_val_score
from scipy.ndimage import gaussian_filter1d
import logging
import pickle
import os

logger = logging.getLogger(__name__)

EMOTION_DIMENSIONS = [
    "attention",
    "arousal",
    "valence",
    "engagement",
    "cognitive_load",
    "emotional_disengagement",
]

EMOTION_LABELS: Dict[str, List[Tuple[float, float, str]]] = {
    "attention": [
        (0.0, 0.35, "Low Attention"),
        (0.35, 0.60, "Moderate Attention"),
        (0.60, 0.80, "High Attention"),
        (0.80, 1.0, "Intense Focus"),
    ],
    "arousal": [
        (0.0, 0.30, "Calm"),
        (0.30, 0.55, "Moderate Arousal"),
        (0.55, 0.75, "High Arousal"),
        (0.75, 1.0, "Extreme Arousal"),
    ],
    "valence": [
        (0.0, 0.30, "Negative Valence"),
        (0.30, 0.45, "Slightly Negative"),
        (0.45, 0.55, "Neutral"),
        (0.55, 0.70, "Slightly Positive"),
        (0.70, 1.0, "Positive Valence"),
    ],
    "engagement": [
        (0.0, 0.30, "Disengaged"),
        (0.30, 0.55, "Low Engagement"),
        (0.55, 0.75, "Engaged"),
        (0.75, 1.0, "Highly Engaged"),
    ],
    "cognitive_load": [
        (0.0, 0.30, "Low Load"),
        (0.30, 0.55, "Moderate Load"),
        (0.55, 0.75, "High Load"),
        (0.75, 1.0, "Overloaded"),
    ],
    "emotional_disengagement": [
        (0.0, 0.30, "Emotionally Connected"),
        (0.30, 0.50, "Slightly Detached"),
        (0.50, 0.70, "Disengaging"),
        (0.70, 1.0, "Emotionally Withdrawn"),
    ],
}


def _label_from_value(dim: str, value: float) -> str:
    buckets = EMOTION_LABELS.get(dim, [])
    for lo, hi, label in buckets:
        if lo <= value < hi:
            return label
    return buckets[-1][2] if buckets else ""


class EmotionClassifier:
    """Multi-dimension emotion-attention classifier.

    Predicts 6 brain-state dimensions from video/audio features:
    - attention: sustained visual/auditory attention
    - arousal: physiological/emotional arousal
    - valence: positive/negative emotional valence
    - engagement: overall engagement level
    - cognitive_load: mental effort required
    - emotional_disengagement: withdrawal of emotional investment

    Uses per-dimension RandomForestRegressors with optional
    temporal smoothing and confidence calibration.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 12,
        temporal_sigma: float = 1.5,
        use_gradient_boosting: bool = False,
        random_state: int = 42,
    ):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.temporal_sigma = temporal_sigma
        self.use_gradient_boosting = use_gradient_boosting
        self.random_state = random_state

        self.models: Dict[str, Any] = {}
        self.scaler = StandardScaler()
        self._fitted = False
        self._n_features = 0
        self._feature_names: List[str] = []
        self._train_scores: Dict[str, float] = {}
        self._feature_importances: Dict[str, np.ndarray] = {}

    def _build_model(self):
        base_cls = GradientBoostingRegressor if self.use_gradient_boosting else RandomForestRegressor
        kwargs = dict(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1,
        )
        if self.use_gradient_boosting:
            kwargs["learning_rate"] = 0.1
        return base_cls(**kwargs)

    def fit(
        self,
        X: np.ndarray,
        y: Dict[str, np.ndarray],
        feature_names: Optional[List[str]] = None,
    ) -> "EmotionClassifier":
        n_samples = X.shape[0]
        if feature_names is None:
            self._feature_names = [f"feat_{i}" for i in range(X.shape[1])]
        else:
            self._feature_names = feature_names

        self._n_features = X.shape[1]

        X_scaled = self.scaler.fit_transform(X)

        for dim in EMOTION_DIMENSIONS:
            if dim not in y:
                logger.warning(f"Dimension '{dim}' not in training data, skipping")
                continue
            y_dim = np.asarray(y[dim])
            if y_dim.ndim == 1:
                y_dim = y_dim.reshape(-1, 1)
            model = self._build_model()
            model.fit(X_scaled, y_dim.ravel())
            self.models[dim] = model
            if hasattr(model, "feature_importances_"):
                self._feature_importances[dim] = model.feature_importances_
            y_pred = model.predict(X_scaled)
            mse = float(np.mean((y_dim.ravel() - y_pred) ** 2))
            self._train_scores[dim] = max(0.0, 1.0 - mse)
            logger.info(f"  {dim}: train MSE={mse:.4f}, score={self._train_scores[dim]:.4f}")

        self._fitted = True
        return self

    def predict(self, X: np.ndarray, smooth: bool = True) -> Dict[str, np.ndarray]:
        if not self._fitted:
            raise RuntimeError("Classifier not fitted. Call fit() first.")
        if X.shape[1] != self._n_features:
            raise ValueError(
                f"Expected {self._n_features} features, got {X.shape[1]}"
            )

        X_scaled = self.scaler.transform(X)
        results = {}
        for dim in EMOTION_DIMENSIONS:
            if dim not in self.models:
                results[dim] = np.full(X.shape[0], 0.5)
                continue
            pred = self.models[dim].predict(X_scaled)
            pred = np.clip(pred, 0.0, 1.0)
            if smooth and self.temporal_sigma > 0 and len(pred) > 3:
                pred = gaussian_filter1d(pred, sigma=self.temporal_sigma, mode="nearest")
            results[dim] = pred
        return results

    def predict_single(self, features: np.ndarray) -> Dict[str, float]:
        if features.ndim == 1:
            features = features.reshape(1, -1)
        results = self.predict(features, smooth=False)
        return {dim: float(values[0]) for dim, values in results.items()}

    def predict_with_confidence(
        self, X: np.ndarray, smooth: bool = True, n_replicates: int = 10
    ) -> Dict[str, Dict[str, np.ndarray]]:
        if not self._fitted:
            raise RuntimeError("Classifier not fitted.")
        X_scaled = self.scaler.transform(X)

        outputs: Dict[str, Dict[str, np.ndarray]] = {}
        for dim in EMOTION_DIMENSIONS:
            if dim not in self.models:
                base = np.full(X.shape[0], 0.5)
                outputs[dim] = {"mean": base, "std": np.full(X.shape[0], 0.1)}
                continue

            model = self.models[dim]
            if isinstance(model, RandomForestRegressor):
                all_preds = np.zeros((X.shape[0], n_replicates))
                trees = model.estimators_[:n_replicates]
                for i, tree in enumerate(trees):
                    all_preds[:, i] = tree.predict(X_scaled)
                mean_pred = np.mean(all_preds, axis=1)
                std_pred = np.std(all_preds, axis=1)
            else:
                mean_pred = model.predict(X_scaled)
                residuals = np.abs(mean_pred - model.predict(X_scaled))
                std_pred = np.full_like(mean_pred, np.mean(residuals))

            mean_pred = np.clip(mean_pred, 0.0, 1.0)
            if smooth and self.temporal_sigma > 0 and len(mean_pred) > 3:
                mean_pred = gaussian_filter1d(mean_pred, sigma=self.temporal_sigma, mode="nearest")

            outputs[dim] = {"mean": mean_pred, "std": std_pred}

        return outputs

    def get_feature_importance(self, dim: str) -> Optional[np.ndarray]:
        return self._feature_importances.get(dim)

    def get_feature_names(self) -> List[str]:
        return self._feature_names

    def cross_validate(
        self, X: np.ndarray, y: Dict[str, np.ndarray], cv: int = 5
    ) -> Dict[str, float]:
        X_scaled = self.scaler.fit_transform(X)
        cv_scores: Dict[str, float] = {}
        for dim in EMOTION_DIMENSIONS:
            if dim not in y:
                continue
            y_dim = np.asarray(y[dim]).ravel()
            model = self._build_model()
            scores = cross_val_score(model, X_scaled, y_dim, cv=cv, scoring="r2")
            cv_scores[dim] = float(np.mean(scores))
            logger.info(f"  {dim}: CV R2={cv_scores[dim]:.4f} +/- {float(np.std(scores)):.4f}")
        return cv_scores

    def save(self, path: str):
        data = {
            "models": self.models,
            "scaler": self.scaler,
            "n_features": self._n_features,
            "feature_names": self._feature_names,
            "train_scores": self._train_scores,
            "feature_importances": self._feature_importances,
            "params": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "temporal_sigma": self.temporal_sigma,
                "use_gradient_boosting": self.use_gradient_boosting,
                "random_state": self.random_state,
            },
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(data, f)
        logger.info(f"Classifier saved to {path}")

    def load(self, path: str) -> "EmotionClassifier":
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.models = data["models"]
        self.scaler = data["scaler"]
        self._n_features = data["n_features"]
        self._feature_names = data.get("feature_names", [])
        self._train_scores = data.get("train_scores", {})
        self._feature_importances = data.get("feature_importances", {})
        if "params" in data:
            params = data["params"]
            self.n_estimators = params.get("n_estimators", self.n_estimators)
            self.max_depth = params.get("max_depth", self.max_depth)
            self.temporal_sigma = params.get("temporal_sigma", self.temporal_sigma)
            self.use_gradient_boosting = params.get("use_gradient_boosting", self.use_gradient_boosting)
        self._fitted = True
        logger.info(f"Classifier loaded from {path}")
        return self

    def is_fitted(self) -> bool:
        return self._fitted

    def get_training_scores(self) -> Dict[str, float]:
        return dict(self._train_scores)

    def summary(self) -> Dict[str, Any]:
        return {
            "fitted": self._fitted,
            "n_features": self._n_features,
            "dimensions": list(self.models.keys()),
            "feature_names": self._feature_names,
            "train_scores": self._train_scores,
            "n_estimators": self.n_estimators,
            "max_depth": self.max_depth,
            "temporal_sigma": self.temporal_sigma,
        }


def compute_emotion_labels(
    predictions: Dict[str, np.ndarray]
) -> Dict[str, List[str]]:
    labels: Dict[str, List[str]] = {}
    for dim, values in predictions.items():
        labels[dim] = [_label_from_value(dim, float(v)) for v in values]
    return labels


def detect_emotional_events(
    predictions: Dict[str, np.ndarray],
    timestamps: np.ndarray,
    attention_threshold: float = 0.35,
    arousal_threshold: float = 0.65,
    disengagement_threshold: float = 0.55,
) -> List[Dict[str, Any]]:
    events = []

    if "attention" in predictions:
        attn = predictions["attention"]
        for i in range(1, len(attn)):
            if attn[i] < attention_threshold and attn[i - 1] >= attention_threshold:
                events.append({
                    "timestamp": float(timestamps[i]),
                    "type": "attention_drop",
                    "severity": "critical" if attn[i] < attention_threshold - 0.15 else "moderate",
                    "value_before": float(attn[i - 1]),
                    "value_after": float(attn[i]),
                    "description": f"Attention drop to {attn[i]:.0%} at {timestamps[i]:.1f}s",
                })

    if "arousal" in predictions:
        aro = predictions["arousal"]
        for i in range(1, len(aro)):
            if aro[i] > arousal_threshold and aro[i - 1] <= arousal_threshold:
                events.append({
                    "timestamp": float(timestamps[i]),
                    "type": "arousal_spike",
                    "severity": "high" if aro[i] > 0.8 else "moderate",
                    "value": float(aro[i]),
                    "description": f"Arousal spike to {aro[i]:.0%} at {timestamps[i]:.1f}s",
                })

    if "emotional_disengagement" in predictions:
        dis = predictions["emotional_disengagement"]
        for i in range(1, len(dis)):
            if dis[i] > disengagement_threshold and dis[i - 1] <= disengagement_threshold:
                events.append({
                    "timestamp": float(timestamps[i]),
                    "type": "emotional_disengagement",
                    "severity": "critical" if dis[i] > 0.75 else "moderate",
                    "value": float(dis[i]),
                    "description": f"Emotional disengagement at {timestamps[i]:.1f}s",
                })

    if "valence" in predictions and "arousal" in predictions:
        val = predictions["valence"]
        aro = predictions["arousal"]
        for i in range(1, len(val)):
            if val[i] < 0.35 and aro[i] > 0.6:
                events.append({
                    "timestamp": float(timestamps[i]),
                    "type": "negative_high_arousal",
                    "severity": "high",
                    "valence": float(val[i]),
                    "arousal": float(aro[i]),
                    "description": f"Negative high-arousal state at {timestamps[i]:.1f}s",
                })
            elif val[i] > 0.65 and aro[i] > 0.6:
                events.append({
                    "timestamp": float(timestamps[i]),
                    "type": "positive_high_arousal",
                    "severity": "positive",
                    "valence": float(val[i]),
                    "arousal": float(aro[i]),
                    "description": f"Positive high-arousal (excitement) at {timestamps[i]:.1f}s",
                })

    events.sort(key=lambda e: e["timestamp"])
    return events
