# NeuralPulse Engine

**Brain-validated ad optimization using simulated fMRI responses via TRIBE v2.**

NeuralPulse Engine is a neuromarketing SaaS platform that simulates brain activity to predict how audiences will respond to advertising content. It analyzes video, audio, and text ads across three neural dimensions — **Attention**, **Dopamine/Reward**, and **Memory Encoding** — delivering actionable optimization recommendations, A/B testing, neural copywriting analysis, AI-powered thumbnail generation, and interactive 3D brain visualizations.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Core Engine](#core-engine)
- [Database](#database)
- [Frontend](#frontend)
- [Token System & Billing](#token-system--billing)
- [Development](#development)
- [License](#license)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Static)                   │
│  HTML · CSS · Chart.js · Three.js · Dark Theme       │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / REST
┌──────────────────────▼──────────────────────────────┐
│              FastAPI Backend (Python)                 │
│  auth · analysis · billing · history · thumbnails    │
└──────┬──────────────────────────────────┬───────────┘
       │                                  │
┌──────▼─────────┐            ┌──────────▼──────────┐
│  neuromarketing │            │  SQLite / PostgreSQL │
│  Core Engine    │            │  SQLAlchemy ORM      │
│  TRIBE v2       │            │  Users · History ·   │
│  Simulation     │            │  Tokens · Thumbnails │
└─────────────────┘            └─────────────────────┘
```

The platform operates in three tiers:

1. **Frontend** — Pure HTML/CSS/JS dashboard with Chart.js visualizations and Three.js 3D brain renderer.
2. **API Layer** — FastAPI routers handling authentication, analysis, billing, history, and thumbnail generation.
3. **Core Engine** — The `neuromarketing` Python package that simulates brain responses, computes neural scores, generates recommendations, and produces 3D brain visualizations.

---

## Features

### Neural Ad Analysis
- **Video Analysis** — Upload MP4, MOV, AVI, WebM, MKV. Analyzes frames for visual attention, reward response, and memory encoding. Detects scene breaks, keyframes, attention dropoffs, and engagement curves.
- **Audio Analysis** — Upload MP3, WAV, OGG, M4A, FLAC. Evaluates auditory attention, emotional arousal, and memory consolidation from audio features.
- **Text Analysis** — Paste or upload TXT, MD, HTML. Word-level and sentence-level neural scoring with vocabulary impact analysis.

### A/B Testing
- Compare 2+ video, audio, or text variants
- Per-dimension significance testing (t-test)
- Automatic winner selection with improvement metrics

### Neural Copywriting
- Analyze original copy against up to N variants
- 9 framing types: gain, loss, urgency, social proof, authority, reciprocity, curiosity, pain point, aspirational
- Per-dimension comparison and winning variant detection

### AI Thumbnail Generation
- 5 supported models: FLUX.1-dev, Stable Diffusion 3.5 Large, Qwen-Image, Qwen-Image-Edit, Cosmos3-Nano
- Local diffusers inference or Hugging Face Inference API
- Neural engagement forecasting per thumbnail
- Generation history with JSON/HTML export

### 3D Brain Visualization
- Interactive brain renderings using nilearn + fsaverage5 surface mesh
- Three.js 3D brain explorer with ROI atlas highlighting
- Attention, dopamine, and memory mode overlays
- MNI coordinate-space ROI mapping

### Virality Scoring
- Composite virality score from 5 factors: Face Engagement, Emotional Arousal, Auditory Hook, Visual Salience, Narrative Immersion
- Optimized format/length/audience recommendations

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI 0.111.0 |
| ASGI Server | Uvicorn 0.29.0 |
| ORM | SQLAlchemy 2.0.30 (async) |
| Auth | python-jose (JWT) + bcrypt |
| Payments | Stripe 8.8.0 |
| ML/AI | PyTorch 2.1+, scikit-learn, diffusers 0.30+, transformers 4.44+ |
| Signal Processing | NumPy, SciPy |
| Brain Visualization | nilearn, nibabel |
| Image Generation | diffusers (FLUX.1-dev, Cosmos3), HF Inference API (SD3.5, Qwen) |

### Frontend
| Component | Technology |
|-----------|-----------|
| Framework | None (vanilla JS) |
| Charts | Chart.js |
| 3D Rendering | Three.js |
| Styling | Custom CSS, dark sci-fi theme with glassmorphism |

---

## Getting Started

### Prerequisites
- Python 3.14+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/Joeltabe/Neuralpulse-engine.git
cd Neuralpulse-engine

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and adjust values:

```bash
cp .env.example .env
```

See [Configuration](#configuration) for all available settings.

### Run the Server

```bash
python run.py
```

The server starts at `http://0.0.0.0:8000` by default with hot-reload enabled.

```
=======================================
 NeuralPulse Engine v1.0
 Neuromarketing SaaS — TRIBE v2 Powered
=======================================
 API:         http://0.0.0.0:8000
 Docs:        http://0.0.0.0:8000/docs
 Landing:     http://0.0.0.0:8000/
 Dashboard:   http://0.0.0.0:8000/app/dashboard.html
=======================================
```

---

## Configuration

All configuration is managed through environment variables (`.env` file).

### Core
| Variable | Default | Description |
|----------|---------|-------------|
| `USE_REAL_TRIBE` | `false` | Use real TRIBE v2 model (local/API) vs simulation |
| `TRIBE_CACHE_DIR` | `./cache` | Model cache directory |
| `TRIBE_MODEL_NAME` | `facebook/tribev2` | Hugging Face model name |
| `DEVICE` | `cpu` | Torch device (`cpu` or `cuda`) |
| `UPLOAD_DIR` | `./uploads` | Temporary upload directory |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `RELOAD` | `true` | Enable hot reload |

### Database
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(Neon PostgreSQL)* | PostgreSQL connection string |
| `USE_SQLITE` | `false` | Force SQLite instead of PostgreSQL |

### Authentication
| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | `neuralpulse-dev-secret-...` | JWT signing secret (change in production!) |
| `TOKEN_EXPIRE_MINUTES` | `1440` | Token expiration (24 hours) |

### Stripe
| Variable | Default | Description |
|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | *(empty)* | Stripe API secret key |
| `STRIPE_WEBHOOK_SECRET` | *(empty)* | Stripe webhook signing secret |
| `FRONTEND_URL` | `http://localhost:8000` | Frontend URL for Stripe redirects |

### TRIBE v2 API
| Variable | Default | Description |
|----------|---------|-------------|
| `TRIBE_API_URL` | `https://thesilenthowler029-tribe-v2-api.hf.space` | Remote TRIBE v2 API endpoint |

---

## API Reference

The full interactive API documentation is available at `/docs` when the server is running.

### Authentication Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Register new user (gets 100 free tokens) |
| POST | `/auth/login` | Login with email/password |
| POST | `/auth/demo-login` | Instant demo login (500 tokens) |
| GET | `/auth/me` | Get current user profile |

### Analysis Endpoints

All analysis endpoints require JWT authentication and deduct tokens.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/analyze/video` | Analyze video file (50 tokens) |
| POST | `/analyze/audio` | Analyze audio file (30 tokens) |
| POST | `/analyze/text` | Analyze text content (10 tokens) |
| POST | `/analyze/upload-text` | Analyze text file (10 tokens) |
| POST | `/analyze/ab-test/video` | A/B test video variants (25 tokens) |
| POST | `/analyze/ab-test/audio` | A/B test audio variants (25 tokens) |
| POST | `/analyze/ab-test/text` | A/B test text variants (25 tokens) |

### Copywriting Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/copy/analyze` | Neural copywriting analysis (10 tokens) |

### Thumbnail Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/thumbnail/generate` | Generate thumbnails (15 tokens) |
| GET | `/thumbnail/models` | List available models |
| GET | `/thumbnail/history` | List generation history |
| GET | `/thumbnail/history/{id}` | Get history detail |
| DELETE | `/thumbnail/history/{id}` | Delete history entry |
| GET | `/thumbnail/history/{id}/export` | Export history (JSON/HTML) |

### History Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/history/analyses` | List analysis history |
| GET | `/history/stats` | Get usage statistics |

### Billing Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/billing/packages` | List token packages |
| GET | `/billing/balance` | Get token balance |
| POST | `/billing/purchase` | Purchase token package |
| POST | `/billing/deduct` | Deduct tokens (internal) |
| GET | `/billing/history` | Transaction history |
| POST | `/billing/stripe-webhook` | Stripe webhook handler |

### Utility Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/info` | Service info and feature flags |
| POST | `/api/predict-brain` | Legacy brain prediction (file upload) |

### Analysis Response Schema

```json
{
  "success": true,
  "data": {
    "id": "a1b2c3d4",
    "filename": "ad.mp4",
    "media_type": "video",
    "duration_sec": 30.0,
    "brain_scores": {
      "attention": {
        "overall": 0.72,
        "label": "High Attention",
        "temporal_scores": [...],
        "peak_moments": [...],
        "dropoff_moments": [...],
        "roi_breakdown": {"V1": 0.8, "V2": 0.75, ...}
      },
      "dopamine": {
        "overall": 0.65,
        "label": "Moderate Dopamine Response",
        "temporal_scores": [...],
        "reward_peaks": [...],
        "roi_breakdown": {"VS": 0.7, "NAcc": 0.6, ...}
      },
      "memory": {
        "overall": 0.58,
        "label": "Moderate Memory Encoding",
        "temporal_scores": [...],
        "encoding_strength": [...],
        "consolidation_potential": 0.62,
        "roi_breakdown": {"HIP": 0.6, "PHC": 0.55, ...}
      }
    },
    "engagement_curve": [...],
    "timestamp_axis": [...],
    "recommendations": [...],
    "summary": "Attention: High Attention | ...",
    "overall_grade": "B+",
    "scene_breaks": [4.5, 9.2, ...],
    "keyframes": [...],
    "brain_viz_urls": {
      "attention": "/brain_viz/a1b2c3d4_attention.html",
      "dopamine": "/brain_viz/a1b2c3d4_dopamine.html",
      "memory": "/brain_viz/a1b2c3d4_memory.html"
    },
    "tokens_used": 50,
    "token_balance_after": 450
  }
}
```

---

## Core Engine

The `neuromarketing/` package is the heart of the platform.

### TRIBE v2 Adapter (`tribe_adapter.py`)

`TribeAdapter` abstracts Facebook's TRIBE v2 model. It supports three operational modes:

| Mode | Trigger | Description |
|------|---------|-------------|
| **Local PyTorch** | `USE_REAL_TRIBE=true` + `tribev2` installed | Runs TRIBE v2 locally via PyTorch |
| **Remote API** | `USE_REAL_TRIBE=true` + no local model | Calls HF Space REST API |
| **Simulated** | `USE_REAL_TRIBE=false` (default) | Enhanced simulation using sinusoidal basis functions, hemodynamic lag, and ROI-specific signal maps |

The simulation generates realistic 20,484-vertex cortical activation patterns at 1Hz temporal resolution. It models:

- **Video**: Motion intensity, scene complexity, and visual salience-based activation
- **Audio**: Amplitude, speech confidence, and spectral energy-based patterns
- **Text**: Word length, novelty, emotional content, and part-of-speech signals

### Neuromarketing Analyzer (`analyzer.py`)

`NeuromarketingAnalyzer` orchestrates the full analysis pipeline:

1. **Feature Extraction** — TRIBE v2 predictions + ROI scoring
2. **Dimension Scoring** — Computes Attention (6 ROIs), Dopamine (5 ROIs), Memory (7 ROIs)
3. **Engagement Curve** — Weighted combination: 40% attention + 35% dopamine + 25% memory
4. **Temporal Analysis** — Peak detection, dropoff identification, scene break detection
5. **Recommendations** — Severity-ranked suggestions (critical/moderate/suggestion)
6. **Grading** — A+ through F based on weighted composite score

### ROI Mapping

| Dimension | ROIs | Function |
|-----------|------|----------|
| **Attention** | V1, V2, V3, MT, IPS, FEF | Visual cortex, parietal, frontal eye fields |
| **Dopamine** | VS, NAcc, vmPFC, SN, VTA | Reward, pleasure, motivation |
| **Memory** | HIP, PHC, PRC, ERC, ANG, PCC, DLPFC | Encoding, consolidation, recall |

### Brain Visualization (`brain_viz.py`)

Generates interactive 3D brain HTML using nilearn's surface projection. ROIs are mapped to MNI152 coordinates and rendered as Gaussian blobs on the fsaverage5 cortical surface. Three visualization modes available:

- **Attention mode** — Highlights visual cortex, parietal, and FEF regions
- **Dopamine mode** — Highlights striatum, vmPFC, SN, VTA
- **Memory mode** — Highlights hippocampus, MTL, cingulate, DLPFC

### Emotion Classifier (`emotion_classifier.py`)

Six-dimension emotion classifier (RandomForest/GradientBoosting ensemble):

| Dimension | Description |
|-----------|-------------|
| Attention | Focused vs distracted |
| Arousal | Calm vs excited |
| Valence | Negative vs positive |
| Engagement | Bored vs immersed |
| Cognitive Load | Easy vs demanding |
| Emotional Disengagement | Connected vs detached |

### Signal Processing (`signal_processing.py`)

Preprocessing pipelines for neuromarketing sensor data:

- **EEG** — Bandpass filtering, notch filtering, ICA artifact removal, epoch extraction
- **GSR** — Lowpass filtering, deconvolution, tonic/phasic separation
- **Pupillometry** — Blink removal, interpolation, baseline correction
- **Eye Tracking** — Fixation detection, saccade detection, velocity filtering

### EEGNet (`eegnet.py`)

PyTorch implementation of EEGNet (Lawhern et al. 2018) with multitask regression extension:
- `EEGNet` — Standard 4-layer convolutional architecture
- `EEGNetMultiTask` — 6 regression heads for all emotion dimensions
- `EEGClassifier` — Convenience wrapper with training/inference pipeline

### Multimodal Fusion (`multimodal_fusion.py`)

Fuses 5 modalities into a 128-dimensional engagement vector:

| Modality | Input Dim | Description |
|----------|-----------|-------------|
| EEG | 128 | 32-channel × 4 frequency bands |
| GSR | 8 | Skin conductance response features |
| Pupillometry | 8 | Pupil dilation features |
| Eye Tracking | 16 | Fixation/saccade features |
| Video Features | 11 | Scene-level visual features |

---

## Database

The system uses SQLAlchemy async ORM with automatic fallback from Neon PostgreSQL to SQLite.

### Models

| Table | Purpose |
|-------|---------|
| `users` | User accounts, roles, token balances |
| `token_packages` | Stripe token pricing tiers |
| `token_transactions` | Purchase and usage ledger |
| `analysis_history` | Full analysis results (JSON) |
| `thumbnail_history` | Generated thumbnail metadata |

### Token Costs

| Operation | Tokens |
|-----------|--------|
| Video Analysis | 50 |
| Audio Analysis | 30 |
| Text Analysis | 10 |
| Copy Analysis | 10 |
| A/B Test | 25 |
| Thumbnail Generation | 15 |

### Packages

| Package | Tokens | Price |
|---------|--------|-------|
| Starter | 100 | $9.99 |
| Pro | 500 | $39.99 |
| Agency | 2500 | $149.99 |

---

## Frontend

The frontend is a single-page application built with vanilla HTML, CSS, and JavaScript.

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Marketing landing page |
| Login | `/app/login.html` | Login/register form |
| Dashboard | `/app/dashboard.html` | Main analysis dashboard |
| Pricing | `/app/pricing.html` | Token pricing plans |
| Brain Explorer | `/app/brain-explorer.html` | Interactive 3D brain viewer |
| Thumbnail Generator | `/app/thumbnail-generator.html` | AI thumbnail creation |
| Thumbnail History | `/app/thumbnail-history.html` | Past thumbnail generations |
| Terms | `/app/terms.html` | Terms of service |
| Privacy | `/app/privacy.html` | Privacy policy |

### Key Libraries

- **Chart.js** — Engagement curves, radar charts, doughnut charts, bar charts, gauge charts
- **Three.js** — 3D brain mesh rendering with ROI atlas highlighting
- **Custom CSS** — Dark sci-fi theme with glassmorphism, gradients, and animations

---

## Token System & Billing

### Flow
1. User registers → receives 100 free tokens
2. Each API call deducts tokens based on operation type
3. Users can purchase token packages via Stripe
4. Transaction history is maintained for auditing

### Stripe Integration
- Checkout Sessions for one-time purchases
- Webhook handler for fulfillment
- Supports automatic fallback when Stripe is not configured

---

## Development

### Project Structure

```
Neuralpulse-engine/
├── api/                    # FastAPI backend
│   ├── main.py             # App factory, lifespan, CORS, static serving
│   ├── auth.py             # JWT authentication
│   ├── billing.py          # Stripe token system
│   ├── database.py         # SQLAlchemy ORM + models
│   ├── dependencies.py     # Upload file handling
│   ├── image_generation.py # AI image generation
│   ├── schemas.py          # Pydantic request/response models
│   └── routers/
│       ├── analysis.py     # Analysis endpoints
│       ├── copywriting.py  # Copy analysis endpoints
│       ├── history.py      # History/stats endpoints
│       └── thumbnail.py    # Thumbnail generation endpoints
├── neuromarketing/         # Core ML engine (primary)
│   ├── analyzer.py         # NeuromarketingAnalyzer
│   ├── tribe_adapter.py    # TRIBE v2 adapter (local/API/simulated)
│   ├── emotion_classifier.py
│   ├── ab_testing.py       # A/B test engine
│   ├── copy_analyzer.py    # Neural copy analysis
│   ├── recommendations.py  # Actionable recommendations
│   ├── brain_viz.py        # 3D brain visualization
│   ├── video_timeline.py   # Video/audio feature extraction
│   ├── signal_processing.py
│   ├── eegnet.py           # EEGNet PyTorch model
│   ├── multimodal_fusion.py
│   ├── engagement_bridge.py
│   ├── train_classifier.py
│   ├── config.py           # Constants and thresholds
│   └── models.py           # Pydantic data models
├── netromarketing/         # Alternative/legacy engine
├── frontend/               # Static web frontend
│   ├── index.html
│   ├── css/style.css
│   ├── js/
│   │   ├── app.js
│   │   ├── charts.js
│   │   └── brain.js
│   └── ... (other pages)
├── models/                 # Pre-trained model files
├── scripts/                # Utility scripts
├── uploads/                # Temporary uploads
├── run.py                  # Server entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
└── opencode.json           # AI IDE configuration
```

### Training the Emotion Classifier

```bash
python -m neuromarketing.train_classifier
```

This trains a RandomForest/GradientBoosting ensemble on synthetic or real labeled data and saves to `models/emotion_classifier.pkl`.

### Generating Brain Mesh Data

```bash
python scripts/generate_brain_mesh.py
```

Generates the icosphere mesh for the Three.js brain explorer.

### Netromarketing Package

The `netromarketing/` package is an alternative engine version with additional analysis features:

- **Dopamine Triggers**: Identifies 11 trigger types (reward anticipation, novelty, social reward, etc.)
- **Visual Dropoffs**: Per-frame visual attention decline analysis
- **Directives**: P0/P1/P2 prioritized action directives
- **Frame Analysis**: Per-timestamp breakdown of all neural dimensions
- **Benchmark Comparisons**: Industry average percentile ranking for video/audio/text ads

This package is not wired into the API routers but serves as a reference for enhanced analysis capabilities.

---

## License

This project is open source. See the LICENSE file for details.

---

## Links

- **GitHub**: [https://github.com/Joeltabe/Neuralpulse-engine](https://github.com/Joeltabe/Neuralpulse-engine)
