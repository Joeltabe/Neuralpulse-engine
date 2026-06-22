# NeuralPulse Engine — Frontend

<p align="center">
  <a href="https://neuralpulse-engine.vercel.app"><strong>Live Demo →</strong></a>
  &nbsp;·&nbsp;
  <a href="https://github.com/Joeltabe/neuralpulse-engine-backend"><strong>Backend Repo →</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/Joeltabe/Neuralpulse-engine?style=flat-square&label=Stars" alt="GitHub stars">
  <img src="https://img.shields.io/github/license/Joeltabe/Neuralpulse-engine?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/Svelte-5-orange?style=flat-square&logo=svelte" alt="Svelte 5">
  <img src="https://img.shields.io/badge/SvelteKit-2-673AB8?style=flat-square&logo=svelte" alt="SvelteKit 2">
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=flat-square&logo=typescript" alt="TypeScript 5">
  <img src="https://img.shields.io/badge/Tailwind-3.4-06B6D4?style=flat-square&logo=tailwindcss" alt="Tailwind 3.4">
  <img src="https://img.shields.io/badge/Vercel-Deployed-000000?style=flat-square&logo=vercel" alt="Deployed on Vercel">
  <img src="https://img.shields.io/badge/Three.js-3D-000000?style=flat-square&logo=three.js" alt="Three.js 3D">
  <img src="https://img.shields.io/badge/GSAP-Animations-88CE02?style=flat-square" alt="GSAP Animations">
</p>

**Brain-validated ad optimization dashboard.** Upload video, audio, or text ads and see simulated fMRI brain responses across attention, dopamine, and memory dimensions — powered by TRIBE v2 neuroscience simulation on the backend.

> 🔬 **95% of purchasing decisions are subconscious** (Zaltman, 2003). NeuralPulse Engine makes those invisible processes visible, measurable, and optimizable — from a browser.

---

## Table of Contents

- [What Is NeuralPulse Engine](#what-is-neuralpulse-engine)
- [Features — Per Page](#features--per-page)
- [Use Cases](#use-cases)
- [User Journey](#user-journey)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [API Proxy Pattern](#api-proxy-pattern)
- [Component Library](#component-library)
- [Design System](#design-system)
- [GSAP Animation Pattern](#gsap-animation-pattern)
- [Card Type Detection](#card-type-detection)
- [Development](#development)
- [Deployment](#deployment)
- [Links](#links)

---

## What Is NeuralPulse Engine

NeuralPulse Engine is a **computational neuromarketing platform** split across two repos:

| Repo | Stack | Host | Purpose |
|------|-------|------|---------|
| **Frontend** (this repo) | SvelteKit 2 + Tailwind + Three.js + Chart.js | Vercel | Dashboard, visualizations, user management |
| **Backend** | Python FastAPI + TRIBE v2 + PostgreSQL | Railway (Docker) | Brain simulation engine, REST API, database |

The frontend delivers a **luxury glassmorphism UI** with 3D brain visualization, real-time neural analytics, and full ad creative management — all proxied through SvelteKit server routes so the backend stays hidden from browsers.

---

## Features — Per Page

### 🏠 Landing Page (`/`)

| Section | Description |
|---------|-------------|
| **Hero** | Animated 3D brain mesh (Three.js) with pulsing neural glow, gradient text headline, CTA buttons |
| **Feature Grid** | 6 glassmorphism cards: Neural Ad Analysis, A/B Testing, Copywriting, Brain Explorer, Thumbnail Gen, Virality Scoring — each with hover lift + glow |
| **How It Works** | 4-step explainer: Upload → Simulate → Analyze → Optimize, with staggered GSAP scroll-triggered reveal |
| **Testimonials** | Carousel with avatar + quote cards |
| **CTA** | "Start Analyzing Your Ads" gradient button, trust bar (logos, metrics) |

**Use case:** First impression. Converts visitors into signups by demonstrating the platform's scientific credibility and visual polish.

---

### 🔐 Login (`/login`)

| Element | Description |
|---------|-------------|
| **Form** | Email + password with client-side validation, show/hide password toggle |
| **Social** | Google OAuth button, "Sign in with GitHub" |
| **Demo Login** | One-click demo account with 500 free tokens |
| **Links** | "Forgot password?", "Don't have an account? Register" |
| **Animated** | Page-wide brain particle background, floating orbs |

**Use case:** Low-friction authentication with demo access to let prospects try the full platform without committing.

---

### 📝 Register (`/register`)

| Element | Description |
|---------|-------------|
| **Form Fields** | Name, email, password, confirm password |
| **Bonus** | 100 free tokens on signup |
| **Validation** | Real-time email format, password strength meter, match confirm |
| **Captcha** | Turnstile/Recaptcha integration |
| **Post-signup** | Auto-redirect to dashboard with welcome toast |

**Use case:** Convert landing visitors into registered users with immediate free token balance.

---

### 📊 Dashboard (`/dashboard`)

| Component | Description |
|-----------|-------------|
| **Token Balance** | Animated odometer counter + "Buy Tokens" CTA when low |
| **Recent Analyses** | Last 5 results as interactive cards with grade (A+–F) and date |
| **Quick Actions** | "New Analysis", "A/B Test", "Copywriting", "Thumbnail" |
| **Activity Chart** | 7-day analysis volume bar chart (Chart.js) |
| **Savings Meter** | Tokens saved this month vs. previous |

**Data sources:** `POST /api/history/stats`, `GET /api/history/recent` (proxied to backend).

**Use case:** Central command center — users see their activity at a glance and jump into any workflow.

---

### 🎬 Analyze (`/analyze`)

| Step | Component | Description |
|------|-----------|-------------|
| 1. Upload | `UploadZone.svelte` | Drag-and-drop video (MP4, WebM, AVI), audio (MP3, WAV, FLAC), or text. 120s client-side timeout with abort. Client-side FFmpeg WASM for video preprocessing (trim, resize, extract audio) |
| 2. Processing | `AnalysisProgress.svelte` | Real-time progress bar with stage labels: "Extracting features", "Simulating brain response", "Computing scores" |
| 3. Results | `ScoreCards.svelte` | 3 gauge cards: Attention Score (0–100), Dopamine Score (0–100), Memory Score (0–100) — each with color-coded arc |
| 4. Detail | `EngagementChart.svelte` | Temporal engagement curve (line chart, 100 time points) with dropoff markers |
| 5. Brain | `RegionHeatmap.svelte` | ROI activation matrix: 18 ROIs × 3 dimensions, color intensity |
| 6. Virality | `ViralityMeter.svelte` | Gauge + 5 factor breakdown: face engagement, emotional arousal, auditory hook, visual salience, narrative immersion |

**Backend call:** `POST /api/analyze/video`, `/audio`, or `/text`.

**Use case:** Core product — users upload their ad creative and get a full brain response report.

---

### 🔬 A/B Test (`/ab-test`)

| Feature | Description |
|---------|-------------|
| **Variant Manager** | Add 2+ variants via upload or paste, drag to reorder |
| **Comparison Chart** | Grouped bar chart (Chart.js) — all 3 dimensions side-by-side per variant |
| **Radar Overlay** | Multi-dimension radar with each variant as a colored polygon |
| **Statistical Test** | t-test results per dimension, Cohen's d effect size, Bonferroni correction |
| **Winner Badge** | "Best Variant" badge on the highest-scoring version |
| **Export** | PNG chart download, CSV data export |

**Use case:** Optimize ad creative — compare headlines, visuals, CTAs, or full videos against each other with statistical confidence.

---

### ✍️ Copywriting (`/copywriting`)

| Feature | Description |
|---------|-------------|
| **Editor** | `RichTextEditor.svelte` with formatting toolbar (bold, italic, lists, headings) |
| **Framing Selector** | Choose from 9 framing types: gain, loss, urgency, social proof, authority, reciprocity, curiosity, pain point, aspirational |
| **Neural Scores** | Per-framing attention/dopamine/memory scores with bar chart |
| **Top Frame** | Auto-detected best-performing framing with explanation |
| **Full Report** | Combined copy + framing analysis with printable layout |

**Backend call:** `POST /api/copy/analyze`.

**Use case:** Marketers and copywriters optimize ad copy for maximum subconscious impact before publishing.

---

### 🧠 Brain Explorer (`/brain-explorer`)

| Feature | Description |
|---------|-------------|
| **3D Brain** | `BrainScene.svelte` — Three.js OBJ brain mesh with orbit controls, auto-rotation |
| **ROI Overlays** | `ROIOverlay.svelte` — Toggle 18 ROI regions with color-coded activation (red=high, blue=low) |
| **Mode Toggle** | Attention / Dopamine / Memory — re-colors ROIs based on the selected neural dimension |
| **Brain Controls** | `BrainControls.svelte` — Rotation speed, zoom, reset view, cross-section toggle |
| **Info Panel** | Click any ROI to see name, coordinates, function, and current activation level |

**Use case:** Educational tool and "wow factor" — users explore which brain regions respond to their content and learn neuromarketing science.

---

### 🖼️ Thumbnail Generator (`/thumbnail`)

| Feature | Description |
|---------|-------------|
| **Model Selector** | Choose from FLUX.1-dev, SD3.5, Qwen2-VL, Cosmos3 — each with preview cards |
| **Prompt Input** | Text area with prompt enhancement tips ("include face, high contrast, bright colors") |
| **Generation** | Loading spinner with estimated time |
| **Gallery** | 4 generated thumbnails in a grid, each with neural forecast overlay |
| **Forecast** | Predicted attention score + CTR estimate for each thumbnail |
| **Download** | PNG export at 1280×720 |

**Backend call:** `POST /api/thumbnail/generate`.

**Use case:** Content creators generate and scientifically validate YouTube/Instagram thumbnails before posting.

---

### 📜 History (`/history`)

| Feature | Description |
|---------|-------------|
| **List View** | Paginated table: date, type (video/audio/text/copy/thumbnail), grade, token cost, score summary |
| **Search** | Full-text search across analysis names |
| **Filter** | By type, date range, score range (min–max grade) |
| **Export** | PDF report per analysis, CSV bulk export |
| **Delete** | Single or batch delete with confirmation modal |

**Backend call:** `POST /api/history/list`, `POST /api/history/export`.

**Use case:** Reference past analyses, track performance over time, export reports for clients.

---

### ⚙️ Settings (`/settings`)

| Tab | Fields |
|-----|--------|
| **Profile** | Name, email, avatar upload |
| **Preferences** | Theme (dark/light), language, default analysis type |
| **Security** | Password change, 2FA toggle, active sessions list |
| **API Keys** | Generate/revoke API keys for programmatic access |
| **Notifications** | Email preferences for analysis completion, low tokens |

**Use case:** User account management and personalization.

---

### 💰 Pricing (`/pricing`)

| Tier | Tokens | Price | Features |
|------|--------|-------|----------|
| **Starter** | 100 | Free (signup) | 1 analysis type, basic reports |
| **Creator** | 500 | $9.99 | All analysis types, A/B testing, export |
| **Professional** | 2,000 | $29.99 | Priority queue, API access, team sharing |
| **Agency** | 10,000 | $99.99 | White-label reports, dedicated support |

Each tier card has: token count, price per token, feature list, "Buy" button with hover glow effect.

**Use case:** Convert users to paid customers by showing clear tier value.

---

### 💳 Payment (`/payment`)

| Step | Component | Description |
|------|-----------|-------------|
| 1. Method | Radio cards | Credit/debit card, Mobile Money (MTN, Airtel, Vodafone) |
| 2. Card Details | `CardForm.svelte` | Card number (auto-detect brand via Luhn), expiry, CVC — live validation |
| 3. Confirm | `ConfirmStep.svelte` | Summary: tier, amount, card masked — "Confirm Payment" button |
| 4. Receipt | `ReceiptStep.svelte` | Success animation, token balance updated, download PDF receipt |

**Backend call:** `POST /api/billing/purchase`.

**Use case:** Complete purchase with zero friction — card detection, validation, and mobile money support.

---

### 📈 Results (`/results/[id]`)

| Section | Component | Description |
|---------|-----------|-------------|
| **Header** | — | Ad name, date, overall grade badge (A+–F) |
| **Scores** | `ScoreCards.svelte` | 3 gauge cards for attention, dopamine, memory |
| **Engagement** | `EngagementChart.svelte` | Line chart with dropoff annotations |
| **Radar** | `RadarChart.svelte` | Multi-dimension radar (if A/B test) |
| **Heatmap** | `RegionHeatmap.svelte` | 18 ROI × 3 dimension matrix |
| **Virality** | `ViralityMeter.svelte` | Gauge + 5 factors |
| **Recommendations** | — | Actionable list: "Add face in first 3 seconds", "Increase contrast in thumbnail" |
| **Copy** | — | Full analyzed text with highlighted framing spans (if copy analysis) |
| **Share** | — | Copy link, download PDF, export CSV |

**Use case:** Deep dive into a single analysis — the full report users reference and share.

---

## Use Cases

| Who | Problem | How NeuralPulse Helps |
|-----|---------|----------------------|
| **Digital Marketers** | Can't predict which ad creative will perform | Neural scores predict subconscious engagement before launch |
| **Content Creators** | Thumbnails and hooks are guesswork | AI thumbnail generation + neural forecast + CTR estimate |
| **Copywriters** | Don't know which framing resonates | 9-framing neural comparison with auto best-frame detection |
| **A/B Testers** | Need statistical confidence in variant decisions | Multi-variant test with t-test, Cohen's d, Bonferroni correction |
| **Agency Strategists** | Must justify creative decisions to clients | Full-color brain heatmaps, printable PDF reports, grade badges |

---

## User Journey

```
Landing → Register (100 free tokens) → Dashboard → Upload Ad → 
Brain Simulation → Scores + Heatmaps → Optimize → A/B Test → 
Best Variant → Export Report → Share with Client
```

New users go from zero to a full brain response report in under 2 minutes with the demo login.

---

## Architecture Overview

```
Browser (User)
     │ HTTPS
     ▼
Vercel (SvelteKit SSR + ISR + CDN)
     │
     │  ┌─────────────────────────────────────────┐
     │  │  SvelteKit Server Routes (API Proxy)     │
     │  │  /api/auth/[action]                      │
     │  │  /api/analyze/[type]                     │
     │  │  /api/billing/[action]                   │
     │  │  /api/history/[action]                   │
     │  │  /api/thumbnail/[action]                 │
     │  │  /api/copy/[action]                      │
     │  └────────────────┬────────────────────────┘
     ▼                   │ Internal API calls (server-side)
Railway (FastAPI Backend Docker Container)
 /auth/*  │  /analyze/*  │  /billing/*  │  /history/*
```

The frontend never calls the backend directly from the browser. All API requests go through SvelteKit server routes, which proxy them to the backend using the `API_URL` environment variable. This keeps the backend URL hidden from clients and allows the frontend to add auth tokens, validate inputs, and handle errors before they reach the browser.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Svelte 5 + SvelteKit 2 |
| Charts | Chart.js 4 with custom neural-themed plugins |
| 3D Rendering | Three.js (OBJLoader, OrbitControls) |
| Animations | GSAP 3 + ScrollTrigger — fade-up, stagger, parallax |
| Styling | Tailwind CSS 3.4 with custom neural design tokens |
| Language | TypeScript 5 (strict mode across all 80+ components) |
| Adapter | @sveltejs/adapter-vercel (Node.js 20, ISR 60s) |
| HTTP Client | Native fetch via SvelteKit server routes (no axios) |
| Video Processing | @ffmpeg/ffmpeg (WASM, client-side) |
| Payment | Card detection (Luhn), mobile money validation |
| Formatting | Prettier (Svelte plugin), ESLint |

---

## Getting Started

### Prerequisites

- **Node.js 18+** and npm
- **Python backend** running locally or remotely (see [backend repo](https://github.com/Joeltabe/neuralpulse-engine-backend))

### Installation

```bash
git clone https://github.com/Joeltabe/Neuralpulse-engine.git
cd Neuralpulse-engine
npm install
cp .env.example .env
```

### Environment Variables

```env
API_URL=http://localhost:8000
ISR_BYPASS_TOKEN=
```

### Run Dev Server

```bash
npm run dev
```

Opens at `http://localhost:5173` with HMR. Run the backend separately on `http://localhost:8000`.

---

## API Proxy Pattern

All backend communication goes through SvelteKit server routes:

1. **Security** — Backend URL and auth tokens never reach the browser
2. **Validation** — Input sanitization server-side before hitting backend
3. **Error Handling** — Consistent error responses, token refresh, graceful degradation
4. **Cookie Management** — HTTP-only cookies for auth tokens set/read server-side

```typescript
// src/lib/utils/api.ts — proxy fetch wrapper
const API_BASE = env.API_URL || 'http://localhost:8000';

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers: Record<string, string> = { ...(options.headers as Record<string, string>) };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120_000);
  try {
    const res = await fetch(`${API_BASE}${endpoint}`, { ...options, headers, signal: controller.signal });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(body.error || `Request failed: ${res.status}`);
    }
    return res.json();
  } finally {
    clearTimeout(timeoutId);
  }
}
```

---

## Component Library

### Layout

| Component | Description |
|-----------|-------------|
| `Navbar.svelte` | Sticky top bar — logo, token balance odometer, user avatar dropdown |
| `Sidebar.svelte` | Collapsible glass sidebar with route links + active state highlight |
| `Footer.svelte` | Footer with links, social icons, copyright |

### Home

| Component | Description |
|-----------|-------------|
| `HeroSection.svelte` | Animated landing hero with Three.js brain, gradient headline, CTA buttons |
| `FeatureGrid.svelte` | 6 glass cards with hover lift + glow effect |
| `HowItWorks.svelte` | 4-step scroll-triggered reveal with GSAP |
| `TestimonialCarousel.svelte` | Auto-rotating quote cards |
| `CTASection.svelte` | "Start Now" section with trust metrics |

### Analysis

| Component | Description |
|-----------|-------------|
| `UploadZone.svelte` | Drag-and-drop with preview, FFmpeg preprocessing, abort support |
| `ScoreCards.svelte` | 3 arc gauges — attention, dopamine, memory |
| `AnalysisProgress.svelte` | Stage-based progress with animated bar |
| `RegionHeatmap.svelte` | 18×3 matrix heatmap (Chart.js matrix plugin) |
| `ViralityMeter.svelte` | Virality gauge + 5-factor breakdown |

### Brain

| Component | Description |
|-----------|-------------|
| `BrainScene.svelte` | Three.js with OBJLoader, OrbitControls, auto-rotation |
| `BrainControls.svelte` | Mode toggle, rotation speed, zoom, reset, cross-section |
| `ROIOverlay.svelte` | Toggleable ROI regions with color-coded activation |

### Charts

| Component | Description |
|-----------|-------------|
| `EngagementChart.svelte` | Temporal line chart with dropoff markers |
| `RadarChart.svelte` | Multi-dataset radar for A/B comparison |
| `DoughnutChart.svelte` | Score distribution doughnut |
| `BarChart.svelte` | Variant comparison bar chart |
| `GaugeChart.svelte` | Single-score gauge 0–100 |

### Editor

| Component | Description |
|-----------|-------------|
| `RichTextEditor.svelte` | ContentEditable with formatting toolbar |
| `Toolbar.svelte` | Bold, italic, underline, list, heading buttons |

### UI (Generic)

| Component | Description |
|-----------|-------------|
| `Toast.svelte` | Positioned toast with auto-dismiss |
| `Modal.svelte` | Centered glass modal with backdrop blur |
| `Button.svelte` | 6 variants: primary, secondary, ghost, danger, gradient, icon |
| `Input.svelte` | Label, validation state, error message, icon slot |
| `Card.svelte` | Glassmorphism container with configurable blur/opacity |
| `LoadingSpinner.svelte` | Spinning neural-ring SVG |
| `EmptyState.svelte` | Icon + message + action button |

### Effects

| Component | Description |
|-----------|-------------|
| `Particles.svelte` | Canvas-based particle system (neural connection lines) |
| `FloatingOrbs.svelte` | CSS-animated gradient orbs z-index layers |
| `GridBackground.svelte` | SVG dot grid with subtle parallax |

---

## Design System

### Color Tokens

| Token | Usage |
|-------|-------|
| `neural-50` … `neural-950` | Primary actions, active states, UI accents — indigo/violet |
| `dopamine-500` … `dopamine-950` | Dopamine/reward visualizations — amber/orange |
| `memory-500` … `memory-950` | Memory dimension — emerald |
| `surface-50` … `surface-950` | Backgrounds, surfaces, elevated panels — dark slate |

### Custom CSS Classes

| Class | Purpose |
|-------|---------|
| `.glass` | Glassmorphism: backdrop-blur, semi-transparent bg |
| `.glass-strong` | Higher opacity glass |
| `.gradient-text` | Linear gradient text fill |
| `.card-hover` | Hover: translateY(-2px), box-shadow glow |
| `.input-neural` | Focus ring with neural color, rounded |
| `.neural-grid` | Background dot grid |

### Typography

- **Inter** — Body, UI (300–800 weight)
- **JetBrains Mono** — Code, scores, data displays

### Animations

| Animation | Type | Description |
|-----------|------|-------------|
| `glow` | CSS | Pulsing box-shadow on active elements |
| `float` | CSS | Gentle vertical translate cycle on cards |
| `shimmer` | CSS | Sweeping gradient on loading skeletons |
| `brain-pulse` | CSS | Rhythmic scale pulse on brain container |

---

## GSAP Animation Pattern

All GSAP animations use the `opacity-0` CSS pattern to prevent SSR flash:

```svelte
<div class="opacity-0" data-animate="fade-up">
  Content
</div>

<script>
  import { onMount } from 'svelte';
  import gsap from 'gsap';

  onMount(() => {
    gsap.to('[data-animate="fade-up"]', {
      opacity: 1,
      y: 0,
      duration: 0.8,
      stagger: 0.15,
      ease: 'power3.out'
    });
  });
</script>
```

---

## Card Type Detection

The frontend includes a zero-dependency card utility (`src/lib/utils/card.ts`):

| Feature | Detail |
|---------|--------|
| Type Detection | Regex for Visa, Mastercard, Amex, Discover, JCB, UnionPay |
| Validation | Luhn checksum |
| Formatting | Auto-space every 4 digits, max length per brand |
| Expiry | MM/YY auto-slash, 01–12 month validation |
| CVC | 3–4 digits based on card type |
| Phone | International mobile money number validation |
| Visuals | Inline SVG brand logos |

---

## Development

### Commands

```bash
npm run dev          # Dev server at localhost:5173 with HMR
npm run build        # Production build to build/
npm run preview      # Preview production build locally
npm run check        # Type-check with svelte-check
```

### Project Structure

```
Neuralpulse-engine/
├── src/
│   ├── app.html                   # HTML shell (dark theme, fonts)
│   ├── app.css                    # Tailwind directives + custom CSS
│   ├── app.d.ts                   # Ambient type declarations
│   ├── hooks.server.ts            # Server hooks — CSP, auth
│   ├── lib/
│   │   ├── components/            # Svelte components by domain
│   │   │   ├── analysis/          # Analysis UI (upload, scores, heatmaps)
│   │   │   ├── brain/             # Three.js brain visualization
│   │   │   ├── charts/            # Chart.js wrappers
│   │   │   ├── editor/            # Rich text editor for copywriting
│   │   │   ├── effects/           # Particles, orbs, grid backgrounds
│   │   │   ├── home/              # Landing page sections
│   │   │   ├── layout/            # Navbar, sidebar, footer
│   │   │   └── ui/                # Button, Input, Modal, Toast, Card
│   │   ├── editor/                # Editor utilities
│   │   ├── i18n/                  # Internationalization
│   │   ├── stores/                # Svelte writable stores
│   │   ├── types/                 # TypeScript type definitions
│   │   └── utils/                 # API client, validation, helpers
│   └── routes/                    # SvelteKit file-based routing
│       ├── +layout.svelte         # Root layout
│       ├── +page.svelte           # Landing page
│       ├── ab-test/               # A/B test comparison
│       ├── analyze/               # Upload + analysis
│       ├── api/                   # API proxy server routes
│       ├── brain-explorer/        # 3D brain explorer
│       ├── copywriting/           # Neural copy analysis
│       ├── dashboard/             # User dashboard
│       ├── history/               # Past analyses
│       ├── login/                 # Login page
│       ├── logout/                # Logout
│       ├── payment/               # 4-step checkout
│       ├── pricing/               # Token pricing tiers
│       ├── privacy/               # Privacy policy (legal)
│       ├── register/              # Registration
│       ├── results/               # Analysis results detail
│       ├── settings/              # User settings
│       ├── terms/                 # Terms of service (legal)
│       └── thumbnail/             # Thumbnail generator
├── static/                        # Favicon, assets
├── .env.example                   # Environment variables
├── svelte.config.js               # Vercel adapter config
├── tailwind.config.ts             # Custom neural design tokens
├── vercel.json                    # Vercel deployment + headers
└── vite.config.ts                 # Vite bundler
```

### CSP Headers

**Development:** `'unsafe-inline'` and `'unsafe-eval'` for HMR, WebSocket to localhost.

**Production:** `script-src 'self' 'unsafe-inline'` (SvelteKit hydration), Google Fonts allowed.

---

## Deployment

### Vercel (Production)

Auto-deploys from GitHub. `svelte.config.js` uses `@sveltejs/adapter-vercel` (Node.js 20, ISR 60s).

### Required Environment Variables

| Variable | Value |
|----------|-------|
| `API_URL` | `https://neuralpulse-engine-backend-production.up.railway.app` |
| `ISR_BYPASS_TOKEN` | *(optional)* |

### Manual Deploy

```bash
npm run build
npx vercel --prod
```

### Caching

| Asset | Duration |
|-------|----------|
| `/_app/immutable/*` | 1 year (immutable) |
| Pages (HTML) | 60s ISR |
| API responses | No cache |

### Security Headers

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- Content-Security-Policy (see CSP section)

---

## Links

| Resource | URL |
|----------|-----|
| **Live Frontend** | [https://neuralpulse-engine.vercel.app](https://neuralpulse-engine.vercel.app) |
| **Frontend GitHub** | [https://github.com/Joeltabe/Neuralpulse-engine](https://github.com/Joeltabe/Neuralpulse-engine) |
| **Backend GitHub** | [https://github.com/Joeltabe/neuralpulse-engine-backend](https://github.com/Joeltabe/neuralpulse-engine-backend) |
| **Backend API** | `https://neuralpulse-engine-backend-production.up.railway.app` |

---

<p align="center">
  <b>Built with</b> SvelteKit · Three.js · Chart.js · GSAP · Tailwind CSS
  <br>
  <b>Powered by</b> TRIBE v2 brain simulation · FastAPI · PostgreSQL
  <br><br>
  <a href="https://neuralpulse-engine.vercel.app"><strong>Try the live demo →</strong></a>
</p>
