import numpy as np
from typing import Dict, Optional
import logging
import os
import argparse

from .emotion_classifier import EmotionClassifier, EMOTION_DIMENSIONS
from .video_timeline import ALL_FEATURE_NAMES

logger = logging.getLogger(__name__)


def generate_synthetic_dataset(
    n_samples: int = 1000,
    n_features: int = len(ALL_FEATURE_NAMES),
    noise: float = 0.05,
    random_state: int = 42,
) -> tuple:
    rng = np.random.RandomState(random_state)
    X = np.zeros((n_samples, n_features), dtype=np.float32)
    t = np.linspace(0, 4 * np.pi, n_samples)

    X[:, 0] = 0.3 + 0.25 * np.sin(t * 0.5) + 0.05 * rng.randn(n_samples)
    X[:, 1] = 0.4 + 0.2 * np.sin(t * 0.7 + 0.5) + 0.04 * rng.randn(n_samples)
    X[:, 2] = 0.5 + 0.15 * np.cos(t * 0.3) + 0.03 * rng.randn(n_samples)
    X[:, 3] = 0.5 + 0.1 * np.sin(t * 0.9 + 1.2) + 0.03 * rng.randn(n_samples)
    X[:, 4] = (np.abs(np.diff(X[:, 0], prepend=X[0, 0])) > 0.1).astype(float)
    X[:, 5] = 0.25 + 0.2 * np.abs(np.sin(t * 0.6)) + 0.05 * rng.randn(n_samples)
    X[:, 6] = 0.4 + 0.15 * np.sin(t * 0.4) + 0.03 * rng.randn(n_samples)
    X[:, 7] = 0.5 + 0.1 * np.sin(t * 0.8) + 0.03 * rng.randn(n_samples)
    X[:, 8] = 0.2 + 0.15 * np.abs(np.cos(t * 0.5)) + 0.02 * rng.randn(n_samples)
    X[:, 9] = 0.3 + 0.1 * np.sin(t * 0.3 + 2.0) + 0.04 * rng.randn(n_samples)
    X[:, 10] = 0.5 + 0.2 * np.sin(t * 0.55) + 0.04 * rng.randn(n_samples)

    X = np.clip(X, 0.0, 1.0)

    y: Dict[str, np.ndarray] = {}

    y["attention"] = np.clip(
        0.35 + 0.3 * X[:, 0] + 0.15 * (1 - X[:, 9]) + 0.1 * np.sin(t * 0.4) + noise * rng.randn(n_samples),
        0, 1,
    )

    y["arousal"] = np.clip(
        0.3 + 0.25 * X[:, 5] + 0.15 * X[:, 10] + 0.1 * np.abs(np.sin(t * 0.3)) + noise * rng.randn(n_samples),
        0, 1,
    )

    y["valence"] = np.clip(
        0.5 + 0.15 * X[:, 3] - 0.1 * X[:, 4] + 0.1 * np.cos(t * 0.2) + noise * rng.randn(n_samples),
        0, 1,
    )

    y["engagement"] = np.clip(
        0.4 * y["attention"] + 0.3 * y["arousal"] + 0.15 * X[:, 0] + 0.15 * X[:, 5] + noise * rng.randn(n_samples),
        0, 1,
    )

    y["cognitive_load"] = np.clip(
        0.3 + 0.15 * X[:, 1] + 0.15 * X[:, 6] + 0.1 * np.abs(np.diff(y["attention"], prepend=y["attention"][0]))
        + noise * rng.randn(n_samples),
        0, 1,
    )

    y["emotional_disengagement"] = np.clip(
        0.2 + 0.2 * X[:, 9] + 0.15 * X[:, 8] + 0.1 * (1 - y["engagement"]) + noise * rng.randn(n_samples),
        0, 1,
    )

    return X, y


def main(args=None):
    parser = argparse.ArgumentParser(description="Train Emotion-Attention Classifier")
    parser.add_argument("--samples", type=int, default=5000, help="Number of synthetic training samples")
    parser.add_argument("--n-estimators", type=int, default=100, help="Number of trees/estimators")
    parser.add_argument("--max-depth", type=int, default=12, help="Max tree depth")
    parser.add_argument("--output", type=str, default="./models/emotion_classifier.pkl", help="Output path for trained model")
    parser.add_argument("--noise", type=float, default=0.05, help="Training noise level")
    parser.add_argument("--cv", action="store_true", help="Run cross-validation")
    parser.add_argument("--gb", action="store_true", help="Use GradientBoosting instead of RandomForest")
    parser.add_argument("--real-data", type=str, default=None, help="Path to real training data (.npz)")
    parser.add_argument("--load", type=str, default=None, help="Load existing model and continue training")
    parsed = parser.parse_args(args)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    if parsed.load:
        logger.info(f"Loading existing model from {parsed.load}")
        classifier = EmotionClassifier().load(parsed.load)
    else:
        classifier = EmotionClassifier(
            n_estimators=parsed.n_estimators,
            max_depth=parsed.max_depth,
            use_gradient_boosting=parsed.gb,
        )

    if parsed.real_data:
        logger.info(f"Loading real training data from {parsed.real_data}")
        data = np.load(parsed.real_data)
        X = data["X"]
        y = {dim: data[dim] for dim in EMOTION_DIMENSIONS if dim in data}
        logger.info(f"Loaded {len(X)} real samples with {X.shape[1]} features")
    else:
        logger.info(f"Generating {parsed.samples} synthetic training samples")
        X, y = generate_synthetic_dataset(
            n_samples=parsed.samples,
            noise=parsed.noise,
        )

    if parsed.cv:
        logger.info("Running cross-validation...")
        cv_scores = classifier.cross_validate(X, y, cv=5)
        for dim, score in cv_scores.items():
            logger.info(f"  {dim}: CV R² = {score:.4f}")

    logger.info("Training classifier...")
    classifier.fit(X, y, feature_names=ALL_FEATURE_NAMES)

    out_dir = os.path.dirname(parsed.output) or "."
    os.makedirs(out_dir, exist_ok=True)
    classifier.save(parsed.output)

    for dim in EMOTION_DIMENSIONS:
        score = classifier.get_training_scores().get(dim, 0)
        logger.info(f"  {dim}: train score = {score:.4f}")

    logger.info(f"Model saved to {parsed.output}")
    logger.info(f"Feature names: {ALL_FEATURE_NAMES}")
    logger.info(f"Dimensions: {EMOTION_DIMENSIONS}")

    predictions = classifier.predict(X)
    logger.info("\nSample prediction (first 5 time steps):")
    for i in range(min(5, len(X))):
        vals = {dim: float(predictions[dim][i]) for dim in EMOTION_DIMENSIONS}
        logger.info(f"  t={i}: {vals}")

    feature_importance_report(classifier)


def feature_importance_report(classifier: EmotionClassifier):
    logger.info("\nFeature importance by dimension:")
    for dim in EMOTION_DIMENSIONS:
        imp = classifier.get_feature_importance(dim)
        if imp is not None:
            names = classifier.get_feature_names()
            top_idx = np.argsort(imp)[-3:][::-1]
            top_feats = [(names[i], imp[i]) for i in top_idx]
            logger.info(f"  {dim}: top features = {top_feats}")


if __name__ == "__main__":
    main()
