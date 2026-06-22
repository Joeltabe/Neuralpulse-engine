# NeuralPulse Engine — Frontend

**Brain-validated ad optimization using simulated fMRI responses via TRIBE v2.**

SvelteKit frontend deployed on Vercel. Backend lives at [neuralpulse-engine-backend](https://github.com/Joeltabe/neuralpulse-engine-backend).

---

## Tech Stack

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

```bash
npm install
npm run dev
```

The dev server starts at `http://localhost:5173`. The backend API must be running separately — set `API_URL` in `.env`:

```env
API_URL=http://localhost:8000
```

---

## Pages

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
| Payment | `/payment` | 4-step payment wizard |
| Terms | `/terms` | Terms of service |
| Privacy | `/privacy` | Privacy policy |
| Results | `/results/[id]` | Individual analysis detail view |

---

## API Proxy Pattern

SvelteKit server routes at `src/routes/api/*` proxy requests to the backend:

```
Browser → Vercel (SvelteKit SSR) → Railway (FastAPI backend)
           POST /api/auth/demo-login   →   POST /auth/demo-login
           GET  /api/analyze/video      →   GET  /analyze/video
```

The backend URL is configured via `API_URL` env var in `src/lib/utils/api.ts`.

---

## Deployment

```bash
npm run build
npm run preview
```

The frontend deploys to **Vercel** via Git integration. Set these env vars in the Vercel dashboard:

| Variable | Value |
|----------|-------|
| `API_URL` | `https://neuralpulse-engine-backend-production.up.railway.app` |
| `ISR_BYPASS_TOKEN` | *(optional)* |

---

## Project Structure

```
src/
├── app.html              # HTML shell
├── app.css               # Tailwind + custom component classes
├── hooks.server.ts       # Server hooks (auth, CSP headers)
├── lib/
│   ├── components/       # UI & layout components
│   ├── stores/           # Svelte writable stores
│   ├── types/            # TypeScript type definitions
│   ├── utils/            # API client, helpers
│   └── i18n/             # Internationalization
├── routes/               # File-based SvelteKit routing
│   ├── api/              # API proxy server routes
│   ├── +layout.svelte    # Root layout
│   ├── +page.svelte      # Landing page
│   ├── login/
│   ├── dashboard/
│   ├── analyze/
│   └── ...
└── static/               # Static assets
```
