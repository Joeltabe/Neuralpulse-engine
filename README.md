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
- Full 70,000 voxel prediction (20,484 cortical + 49,516 subcortical)
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
| Framework | Svelte 5 + SvelteKit 2 |
| Meta-framework | SvelteKit with Vite |
| Charts | Chart.js |
| 3D Rendering | Three.js |
| Animations | GSAP + ScrollTrigger |
| Styling | Tailwind CSS 3.4 with custom neural design tokens |
| Package Manager | npm |
| Language | TypeScript |
| Adapter | @sveltejs/adapter-vercel |

---

## Getting Started

### Prerequisites
- **Python 3.14+** and pip
- **Node.js 18+** and npm
- **Git LFS** (for model files: `git lfs install`)

### Installation

#### Backend Setup

```bash
# Clone the repository
git clone https://github.com/Joeltabe/Neuralpulse-engine.git
cd Neuralpulse-engine

# Create and activate a virtual environment (recommended)
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your preferred settings (see Configuration section)
```

#### Frontend Setup

```bash
# Install Node.js dependencies
npm install

# Start the SvelteKit dev server
npm run dev
```

### Run the Server

Start the backend API server:

```bash
python run.py
```

In a separate terminal, start the frontend dev server:

```bash
npm run dev
```

The API server starts at `http://0.0.0.0:8000` by default with hot-reload enabled, and the frontend dev server runs at `http://localhost:5173`.

```
=======================================
 NeuralPulse Engine v1.0
 Neuromarketing SaaS — TRIBE v2 Powered
=======================================
 API:         http://0.0.0.0:8000
 Docs:        http://0.0.0.0:8000/docs
 Landing:     http://localhost:5173
 Dashboard:   http://localhost:5173/dashboard
=======================================
```

### Frontend Production Build

```bash
npm run build
npm run preview    # preview the production build locally
```

The production frontend is built to the `build/` directory and deployed via the SvelteKit adapter (Vercel by default).

---

## Configuration

All configuration is managed through environment variables (`.env` file). The `.env.example` file contains the default values.

### Runtime
| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `RELOAD` | `true` | Enable hot reload on code changes |

### TRIBE v2 Engine
| Variable | Default | Description |
|----------|---------|-------------|
| `USE_REAL_TRIBE` | `false` | Use real TRIBE v2 model (`true`) vs simulation (`false`) |
| `TRIBE_CACHE_DIR` | `./cache` | Model cache directory |
| `TRIBE_MODEL_NAME` | `facebook/tribev2` | Hugging Face model name |
| `TRIBE_API_URL` | `https://thesilenthowler029-tribe-v2-api.hf.space` | Remote TRIBE v2 API endpoint |
| `DEVICE` | `cpu` | Torch device (`cpu` or `cuda`) |

### File Storage
| Variable | Default | Description |
|----------|---------|-------------|
| `UPLOAD_DIR` | `./uploads` | Temporary upload directory for analysis files |

### Database
| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | *(Neon PostgreSQL)* | PostgreSQL connection string (async with asyncpg) |
| `USE_SQLITE` | `false` | Force SQLite fallback instead of PostgreSQL |

The system uses SQLAlchemy async ORM with automatic fallback to SQLite if PostgreSQL is unreachable.

### Authentication
| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET` | *(auto-generated)* | JWT signing secret (change in production!) |
| `TOKEN_EXPIRE_MINUTES` | `1440` | JWT token expiration (24 hours) |

### Stripe (Token Purchases)
| Variable | Default | Description |
|----------|---------|-------------|
| `STRIPE_SECRET_KEY` | *(empty)* | Stripe API secret key (optional, token system falls back gracefully) |
| `STRIPE_WEBHOOK_SECRET` | *(empty)* | Stripe webhook signing secret |
| `FRONTEND_URL` | `http://localhost:8000` | Frontend URL for Stripe redirects |

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
| POST | `/billing/purchase` | Purchase token package (Stripe card or mobile money) |
| POST | `/billing/mobile-payment` | Mobile money payment (Orange Money / MTN MoMo) |
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
| **Aligned Simulation** | `USE_REAL_TRIBE=false` (default) | Advanced simulation using universal cortical basis, OR-thogonalized representations, canonical HRF deconvolution, full 70K voxel output, and subject-layer variability |

The simulation is architecturally aligned with the real TRIBE v2 paper across 5 stages:

1. **Tri-modal Feature Encoding** — Content-aware feature extraction from video (motion, color diversity, scene complexity, temporal variance), audio (amplitude envelope, spectral centroid, rhythm, speech confidence), and text (word length, novelty, familiarity, emotional valence, syntactic complexity)
2. **Universal Representation** — ROI-mean signals are projected through a 64-component orthogonal cortical basis (QR-decomposed sinusoids) producing a shared latent space across all modalities and stimuli
3. **Subject Layer** — Per-subject gain scaling, ROI-specific modulation, and noise flooring enables zero-shot generalization simulation across 4 built-in subject profiles (`default`, `high_attention`, `high_dopamine`, `low_engagement`)
4. **Full 70K Voxel Generation** — 20,484 cortical vertices (31 parcels across visual, auditory, language, attention, dopamine, memory, and somatomotor networks) + 49,516 subcortical voxels (thalamus, caudate, putamen, pallidum, brainstem, hippocampus, amygdala, accumbens)
5. **Canonical HRF Deconvolution** — Pseudo-inverse hemodynamic response function deconvolution recovers the underlying neural signal from the simulated BOLD response (opposite direction of traditional forward convolution, matching real fMRI preprocessing)

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

The frontend is a **Svelte 5** application built with **SvelteKit 2**, **TypeScript**, and **Tailwind CSS 3.4**.

### Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Marketing landing page with animated hero |
| Login | `/login` | Login form |
| Register | `/register` | Registration form |
| Dashboard | `/dashboard` | Main analysis dashboard |
| Analyze | `/analyze` | Video/audio/text analysis runner |
| AB Test | `/ab-test` | A/B test comparison interface |
| Copywriting | `/copywriting` | Neural copy analysis tool |
| Brain Explorer | `/brain-explorer` | Interactive 3D brain viewer |
| Thumbnail Generator | `/thumbnail` | AI thumbnail creation |
| History | `/history` | Past analysis results |
| Settings | `/settings` | User settings |
| Pricing | `/pricing` | Token pricing plans |
| Payment | `/payment` | 4-step payment wizard (method selection, card/mobile money) |
| Terms | `/terms` | Terms of service |
| Privacy | `/privacy` | Privacy policy |
| Results | `/results/[id]` | Individual analysis detail view |

### Key Libraries

| Library | Purpose |
|---------|---------|
| **Chart.js** (via npm) | Engagement curves, radar charts, doughnut charts, bar charts, gauge charts |
| **Three.js** (via npm) | 3D brain mesh rendering with ROI atlas highlighting |
| **GSAP** (via npm) | Scroll-triggered animations, page transitions, hero animations |
| **Tailwind CSS** | Utility-first styling with custom neural design tokens |
| **SvelteKit** | File-based routing, SSR/SSR hydration, API proxy, form actions |

### Design System

The Tailwind config in `tailwind.config.ts` defines custom color palettes for each neural dimension:

| Token | Usage |
|-------|-------|
| `neural-*` | Primary actions, active states, primary UI elements |
| `dopamine-*` | Reward/dopamine dimension visualizations |
| `memory-*` | Memory dimension visualizations |
| `surface-*` | Backgrounds, surfaces, elevated elements |

Custom component classes in `src/app.css`:
- `.glass` / `.glass-strong` — Glassmorphism panels
- `.gradient-text` — Gradient text for headings
- `.card-hover` — Interactive card hover effects
- `.input-neural` — Styled form inputs
- `.neural-grid` — Background grid pattern

---

## Token System & Billing

### Flow
1. User registers → receives 100 free tokens
2. Each API call deducts tokens based on operation type
3. Users can purchase token packages via Stripe card or mobile money
4. Transaction history is maintained for auditing

### Payment Methods

#### Stripe Card
- Checkout Sessions for one-time purchases via `/billing/purchase`
- Webhook handler at `/billing/stripe-webhook` for fulfillment
- Frontend redirects to `/payment?success=1` after successful checkout
- Supports automatic fallback when Stripe is not configured

#### Mobile Money (Orange Money / MTN MoMo)
- African mobile money integration via `/billing/mobile-payment`
- Accepts phone number with country code, operator selection, and amount
- Generates unique payment reference with `MOB-` prefix
- Token grant is applied immediately upon request (production would verify via Flutterwave/Paystack callback)

#### Card Type Detection
The frontend includes a zero-dependency card type detection utility at `src/lib/utils/card.ts`:

| Feature | Implementation |
|---------|---------------|
| Type Detection | Regex patterns for Visa, Mastercard, Amex, Discover, JCB, UnionPay |
| Validation | Luhn algorithm for card number checksum verification |
| Formatting | Auto-spacing with max digits per card type (16-19) |
| Expiry | MM/YY formatting with month range validation (01-12) |
| CVC | 3-4 digit validation based on card type |
| Phone | International phone number validation for mobile money |
| Visuals | SVG card brand logos rendered inline

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
│   ├── __init__.py
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
├── src/                    # SvelteKit frontend source
│   ├── app.html            # HTML shell
│   ├── app.css             # Tailwind + custom component classes
│   ├── app.d.ts            # Ambient type declarations
│   ├── hooks.server.ts     # Server hooks (auth, CSP headers)
│   ├── lib/                # Shared components, stores, utils
│   │   ├── components/     # UI & layout components
│   │   ├── stores/         # Svelte writable stores
│   │   ├── types/          # TypeScript type definitions
│   │   ├── utils/          # API client, helpers
│   │   └── i18n/           # Internationalization
│   └── routes/             # File-based SvelteKit routing
│       ├── +layout.svelte  # Root layout (sidebar, navbar, effects)
│       ├── +layout.server.ts
│       ├── +page.svelte    # Landing page
│       ├── login/
│       ├── dashboard/
│       ├── analyze/
│       ├── ab-test/
│       ├── brain-explorer/
│       └── ... (other routes)
├── static/                 # Static assets
│   └── favicon.svg
├── models/                 # Pre-trained model files (git LFS)
├── scripts/                # Utility scripts
├── uploads/                # Temporary uploads (gitignored)
├── cache/                  # Model cache (gitignored)
├── run.py                  # Server entry point
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies & scripts
├── svelte.config.js        # SvelteKit configuration (Vercel adapter)
├── vite.config.ts          # Vite bundler configuration
├── tailwind.config.ts      # Tailwind CSS with neural design tokens
├── postcss.config.js       # PostCSS (Tailwind + autoprefixer)
├── tsconfig.json           # TypeScript configuration
├── .env.example            # Environment template
└── opencode.json           # OpenCode AI IDE configuration
```

### Frontend Development

The SvelteKit frontend runs on its own dev server with HMR (Hot Module Replacement):

```bash
npm run dev          # start dev server (default http://localhost:5173)
npm run build        # production build to build/
npm run preview      # preview production build locally
npm run check        # type-check with svelte-check
```

The backend API must be running separately (see [Run the Server](#run-the-server)). The frontend dev server proxies API requests through SvelteKit's server hooks when needed.

#### GSAP Animation Pattern

To prevent SSR flash (content briefly visible before JS runs), all GSAP animations use the `opacity-0` CSS pattern:

```svelte
<!-- Element starts invisible via CSS -->
<div class="opacity-0" data-animate="fade-up">
  Content
</div>
```

```js
// GSAP animates to visible on mount
gsap.to('[data-animate="fade-up"]', {
  opacity: 1,
  y: 0,
  duration: 0.8,
  stagger: 0.15
});
```

This avoids `gsap.from()` which causes visible flash on SSR-rendered content. All animated pages (dashboard, analyze, pricing, payment) follow this pattern.

#### API Proxy Pattern

SvelteKit server routes at `src/routes/api/analyze/[type]/+server.ts` and `src/routes/api/billing/[action]/+server.ts` proxy requests to the FastAPI backend:

- Allowed billing actions are validated against `ALLOWED_BILLING_ACTIONS` in `src/lib/utils/validation.ts`
- Backend HTTP status codes (400, 401, 402, 404, 500) are passed through unmodified
- Errors are caught and returned as 502 with the backend error message
- File uploads use `FormData` forwarding with correct content-type passthrough
- AB test mode is handled via a `mode` field in the request body (`text`, `video`, `audio`)

### Gitignore

The `.gitignore` file excludes the following from version control:

| Pattern | What it excludes |
|---------|-----------------|
| `node_modules/` | npm dependencies |
| `.svelte-kit/` | SvelteKit build cache |
| `build/` / `dist/` | Production build output |
| `__pycache__/`, `*.py[cod]` | Python bytecode |
| `*.egg-info/`, `*.egg` | Python package builds |
| `.env`, `.env.*` | Environment secrets |
| `*.db`, `*.db-journal` | SQLite database files |
| `uploads/*` | Temporary uploads |
| `cache/*` | Model caching |
| `models/*` | Pre-trained model files (tracked via Git LFS) |
| `frontend/thumbnails/` | Generated thumbnail images |
| `frontend/brain_viz/` | Generated brain visualization HTML |
| `server*.log`, `server*.err` | Server log files |
| `.vercel/` | Vercel deploy artifacts |
| `frontend/` | Legacy static frontend (replaced by SvelteKit) |

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

## Production Deployment

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Vercel (Frontend)                                    │
│  SvelteKit SSR + ISR │ caching │ CDN                 │
└──────────┬──────────────────────────────────────────┘
           │ HTTPS (API proxy via SvelteKit server routes)
┌──────────▼──────────────────────────────────────────┐
│  Nginx (Reverse Proxy)                                │
│  Rate limiting │ caching │ compression │ SSL          │
└──────────┬──────────────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────┐
│  API (Gunicorn + Uvicorn workers)                     │
│  FastAPI │ JWT auth │ Stripe billing │ TRIBE v2       │
└──────────┬───────────────────────────┬──────────────┘
           │                           │
┌──────────▼─────────┐     ┌──────────▼──────────────┐
│  PostgreSQL 16      │     │  Redis 7                  │
│  Primary database   │     │  Cache │ rate limiting    │
│  Connection pooling │     │  Session store            │
└────────────────────┘     └─────────────────────────┘
```

The **frontend** (SvelteKit) deploys to **Vercel** using `npm run build`. The **backend** (FastAPI) runs in Docker with PostgreSQL and Redis on a VPS or cloud container service.

### Deploy the Backend (Docker)

```bash
# 1. Configure production environment
cp .env.production .env
# Edit .env with your secrets

# 2. Build and start the stack
docker-compose -f docker-compose.yml up -d

# 3. Verify health
curl http://localhost/health

# 4. View logs
docker-compose -f docker-compose.yml logs -f api
```

### Deploy the Frontend (Vercel)

```bash
# 1. Set environment variables in Vercel dashboard:
#    - API_URL: https://your-backend-domain.com
#    - PUBLIC_APP_URL: https://your-frontend.vercel.app

# 2. Deploy (via Vercel CLI or Git integration)
npx vercel --prod
```

Or connect your GitHub repo to Vercel for automatic deployments.

### Performance Configuration

#### Backend Workers

Adjust `WORKERS` in `.env.production` based on your CPU:
- **2 vCPUs**: `WORKERS=2`
- **4 vCPUs**: `WORKERS=4`
- **8 vCPUs**: `WORKERS=8`

Rule of thumb: `WORKERS = (2 × CPU cores) + 1`

#### Database Connection Pool

For high concurrency (100k users):

```env
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

#### Redis Memory

Redis is used for rate limiting and optional caching:
- Default: `maxmemory 1gb` with `allkeys-lru` eviction
- For high traffic: increase to `2gb`

#### Rate Limiting

Configured per endpoint tier in `.env.production`:

| Tier | Default Rate | Window |
|------|-------------|--------|
| General API | 100 req | 60s |
| Auth endpoints | 20 req | 60s |
| Analysis endpoints | 10 req | 60s |

### Scaling to 100k+ Users

#### Horizontal Scaling

The API is **stateless** (JWT-based auth), so you can scale horizontally:

```bash
# Run multiple API instances behind the load balancer
docker-compose up -d --scale api=3
```

Update `nginx/nginx.conf` upstream block to include all instances.

#### Database

- Use a **managed PostgreSQL** service (Neon, AWS RDS, Supabase) with connection pooling (PgBouncer)
- Key indexes already defined in `api/database.py`:
  - `users`: email + is_active, created_at
  - `analysis_history`: user_id + created_at, media_type
  - `token_transactions`: user_id + created_at
  - `thumbnail_history`: user_id + created_at
- For analytics: add read replicas

#### Caching Strategy

| Data | Cache | TTL | Strategy |
|------|-------|-----|----------|
| Token packages | In-memory | 5 min | Lazy refresh |
| Analysis results | Redis | 1 hour | Cache-aside |
| Rate limit counters | Redis | window | Real-time |
| Static files | Nginx/CDN | 30 days | Immutable |
| SvelteKit pages | Vercel ISR | 60s | Stale-while-revalidate |

#### CDN

The frontend is already served via Vercel's global CDN. Nginx caches static assets with 30-day immutable Cache-Control headers.

### Monitoring

- **Health endpoint**: `GET /health` — checks DB connectivity and model status
- **Request tracing**: Every response includes `X-Request-ID` and `X-Process-Time` headers
- **Slow request alerts**: Requests exceeding 5s are logged as warnings
- **Error tracking**: Optional Sentry integration (`SENTRY_DSN`)

### Security

| Measure | Implementation |
|---------|---------------|
| JWT Authentication | HS256 tokens with configurable expiry |
| Password Hashing | bcrypt with auto-generated salt |
| Rate Limiting | Redis-backed per-IP limiting per tier |
| CORS | Restricted origins in production |
| CSP Headers | Set via SvelteKit hooks |
| SQL Injection | SQLAlchemy parameterized queries |
| XSS Protection | Content-Security-Policy headers |
| HTTPS | Nginx termination / Vercel edge |
| File Upload Validation | Extension + size limits |

---

## License

This project is open source. See the LICENSE file for details.

---

## Links

- **GitHub**: [https://github.com/Joeltabe/Neuralpulse-engine](https://github.com/Joeltabe/Neuralpulse-engine)
