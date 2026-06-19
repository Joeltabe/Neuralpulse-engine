import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ModalityEncoder(nn.Module):
    """Projects a modality's features into a common latent space."""

    def __init__(self, input_dim: int, output_dim: int = 64, hidden_dim: Optional[int] = None):
        super().__init__()
        h = hidden_dim or max(output_dim * 2, input_dim * 2)
        self.net = nn.Sequential(
            nn.Linear(input_dim, h),
            nn.LayerNorm(h),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(h, output_dim),
            nn.LayerNorm(output_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class MultiModalFusion(nn.Module):
    """Multi-modal fusion layer → 128-dim engagement vector.

    Architecture:
        EEG features (128)  ──→ ModalityEncoder ──┐
        GSR features (8)    ──→ ModalityEncoder ──┤
        Pupil features (8)  ──→ ModalityEncoder ──┤──→ Concat ──→ Projection(→128) ──→ Engagement Vector
        Fixation features (16) ─→ ModalityEncoder ─┤
        Video features (11) ──→ ModalityEncoder ──┘

    Each modality is projected into a 64-dim latent space independently,
    then concatenated and projected to 128-dim.

    Supports missing modalities via zero-masking.
    """

    ENGAGEMENT_DIM = 128
    MODALITY_LATENT_DIM = 64

    MODALITY_DIMS = {
        "eeg": 128,
        "gsr": 8,
        "pupil": 8,
        "fixation": 16,
        "video": 11,
    }

    def __init__(
        self,
        modalities: Optional[List[str]] = None,
        engagement_dim: int = 128,
        modality_latent_dim: int = 64,
        fusion_hidden: int = 256,
        dropout: float = 0.3,
    ):
        super().__init__()
        self.engagement_dim = engagement_dim
        self.modality_latent_dim = modality_latent_dim
        self.modalities = modalities or list(self.MODALITY_DIMS.keys())

        self.encoders = nn.ModuleDict()
        for mod in self.modalities:
            input_dim = self.MODALITY_DIMS.get(mod, 64)
            self.encoders[mod] = ModalityEncoder(
                input_dim=input_dim,
                output_dim=modality_latent_dim,
                hidden_dim=max(input_dim * 2, 128),
            )

        n_latent = len(self.modalities) * modality_latent_dim
        self.fusion = nn.Sequential(
            nn.Linear(n_latent, fusion_hidden),
            nn.LayerNorm(fusion_hidden),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_hidden, engagement_dim),
            nn.LayerNorm(engagement_dim),
        )

        self._modality_mask: Optional[torch.Tensor] = None

    def set_modality_mask(self, mask: Dict[str, bool]):
        self._modality_mask = mask

    def forward(
        self,
        eeg: Optional[torch.Tensor] = None,
        gsr: Optional[torch.Tensor] = None,
        pupil: Optional[torch.Tensor] = None,
        fixation: Optional[torch.Tensor] = None,
        video: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        inputs = {
            "eeg": eeg,
            "gsr": gsr,
            "pupil": pupil,
            "fixation": fixation,
            "video": video,
        }

        latents = []
        batch_size = None

        for mod in self.modalities:
            x = inputs.get(mod)
            if x is None:
                continue
            if batch_size is None:
                batch_size = x.shape[0]
            if x.dim() == 1:
                x = x.unsqueeze(0)

            encoded = self.encoders[mod](x)
            latents.append(encoded)

        if len(latents) == 0:
            raise ValueError("No modalities provided")

        latent = torch.cat(latents, dim=-1)

        if latent.size(-1) != self.fusion[0].in_features:
            padded = torch.zeros(latent.shape[0], self.fusion[0].in_features, device=latent.device)
            padded[:, :latent.size(-1)] = latent
            latent = padded

        engagement = self.fusion(latent)
        engagement = F.normalize(engagement, p=2, dim=-1)
        return engagement

    def forward_masked(
        self, inputs: Dict[str, Optional[torch.Tensor]]
    ) -> torch.Tensor:
        return self.forward(**inputs)


class EngagementContrastiveLoss(nn.Module):
    """Contrastive loss for engagement vector training.

    Positive pairs (same content, same viewer) should be close in
    embedding space; negative pairs (different content) should be far.
    """

    def __init__(self, temperature: float = 0.1):
        super().__init__()
        self.temperature = temperature

    def forward(self, z: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        z = F.normalize(z, p=2, dim=-1)
        similarity = torch.mm(z, z.T) / self.temperature
        mask = labels.unsqueeze(0) == labels.unsqueeze(1)
        mask.fill_diagonal_(False)

        exp_sim = torch.exp(similarity)
        exp_sim.masked_fill_(torch.eye(len(z), device=z.device, dtype=bool), 0)

        pos = exp_sim[mask]
        neg = exp_sim[~mask & ~torch.eye(len(z), device=z.device, dtype=bool)]

        if pos.numel() == 0 or neg.numel() == 0:
            return torch.tensor(0.0, device=z.device)

        loss = -torch.log(pos.sum() / neg.sum() + 1e-10)
        return loss


class EngagementVectorPipeline:
    """Full inference pipeline: raw signals → 128-dim engagement vector.

    Sequence:
    1. EEG: preprocess → epoch → EEGNet feature extractor
    2. GSR: preprocess → extract features
    3. Pupil: preprocess → extract features
    4. Fixation: preprocess → extract features
    5. Video: extract features (from TimelineAligner)
    6. Fusion: MultiModalFusion → 128-dim engagement vector

    Outputs per-second engagement vectors aligned to the video timeline.
    """

    def __init__(
        self,
        eeg_preprocessor: Optional[Any] = None,
        gsr_preprocessor: Optional[Any] = None,
        pupil_preprocessor: Optional[Any] = None,
        fixation_preprocessor: Optional[Any] = None,
        eeg_feature_extractor: Optional[nn.Module] = None,
        fusion_model: Optional[MultiModalFusion] = None,
        device: Optional[torch.device] = None,
        sr: int = 256,
    ):
        from .signal_processing import EEGPreprocessor, GSRPreprocessor, PupilPreprocessor, FixationPreprocessor

        self.sr = sr
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.eeg_preprocessor = eeg_preprocessor or EEGPreprocessor(sr=sr)
        self.gsr_preprocessor = gsr_preprocessor or GSRPreprocessor(sr=sr)
        self.pupil_preprocessor = pupil_preprocessor or PupilPreprocessor(sr=sr)
        self.fixation_preprocessor = fixation_preprocessor or FixationPreprocessor(sr=sr)

        self.eeg_feature_extractor = eeg_feature_extractor
        self.fusion_model = fusion_model

        self._fusion_ready = fusion_model is not None and eeg_feature_extractor is not None

    def process_epoch(
        self,
        eeg_epoch: np.ndarray,
        gsr_epoch: Optional[np.ndarray] = None,
        pupil_epoch: Optional[np.ndarray] = None,
        gaze_x_epoch: Optional[np.ndarray] = None,
        gaze_y_epoch: Optional[np.ndarray] = None,
        video_features: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        if not self._fusion_ready:
            raise RuntimeError(
                "Fusion not ready. Set eeg_feature_extractor and fusion_model."
            )
        batch_dim = eeg_epoch.ndim == 3

        if not batch_dim:
            eeg_epoch = eeg_epoch[np.newaxis, :, :]
        if gsr_epoch is not None and gsr_epoch.ndim == 1:
            gsr_epoch = gsr_epoch[np.newaxis, :]
        if pupil_epoch is not None and pupil_epoch.ndim == 1:
            pupil_epoch = pupil_epoch[np.newaxis, :]
        if gaze_x_epoch is not None and gaze_x_epoch.ndim == 1:
            gaze_x_epoch = gaze_x_epoch[np.newaxis, :]
            gaze_y_epoch = gaze_y_epoch[np.newaxis, :] if gaze_y_epoch is not None else None
        if video_features is not None and video_features.ndim == 1:
            video_features = video_features[np.newaxis, :]

        eeg_tensor = torch.from_numpy(eeg_epoch).unsqueeze(1).float().to(self.device)

        with torch.no_grad():
            eeg_feats = self.eeg_feature_extractor(eeg_tensor)

        inputs: Dict[str, Optional[torch.Tensor]] = {"eeg": eeg_feats}

        if gsr_epoch is not None:
            if gsr_epoch.shape[1] < 8:
                from .signal_processing import GSRPreprocessor
                temp_pp = GSRPreprocessor(sr=self.sr)
                gsr_feats = temp_pp.extract_features(gsr_epoch[0])
                gsr_tensor = torch.from_numpy(gsr_feats).float().to(self.device)
                gsr_tensor = gsr_tensor.view(1, -1)
            else:
                gsr_tensor = torch.from_numpy(gsr_epoch).float().to(self.device)
            inputs["gsr"] = gsr_tensor
        else:
            inputs["gsr"] = torch.zeros(1, 8, device=self.device)

        if pupil_epoch is not None:
            if pupil_epoch.shape[1] < 8:
                from .signal_processing import PupilPreprocessor
                temp_pp = PupilPreprocessor(sr=self.sr)
                pupil_feats = temp_pp.extract_features(pupil_epoch[0])
                pupil_tensor = torch.from_numpy(pupil_feats).float().to(self.device)
                pupil_tensor = pupil_tensor.view(1, -1)
            else:
                pupil_tensor = torch.from_numpy(pupil_epoch).float().to(self.device)
            inputs["pupil"] = pupil_tensor
        else:
            inputs["pupil"] = torch.zeros(1, 8, device=self.device)

        if gaze_x_epoch is not None and gaze_y_epoch is not None:
            from .signal_processing import FixationPreprocessor
            temp_fp = FixationPreprocessor(sr=self.sr)
            fix_feats = temp_fp.extract_features(gaze_x_epoch[0], gaze_y_epoch[0])
            fix_tensor = torch.from_numpy(fix_feats).float().to(self.device)
            fix_tensor = fix_tensor.view(1, -1)
            inputs["fixation"] = fix_tensor
        else:
            inputs["fixation"] = torch.zeros(1, 16, device=self.device)

        if video_features is not None:
            vid_tensor = torch.from_numpy(video_features).float().to(self.device)
            inputs["video"] = vid_tensor
        else:
            inputs["video"] = torch.zeros(1, 11, device=self.device)

        engagement = self.fusion_model.forward_masked(inputs)

        return engagement.cpu().numpy()

    def process_video(
        self,
        eeg_data: np.ndarray,
        gsr_data: Optional[np.ndarray] = None,
        pupil_data: Optional[np.ndarray] = None,
        gaze_x: Optional[np.ndarray] = None,
        gaze_y: Optional[np.ndarray] = None,
        video_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        eeg_clean = self.eeg_preprocessor.preprocess(eeg_data)
        epochs, timestamps = self.eeg_preprocessor.epoch(eeg_clean)
        n_epochs = len(epochs)

        if gsr_data is not None:
            gsr_feats = self.gsr_preprocessor.extract_features(gsr_data)
        else:
            gsr_feats = np.zeros((n_epochs, 8))

        if pupil_data is not None:
            pupil_feats = self.pupil_preprocessor.extract_features(pupil_data)
        else:
            pupil_feats = np.zeros((n_epochs, 8))

        if gaze_x is not None and gaze_y is not None:
            fix_feats = self.fixation_preprocessor.extract_features(gaze_x, gaze_y)
        else:
            fix_feats = np.zeros((n_epochs, 16))

        video_feats = np.zeros((n_epochs, 11))
        if video_path is not None:
            try:
                from .video_timeline import TimelineAligner
                aligner = TimelineAligner()
                features, _ = aligner.extract_features(video_path)
                min_len = min(n_epochs, features.shape[0])
                video_feats[:min_len] = features[:min_len]
            except Exception as e:
                logger.warning(f"Video feature extraction failed: {e}")

        engagement_vectors = np.zeros((n_epochs, self.fusion_model.engagement_dim), dtype=np.float32)

        for i in range(n_epochs):
            ev = self.process_epoch(
                eeg_epoch=epochs[i],
                gsr_epoch=gsr_feats[i] if gsr_data is not None else None,
                pupil_epoch=pupil_feats[i] if pupil_data is not None else None,
                gaze_x_epoch=fix_feats[i] if gaze_x is not None else None,
                gaze_y_epoch=fix_feats[i] if gaze_y is not None else None,
                video_features=video_feats[i],
            )
            engagement_vectors[i] = ev[0]

        return {
            "engagement_vectors": engagement_vectors,
            "timestamps": timestamps,
            "eeg_labels": self._default_labels(),
            "n_epochs": n_epochs,
            "engagement_dim": self.fusion_model.engagement_dim,
        }

    def _default_labels(self) -> Dict[str, np.ndarray]:
        return {
            dim: np.zeros(0) for dim in ["attention", "arousal", "valence",
                                          "engagement", "cognitive_load", "emotional_disengagement"]
        }


def build_engagement_vector_pipeline(
    n_channels: int = 64,
    n_times: int = 256,
    sr: int = 256,
    eegnet_variant: str = "8,2",
    device: Optional[torch.device] = None,
) -> EngagementVectorPipeline:
    from .eegnet import EEGNetMultiTask, EEGNetFeatureExtractor, build_eegnet_config

    dev = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")

    cfg = build_eegnet_config(eegnet_variant, n_channels, n_times)
    backbone = EEGNetMultiTask(
        n_channels=n_channels,
        n_times=n_times,
        F1=cfg["F1"], D=cfg["D"], F2=cfg["F2"],
        dropout_rate=0.5,
        n_regression=6,
        hidden_dim=128,
    ).to(dev)

    feature_extractor = EEGNetFeatureExtractor(backbone).to(dev)
    feature_extractor.eval()

    fusion = MultiModalFusion(
        modalities=["eeg", "gsr", "pupil", "fixation", "video"],
        engagement_dim=128,
        modality_latent_dim=64,
    ).to(dev)
    fusion.eval()

    pipeline = EngagementVectorPipeline(
        eeg_feature_extractor=feature_extractor,
        fusion_model=fusion,
        device=dev,
        sr=sr,
    )

    logger.info(f"Engagement vector pipeline built (variant={eegnet_variant}, device={dev})")
    logger.info(f"  EEGNet params: {sum(p.numel() for p in backbone.parameters()):,}")
    logger.info(f"  Fusion params: {sum(p.numel() for p in fusion.parameters()):,}")
    return pipeline
