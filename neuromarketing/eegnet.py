import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, List, Dict, Tuple, Any
import logging
import math

logger = logging.getLogger(__name__)


class DepthwiseConv2d(nn.Module):
    """Depthwise convolution: one spatial filter per input channel.

    Applies a separate 2D convolution to each input channel,
    producing D * C_out output channels where C_out = in_channels.
    """

    def __init__(self, in_channels: int, depth_multiplier: int, kernel_size: Tuple[int, int],
                 padding: Tuple[int, int] = (0, 0), max_norm: float = 1.0):
        super().__init__()
        self.max_norm = max_norm
        self.depthwise = nn.Conv2d(
            in_channels, in_channels * depth_multiplier,
            kernel_size=kernel_size, padding=padding,
            groups=in_channels, bias=False,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.max_norm > 0:
            with torch.no_grad():
                for param in self.depthwise.parameters():
                    norm = param.norm(2.0)
                    if norm > self.max_norm:
                        param.mul_(self.max_norm / norm)
        return self.depthwise(x)


class SeparableConv2d(nn.Module):
    """Separable convolution: depthwise → pointwise.

    Reduces parameters vs standard Conv2d by factor of ~kernel_size.
    """

    def __init__(self, in_channels: int, out_channels: int, kernel_size: Tuple[int, int],
                 padding: Tuple[int, int] = (0, 0), max_norm: float = 1.0):
        super().__init__()
        self.max_norm = max_norm
        self.depthwise = nn.Conv2d(
            in_channels, in_channels, kernel_size=kernel_size,
            padding=padding, groups=in_channels, bias=False,
        )
        self.pointwise = nn.Conv2d(
            in_channels, out_channels, kernel_size=1, bias=False,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.max_norm > 0:
            with torch.no_grad():
                for param in self.depthwise.parameters():
                    norm = param.norm(2.0)
                    if norm > self.max_norm:
                        param.mul_(self.max_norm / norm)
                for param in self.pointwise.parameters():
                    norm = param.norm(2.0)
                    if norm > self.max_norm:
                        param.mul_(self.max_norm / norm)
        x = self.depthwise(x)
        x = self.pointwise(x)
        return x


class EEGNet(nn.Module):
    """EEGNet: A Compact Convolutional Neural Network for EEG-based BCIs.

    Based on Lawhern et al. 2018 (https://arxiv.org/abs/1611.08024).

    Configurations (F1, D, F2, kernel_1, kernel_2):
    - EEGNet-4,2:  (4, 2, 8,  64, 16)  — default, good for small datasets
    - EEGNet-8,2:  (8, 2, 16, 64, 16)
    - EEGNet-16,2: (16, 2, 32, 64, 16)

    Input shape:  (batch, 1, n_channels, n_times)
    Output shape: (batch, n_classes) for classification
                  (batch, feature_dim) when return_features=True
    """

    def __init__(
        self,
        n_channels: int = 64,
        n_times: int = 256,
        F1: int = 8,
        D: int = 2,
        F2: int = 16,
        kernel_1: int = 64,
        kernel_2: int = 16,
        dropout_rate: float = 0.5,
        n_classes: int = 3,
        return_features: bool = False,
    ):
        super().__init__()
        self.n_channels = n_channels
        self.n_times = n_times
        self.F1 = F1
        self.D = D
        self.F2 = F2
        self.kernel_1 = kernel_1
        self.kernel_2 = kernel_2
        self.dropout_rate = dropout_rate
        self.n_classes = n_classes
        self.return_features = return_features

        padding_1 = self._same_padding(n_times, kernel_1)
        self._padding_1 = (0, padding_1)

        padding_2 = self._same_padding(n_times, kernel_2)
        self._padding_2 = (0, padding_2)

        self.block1 = nn.Sequential()
        self.block1.add_module("conv_temporal", nn.Conv2d(
            1, F1, (1, kernel_1), padding=self._padding_1, bias=False,
        ))
        self.block1.add_module("bn_temporal", nn.BatchNorm2d(F1, momentum=0.01, eps=1e-3))

        self.block1.add_module("conv_depthwise", DepthwiseConv2d(
            F1, D, (n_channels, 1), padding=(0, 0), max_norm=1.0,
        ))
        self.block1.add_module("bn_depthwise", nn.BatchNorm2d(F1 * D, momentum=0.01, eps=1e-3))
        self.block1.add_module("elu_depthwise", nn.ELU())
        self.block1.add_module("avgpool_depthwise", nn.AvgPool2d((1, 4), stride=(1, 4)))
        self.block1.add_module("dropout_depthwise", nn.Dropout2d(dropout_rate))

        self.block2 = nn.Sequential()
        self.block2.add_module("conv_separable", SeparableConv2d(
            F1 * D, F2, (1, kernel_2), padding=self._padding_2, max_norm=1.0,
        ))
        self.block2.add_module("bn_separable", nn.BatchNorm2d(F2, momentum=0.01, eps=1e-3))
        self.block2.add_module("elu_separable", nn.ELU())
        self.block2.add_module("avgpool_separable", nn.AvgPool2d((1, 8), stride=(1, 8)))
        self.block2.add_module("dropout_separable", nn.Dropout2d(dropout_rate))

        self._feature_dim = None
        self._classifier = None

    def _same_padding(self, n_times: int, kernel_size: int) -> int:
        return (kernel_size - 1) // 2

    def _compute_feature_dim(self, x: torch.Tensor) -> int:
        with torch.no_grad():
            features = self._forward_features(x)
            return features.shape[1] * features.shape[2] * features.shape[3]

    def _forward_features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.block1(x)
        x = self.block2(x)
        return x

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self._forward_features(x)

        if self.return_features:
            return x

        if self._classifier is None:
            self._feature_dim = x.shape[1] * x.shape[2] * x.shape[3]
            self._classifier = nn.Linear(self._feature_dim, self.n_classes).to(x.device)
            self._classifier.weight.data.normal_(0, 0.01)
            self._classifier.bias.data.zero_()

        x = x.view(x.size(0), -1)
        x = self._classifier(x)
        if self.n_classes == 1:
            x = torch.sigmoid(x)
        else:
            x = F.log_softmax(x, dim=1)
        return x


class EEGNetMultiTask(nn.Module):
    """EEGNet with multi-task output heads for emotion-attention prediction.

    Predicts attention, valence, and arousal simultaneously from EEG.
    Each dimension has its own regression head (+/- classification aux loss).
    """

    def __init__(
        self,
        n_channels: int = 64,
        n_times: int = 256,
        F1: int = 8,
        D: int = 2,
        F2: int = 16,
        kernel_1: int = 64,
        kernel_2: int = 16,
        dropout_rate: float = 0.5,
        n_regression: int = 6,
        hidden_dim: int = 128,
    ):
        super().__init__()
        self.n_regression = n_regression
        self.hidden_dim = hidden_dim

        self.backbone = EEGNet(
            n_channels=n_channels,
            n_times=n_times,
            F1=F1, D=D, F2=F2,
            kernel_1=kernel_1, kernel_2=kernel_2,
            dropout_rate=dropout_rate,
            n_classes=1,
            return_features=True,
        )

        dummy = torch.zeros(1, 1, n_channels, n_times)
        with torch.no_grad():
            feat = self.backbone._forward_features(dummy)
            backbone_dim = feat.shape[1] * feat.shape[2] * feat.shape[3]

        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc_proj = nn.Linear(backbone_dim, hidden_dim)
        self.bn_proj = nn.BatchNorm1d(hidden_dim)
        self.regression_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim // 2),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(hidden_dim // 2, 1),
                nn.Sigmoid(),
            )
            for _ in range(n_regression)
        ])

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone._forward_features(x)
        pooled = self.global_pool(features)
        pooled = pooled.view(pooled.size(0), -1)
        shared = self.fc_proj(pooled)
        shared = self.bn_proj(shared)
        shared = F.relu(shared)

        outputs = []
        for head in self.regression_heads:
            outputs.append(head(shared))
        regression_out = torch.cat(outputs, dim=1)

        return regression_out, shared


class EEGNetFeatureExtractor(nn.Module):
    """EEGNet pretrained feature extractor.

    Wraps a trained EEGNetMultiTask and returns the shared representation
    (hidden_dim vector) for use in multi-modal fusion.
    """

    def __init__(self, backbone: EEGNetMultiTask):
        super().__init__()
        self.backbone = backbone
        for param in self.backbone.parameters():
            param.requires_grad = False
        self._feature_dim = backbone.hidden_dim

    @property
    def feature_dim(self) -> int:
        return self._feature_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, shared = self.backbone(x)
        return shared


class EEGClassifier(nn.Module):
    """Lightweight wrapper: EEGNet → per-second emotion labels.

    End-to-end replacement for the sklearn EmotionClassifier.
    Outputs [attention, arousal, valence, engagement, cognitive_load, disengagement].
    """

    EMOTION_DIMS = ["attention", "arousal", "valence", "engagement", "cognitive_load", "emotional_disengagement"]

    def __init__(
        self,
        n_channels: int = 64,
        n_times: int = 256,
        sr: int = 256,
        F1: int = 8,
        D: int = 2,
        F2: int = 16,
        dropout_rate: float = 0.5,
        hidden_dim: int = 128,
    ):
        super().__init__()
        self.sr = sr
        self.n_channels = n_channels
        self.n_times = n_times
        self.hidden_dim = hidden_dim

        self.model = EEGNetMultiTask(
            n_channels=n_channels,
            n_times=n_times,
            F1=F1, D=D, F2=F2,
            dropout_rate=dropout_rate,
            n_regression=len(self.EMOTION_DIMS),
            hidden_dim=hidden_dim,
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.model(x)

    def predict_emotions(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        regression_out, _ = self.model(x)
        return {
            dim: regression_out[:, i]
            for i, dim in enumerate(self.EMOTION_DIMS)
        }

    @property
    def device(self) -> torch.device:
        return next(self.parameters()).device


def count_eegnet_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def build_eegnet_config(
    variant: str = "8,2",
    n_channels: int = 64,
    n_times: int = 256,
    n_classes: int = 6,
) -> Dict[str, Any]:
    configs = {
        "4,2":  {"F1": 4,  "D": 2, "F2": 8,  "kernel_1": 64, "kernel_2": 16},
        "8,2":  {"F1": 8,  "D": 2, "F2": 16, "kernel_1": 64, "kernel_2": 16},
        "16,2": {"F1": 16, "D": 2, "F2": 32, "kernel_1": 64, "kernel_2": 16},
        "4,4":  {"F1": 4,  "D": 4, "F2": 16, "kernel_1": 32, "kernel_2": 8},
        "8,4":  {"F1": 8,  "D": 4, "F2": 32, "kernel_1": 32, "kernel_2": 8},
    }
    cfg = configs.get(variant, configs["8,2"]).copy()
    cfg["n_channels"] = n_channels
    cfg["n_times"] = n_times
    cfg["n_classes"] = n_classes
    return cfg
