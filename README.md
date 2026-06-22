# NeuralPulse Engine — Frontend

**Brain-validated ad optimization using simulated fMRI responses via TRIBE v2.**

SvelteKit frontend deployed on Vercel. Communicates with the Python backend at [neuralpulse-engine-backend](https://github.com/Joeltabe/neuralpulse-engine-backend) (FastAPI on Railway).

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Pages & Routes](#pages--routes)
- [Getting Started](#getting-started)
- [API Proxy Pattern](#api-proxy-pattern)
- [Component Library](#component-library)
- [Design System](#design-system)
- [GSAP Animation Pattern](#gsap-animation-pattern)
- [Card Type Detection](#card-type-detection)
- [Development](#development)
- [Deployment](#deployment)
- [Project Structure](#project-structure)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Browser (User)                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│              Vercel (SvelteKit SSR + ISR + CDN)               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              SvelteKit Server Routes                  │    │
│  │  /api/auth/[action]  │  /api/analyze/[type]          │    │
│  │  /api/billing/[action]│ /api/history/[action]        │    │
│  │  /api/thumbnail/[action]│ /api/copy/[action]         │    │
│  └──────────────────────┬───────────────────────────────┘    │
└──────────────────────────┼──────────────────────────────────┘
                           │ Internal API calls (server-side)
┌──────────────────────────▼──────────────────────────────────┐
│      Railway (FastAPI Backend Docker Container)               │
│  /auth/*  │  /analyze/*  │  /billing/*  │  /history/*       │
└──────────────────────────────────────────────────────────────┘
```

The frontend never calls the backend directly from the browser. All API requests go through SvelteKit server routes, which proxy them to the backend using the `API_URL` environment variable. This keeps the backend URL hidden from clients and allows the frontend to add auth tokens, validate inputs, and handle errors before they reach the browser.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Svelte 5 + SvelteKit 2 |
| Meta-framework | SvelteKit with Vite |
| Charts | Chart.js 4 |
| 3D Rendering | Three.js |
| Animations | GSAP 3 + ScrollTrigger |
| Styling | Tailwind CSS 3.4 |
| Package Manager | npm |
| Language | TypeScript 5 |
| Adapter | @sveltejs/adapter-vercel |
| HTTP Client | Native fetch (via SvelteKit server routes) |
| Video Processing | @ffmpeg/ffmpeg (wasm, client-side) |

---

## Pages & Routes

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Marketing hero with animated brain visualization, feature highlights, CTA |
| Login | `/login` | Email/password login form |
| Register | `/register` | Registration form with 100 free tokens |
| Dashboard | `/dashboard` | Main hub — recent analyses, token balance, quick actions |
| Analyze | `/analyze` | Upload video/audio/text for neural analysis |
| AB Test | `/ab-test` | Compare 2+ variants across neural dimensions |
| Copywriting | `/copywriting` | Neural copy analysis with 9 framing types |
| Brain Explorer | `/brain-explorer` | Interactive 3D brain with ROI atlas overlays |
| Thumbnail Generator | `/thumbnail` | AI thumbnail creation with neural forecasting |
| History | `/history` | Past analysis results with export |
| Settings | `/settings` | User profile and preferences |
| Pricing | `/pricing` | Token package comparison |
| Payment | `/payment` | 4-step wizard: method → card/mobile money → confirm → receipt |
| Terms | `/terms` | Terms of service |
| Privacy | `/privacy` | Privacy policy |
| Results | `/results/[id]` | Detailed analysis view with charts |

### API Server Routes (proxied)

| Route | Backend Target | Purpose |
|-------|---------------|---------|
| `POST /api/auth/[action]` | `POST /auth/[action]` | Login, register, demo-login, logout |
| `POST /api/analyze/[type]` | `POST /analyze/[type]` | Video/audio/text analysis |
| `POST /api/copy/[action]` | `POST /copy/[action]` | Copywriting analysis |
| `POST /api/billing/[action]` | `POST /billing/[action]` | Token purchase, balance, history |
| `POST /api/history/[action]` | `GET /history/[action]` | Analysis history and stats |
| `POST /api/thumbnail/[action]` | `/thumbnail/[action]` | Thumbnail generation |
| `GET /api/predict/[...path]` | `POST /api/predict-brain` | Legacy brain prediction |

---

## Getting Started

### Prerequisites

- **Node.js 18+** and npm
- **Python backend** running locally or remotely (see backend repo)

### Installation

```bash
# Clone the repository
git clone https://github.com/Joeltabe/Neuralpulse-engine.git
cd Neuralpulse-engine

# Install dependencies
npm install

# Create environment file
cp .env.example .env
```

### Environment Variables

Create a `.env` file in the project root:

```env
# Backend API URL (required)
API_URL=http://localhost:8000

# SvelteKit ISR bypass token (optional, for Vercel)
ISR_BYPASS_TOKEN=
```

### Run Development Server

```bash
npm run dev
```

The dev server starts at `http://localhost:5173` with HMR enabled. The backend must be running separately on `http://localhost:8000`.

---

## API Proxy Pattern

All communication with the backend goes through SvelteKit server routes. This is a deliberate architectural choice:

### Why Server Routes Instead of Direct Calls?

1. **Security** — Backend URL and auth tokens are never exposed to the browser
2. **Validation** — Input sanitization and validation happens server-side before reaching the backend
3. **Error Handling** — Consistent error responses, token refresh, and graceful degradation
4. **Cookie Management** — HTTP-only cookies for auth tokens are set/read server-side

### Flow

```
Browser                          Vercel (SvelteKit)                Railway (FastAPI)
   │                                    │                                │
   │  POST /api/auth/login              │                                │
   │───────────────────────────────────►│                                │
   │                                    │  POST /auth/login              │
   │                                    │───────────────────────────────►│
   │                                    │                                │
   │                                    │  { token, user }               │
   │                                    │◄───────────────────────────────│
   │                                    │                                │
   │  Set-Cookie: neuralpulse_token     │                                │
   │◄───────────────────────────────────│                                │
   │  { success: true, user }           │                                │
```

### Implementation

The proxy is implemented in `src/routes/api/[resource]/[action]/+server.ts` files. Each handler:
1. Extracts parameters from the request
2. Validates inputs using utilities in `src/lib/utils/validation.ts`
3. Calls the backend via `apiFetch()` from `src/lib/utils/api.ts`
4. Handles cookies (set/delete auth tokens)
5. Returns the response or a formatted error

```typescript
// src/lib/utils/api.ts
import { env } from '$env/dynamic/private';

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

Components live in `src/lib/components/` organized by domain:

### Layout
| Component | Description |
|-----------|-------------|
| `Navbar.svelte` | Top navigation — logo, token balance, user menu |
| `Sidebar.svelte` | Collapsible sidebar with route links |
| `Footer.svelte` | Page footer with links |

### Home
| Component | Description |
|-----------|-------------|
| `HeroSection.svelte` | Animated landing hero with brain visualization |
| `FeatureGrid.svelte` | Feature highlight cards |
| `HowItWorks.svelte` | Step-by-step explainer |
| `TestimonialCarousel.svelte` | User testimonials |
| `CTASection.svelte` | Call-to-action section |

### Analysis
| Component | Description |
|-----------|-------------|
| `UploadZone.svelte` | Drag-and-drop file upload with preview |
| `ScoreCards.svelte` | Attention/dopamine/memory score display |
| `AnalysisProgress.svelte` | Progress indicator during analysis |
| `RegionHeatmap.svelte` | ROI activation heatmap |
| `ViralityMeter.svelte` | Virality score gauge |

### Brain
| Component | Description |
|-----------|-------------|
| `BrainScene.svelte` | Three.js 3D brain renderer |
| `BrainControls.svelte` | Mode toggle and rotation controls |
| `ROIOverlay.svelte` | ROI atlas overlay on brain mesh |

### Charts
| Component | Description |
|-----------|-------------|
| `EngagementChart.svelte` | Temporal engagement curve (line chart) |
| `RadarChart.svelte` | Multi-dimension radar comparison |
| `DoughnutChart.svelte` | Score distribution doughnut |
| `BarChart.svelte` | Variant comparison bar chart |
| `GaugeChart.svelte` | Single-score gauge display |

### Editor
| Component | Description |
|-----------|-------------|
| `RichTextEditor.svelte` | Rich text input for copy analysis |
| `Toolbar.svelte` | Formatting toolbar (bold, italic, etc.) |

### UI (Generic)
| Component | Description |
|-----------|-------------|
| `Toast.svelte` | Toast notification system |
| `Modal.svelte` | Reusable modal dialog |
| `Button.svelte` | Styled button variants |
| `Input.svelte` | Form input with validation |
| `Card.svelte` | Glassmorphism card container |
| `LoadingSpinner.svelte` | Loading indicator |
| `EmptyState.svelte` | Empty state placeholder |

### Effects
| Component | Description |
|-----------|-------------|
| `Particles.svelte` | Animated particle background |
| `FloatingOrbs.svelte` | Floating gradient orbs |
| `GridBackground.svelte` | Neural grid pattern |

---

## Design System

### Color Tokens

Defined in `tailwind.config.ts`:

| Token | Usage |
|-------|-------|
| `neural-50` through `neural-950` | Primary actions, active states, UI accents — indigo/violet spectrum |
| `dopamine-500` through `dopamine-950` | Dopamine/reward visualizations — amber/orange |
| `memory-500` through `memory-950` | Memory dimension visualizations — emerald |
| `surface-50` through `surface-950` | Backgrounds, surfaces, elevated panels — dark slate |

### Custom CSS Classes

Defined in `src/app.css`:

| Class | Purpose |
|-------|---------|
| `.glass` | Glassmorphism panel with backdrop blur |
| `.glass-strong` | Stronger glass effect with more opacity |
| `.gradient-text` | Gradient text fill for headings |
| `.card-hover` | Interactive card with lift and glow on hover |
| `.input-neural` | Styled form inputs with focus ring |
| `.neural-grid` | Background dot grid pattern |

### Typography

- **Inter** — Body text, UI elements (300–800 weight)
- **JetBrains Mono** — Code, data displays, scores

### Animations

| Animation | Trigger | Description |
|-----------|---------|-------------|
| `glow` | CSS | Pulsing glow effect on active elements |
| `float` | CSS | Gentle vertical float on cards |
| `shimmer` | CSS | Shimmer sweep on loading states |
| `brain-pulse` | CSS | Rhythmic pulse for brain visualization |

---

## GSAP Animation Pattern

To prevent SSR flash (content briefly visible before JS executes), all GSAP animations use the `opacity-0` CSS pattern:

```svelte
<!-- Element starts invisible -->
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

This avoids `gsap.from()` which causes visible flash on SSR-rendered content. All animated pages follow this pattern.

---

## Card Type Detection

The frontend includes a zero-dependency card type detection utility at `src/lib/utils/card.ts`:

| Feature | Implementation |
|---------|---------------|
| Type Detection | Regex patterns for Visa, Mastercard, Amex, Discover, JCB, UnionPay |
| Validation | Luhn algorithm for card number checksum |
| Formatting | Auto-spacing with max digits per card type (16–19) |
| Expiry | MM/YY formatting with month range validation (01–12) |
| CVC | 3–4 digit validation based on card type |
| Phone | International phone validation for mobile money |
| Visuals | SVG card brand logos rendered inline |

---

## Development

### Commands

```bash
npm run dev          # Start dev server (HMR at localhost:5173)
npm run build        # Production build to build/
npm run preview      # Preview production build locally
npm run check        # Type-check with svelte-check
```

### Project Structure

```
Neuralpulse-engine/
├── src/
│   ├── app.html                # HTML shell (dark theme, fonts, meta)
│   ├── app.css                 # Tailwind directives + custom classes
│   ├── app.d.ts                # Ambient type declarations
│   ├── hooks.server.ts         # Server hooks — auth, CSP headers
│   ├── lib/
│   │   ├── components/         # Svelte components by domain
│   │   │   ├── analysis/       # Analysis UI components
│   │   │   ├── brain/          # 3D brain visualization
│   │   │   ├── charts/         # Chart.js wrappers
│   │   │   ├── editor/         # Rich text editor
│   │   │   ├── effects/        # Particles, orbs, backgrounds
│   │   │   ├── home/           # Landing page sections
│   │   │   ├── layout/         # Navbar, sidebar, footer
│   │   │   └── ui/             # Generic UI primitives
│   │   ├── editor/             # Editor utilities
│   │   ├── i18n/               # Internationalization
│   │   ├── stores/             # Svelte writable stores (theme, etc.)
│   │   ├── types/              # TypeScript type definitions
│   │   └── utils/              # API client, validation, helpers
│   └── routes/                 # File-based routing
│       ├── +layout.svelte      # Root layout (sidebar, navbar, effects)
│       ├── +layout.server.ts   # Server-side layout data
│       ├── +page.svelte        # Landing page
│       ├── api/                # API proxy server routes
│       ├── ab-test/
│       ├── analyze/
│       ├── brain-explorer/
│       ├── copywriting/
│       ├── dashboard/
│       ├── editor/
│       ├── history/
│       ├── login/
│       ├── logout/
│       ├── payment/
│       ├── pricing/
│       ├── privacy/
│       ├── register/
│       ├── results/
│       ├── settings/
│       ├── terms/
│       └── thumbnail/
├── static/                     # Static assets (favicon, etc.)
├── .env.example                # Environment variable template
├── package.json                # Dependencies and scripts
├── svelte.config.js            # SvelteKit config (Vercel adapter)
├── vite.config.ts              # Vite bundler config
├── tailwind.config.ts          # Tailwind with neural design tokens
├── postcss.config.js           # PostCSS (Tailwind + autoprefixer)
├── tsconfig.json               # TypeScript config
└── vercel.json                 # Vercel deployment config
```

### CSP Headers

Content Security Policy is set in `src/hooks.server.ts`:

**Development:** Allows `'unsafe-inline'` and `'unsafe-eval'` for HMR, WebSocket connections to localhost.

**Production:** Stricter policy — `script-src 'self' 'unsafe-inline'` (required for SvelteKit hydration scripts), Google Fonts allowed for styles/fonts.

### Gitignore

The `.gitignore` excludes:
- `node_modules/` — npm dependencies
- `.svelte-kit/` — SvelteKit build cache
- `build/` / `dist/` — Production build output
- `.env`, `.env.*.local` — Secrets
- `.vercel/` — Vercel deploy artifacts
- `*.log` — Server logs

---

## Deployment

### Vercel (Production)

The frontend deploys to Vercel automatically via Git integration. The `svelte.config.js` uses `@sveltejs/adapter-vercel` with Node.js 20 runtime and ISR (60s cache).

#### Required Environment Variables

Set in Vercel dashboard → Settings → Environment Variables:

| Variable | Value | Purpose |
|----------|-------|---------|
| `API_URL` | `https://neuralpulse-engine-backend-production.up.railway.app` | Backend API URL |
| `ISR_BYPASS_TOKEN` | *(optional, random hex)* | ISR cache bypass for on-demand revalidation |

#### Deployment Commands

```bash
npm run build                    # Production build
npx vercel --prod                # Deploy via CLI
```

Or connect the GitHub repo to Vercel for automatic deployments on push.

#### Caching Strategy

| Asset | Cache Duration |
|-------|---------------|
| `/_app/immutable/*` | 1 year (immutable) |
| Pages (HTML) | 60s ISR (stale-while-revalidate) |
| API responses | No cache (dynamic) |

#### Security Headers

Set via `vercel.json` and `hooks.server.ts`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- `Content-Security-Policy` (see CSP section above)

---

## Links

- **Frontend GitHub**: [https://github.com/Joeltabe/Neuralpulse-engine](https://github.com/Joeltabe/Neuralpulse-engine)
- **Backend GitHub**: [https://github.com/Joeltabe/neuralpulse-engine-backend](https://github.com/Joeltabe/neuralpulse-engine-backend)
- **Frontend (Vercel)**: [https://neuralpulse-engine.vercel.app](https://neuralpulse-engine.vercel.app)
- **Backend (Railway)**: `https://neuralpulse-engine-backend-production.up.railway.app`
