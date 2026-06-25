# NeuralPulse Engine

<p align="center">
  <strong>Brain-Validated Ad Optimization</strong><br/>
  <em>See what your audience's subconscious mind actually thinks about your creative</em>
</p>

<p align="center">
  <a href="#problem"><strong>Problem</strong></a> •
  <a href="#solution"><strong>Solution</strong></a> •
  <a href="#features"><strong>Features</strong></a> •
  <a href="#quick-start"><strong>Quick Start</strong></a> •
  <a href="#tech-stack"><strong>Tech Stack</strong></a>
</p>

---

## Problem

### Marketing is flying blind on creative performance

Most marketing platforms measure **surface metrics only**: clicks, views, watch time, conversion rates. They tell you *what* people do, but not *why* — or whether your creative actually captures attention, triggers emotional reward, or creates lasting memories.

**The result?**
- Ad creatives that "look good" fail in market
- Expensive creative production with no directional feedback
- Copywriting A/B tests that take weeks
- Thumbnail testing by trial-and-error
- No scientific framework to explain campaign impact beyond clicks

### Why this matters

95% of purchasing decisions occur subconsciously (Zaltman, 2003). Your audience's emotional, reward, and memory systems drive behavior — but traditional analytics ignore all three.

---

## Solution

**NeuralPulse Engine** is a computational neuromarketing platform that makes subconscious creative impact **visible, measurable, and actionable**.

Upload your ad creative (video, audio, or text), and NeuralPulse:
1. **Simulates fMRI-like brain response** using TRIBE v2 neuroscience models
2. **Measures three core dimensions**:
   - **Attention** — Does it capture and hold focus? (Dorsal attention network)
   - **Dopamine reward** — Does it trigger emotional engagement? (Ventral striatum, vmPFC)
   - **Memory encoding** — Will it stick? (Hippocampus, PCC, DLPFC)
3. **Generates actionable insights**:
   - Neural heatmaps showing regional brain activation
   - Temporal engagement curves revealing dropoff points
   - ROI activation matrices across 18 brain regions
   - Statistical A/B comparisons (t-test, Cohen's d)
   - Copy optimization across 9 persuasion framings
   - AI thumbnail generation with predicted CTR

**Result:** Teams can validate ad concepts, compare variants, and optimize messaging *before* launch — grounded in neuroscience, not guesswork.

---

## Features

### Core Workflows

| Workflow | What It Does | Time | Outcome |
|----------|-------------|------|---------|
| **Neural Analysis** | Upload 1 ad creative → Get full brain response (attention, dopamine, memory scores + temporal curves + ROI heatmaps) | ~30s | Single-variant baseline |
| **A/B Testing** | Compare 2+ variants with statistical significance (t-test, Cohen's d, Bonferroni correction) | ~2min | Data-driven winner + effect sizes |
| **Copywriting** | Test same ad with 9 different persuasion framings (reason, emotion, urgency, social proof, etc.) | ~1min | Best-performing message angle |
| **Thumbnail Generator** | AI generates variations → NeuralPulse predicts CTR for each → Pick winners | ~45s | Predicted best-performing thumbnail |
| **Brain Explorer** | Interactive 3D brain visualization → Switch activation modes (attention/dopamine/memory) → Drill into individual ROIs | Exploration | Understand neuroscience |

### Dashboard

- **Recent analyses** with neural grades (A+ to F)
- **Token management** (pay-as-you-go model)
- **Quick action buttons** to launch any workflow
- **Activity tracking** — see your analysis trends over time

### Visualizations

- **3D brain heatmaps** with realistic gray/white matter and activation overlays
- **Temporal engagement curves** showing attention over time
- **ROI activation matrix** — 18 brain regions × 3 dimensions
- **Statistical comparison charts** — variant-vs-variant side-by-side
- **Virality scorer** — 5 predictive factors for social sharing

---

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- Backend running (see [Backend Repo](https://github.com/Joeltabe/neuralpulse-engine))

### Installation

```bash
# Clone this repo
git clone https://github.com/Joeltabe/Neuralpulse-engine.git
cd Neuralpulse-engine

# Install dependencies
npm install

# Start dev server
npm run dev -- --host
```

Open `http://localhost:5174`

### Environment Variables

Create `.env.local`:
```env
PUBLIC_API_BASE=http://localhost:8000
VITE_DEMO_MODE=false
```

---

## Tech Stack

### Frontend (This Repo)
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Framework** | SvelteKit 2 | SSR, server routes, file-based routing |
| **Language** | TypeScript | Type safety |
| **Styling** | Tailwind CSS | Rapid UI development |
| **3D Visualization** | Three.js | Brain mesh, real-time activation overlays |
| **Charts** | Chart.js | Temporal analytics, A/B comparisons |
| **Animations** | GSAP | Smooth transitions, scroll triggers |
| **State** | Svelte stores | Reactive state management |
| **Forms** | SvelteKit forms | Progressive form handling |

### Backend (Separate Repo)
| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API** | FastAPI (Python) | REST endpoints, async processing |
| **Brain Simulation** | TRIBE v2 | fMRI-like cortical activation models |
| **Database** | PostgreSQL + SQLAlchemy | User data, analysis history, token ledger |
| **Image Gen** | Hugging Face Inference API | AI thumbnail generation |
| **Hosting** | Railway (Docker) | Containerized deployment |

### Deployment
- **Frontend:** Vercel (auto-deploy from GitHub)
- **Backend:** Railway.app (Docker + Python environment)

---

## Architecture

### Data Flow

```
User uploads ad creative
        ↓
Frontend (SvelteKit) receives file
        ↓
SvelteKit API route (server-side proxy)
        ↓
FastAPI backend
        ↓
1. Extract features (video/audio/text preprocessing)
2. TRIBE v2 brain simulation
3. Compute neural scores & activation maps
4. Save to PostgreSQL
        ↓
Return results to frontend
        ↓
Three.js renders 3D brain heatmap
Chart.js renders temporal engagement
UI displays ROI matrix, scores, recommendations
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **SvelteKit server routes** | Backend stays hidden; browsers never hit backend directly. All API calls proxied through `/api/*` routes. |
| **Progressive enhancement** | Forms work server-side; JavaScript enhances interactivity. Graceful degradation. |
| **Real-time progress** | Server-sent events (SSE) stream analysis progress to the browser. No polling. |
| **Three.js for brain** | GPU-accelerated 3D mesh with real-time vertex coloring for activation updates. |
| **Token-based billing** | Pay-as-you-go model. Each analysis consumes tokens; users buy in bulk. |

---

## Project Structure

```
src/
├── routes/
│   ├── /                          # Landing page
│   ├── /login, /register          # Auth
│   ├── /dashboard                 # Home hub
│   ├── /analyze                   # Single creative analysis
│   ├── /ab-test                   # Multi-variant testing
│   ├── /copywriting               # Message optimization
│   ├── /thumbnail                 # AI thumbnail generation
│   ├── /brain-explorer            # Interactive 3D brain
│   ├── /history                   # Analysis history
│   ├── /results/[id]              # Detailed result view
│   └── /api/
│       ├── /analyze/video|audio|text
│       ├── /ab-test/compare
│       ├── /thumbnail/generate
│       └── /history
├── lib/
│   ├── components/
│   │   ├── brain/
│   │   │   └── BrainViewer.svelte       # 3D brain mesh + activation
│   │   ├── charts/
│   │   │   ├── EngagementChart.svelte   # Temporal activation curve
│   │   │   └── ComparisonChart.svelte   # A/B variant comparison
│   │   └── ui/
│   │       ├── Card.svelte
│   │       ├── Button.svelte
│   │       └── ScoreGauge.svelte
│   ├── stores/
│   │   ├── auth.ts                      # User session, tokens
│   │   ├── analysis.ts                  # Current analysis state
│   │   └── theme.ts                     # Dark/light mode
│   └── utils/
│       ├── api.ts                       # API client
│       └── format.ts                    # Score formatting
└── app.html                             # Root template
```

---

## What's Missing / Roadmap

### High Priority
- [ ] **Real-time progress streaming** — Backend status updates via SSE (currently: polling)
- [ ] **Export to PDF** — Generate professional reports with branding
- [ ] **Batch analysis** — Upload 10+ creatives at once
- [ ] **Webhook callbacks** — POST results to external tools (Slack, email, CRM)
- [ ] **API documentation** — OpenAPI spec for headless integrations

### Medium Priority
- [ ] **Custom ROI definitions** — Users define their own brain regions
- [ ] **Historical trend analysis** — See how neural scores improve across iterations
- [ ] **Team collaboration** — Share analyses, add comments
- [ ] **Multi-language support** — Localize UI + copy analysis to non-English
- [ ] **Mobile app** — React Native companion for on-the-go analysis review

### Nice-to-Have
- [ ] **Predictive scoring** — ML model to predict real-world CTR/conversion from neural scores
- [ ] **Competitor benchmarking** — Compare your ad against industry benchmarks
- [ ] **Video annotation** — Frame-by-frame neural breakdown with hotspot timeline
- [ ] **Marketplace** — Pre-analyzed ad library, trending creative templates

---

## Getting Involved

### Developers

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Follow the code style (ESLint + Prettier)
4. Add tests for new components
5. Submit a pull request

### Running Tests

```bash
npm run test
npm run test:watch
```

### Linting & Formatting

```bash
npm run lint
npm run format
```

---

## Deployment

### Frontend (Vercel)
- Automatic deployments on every push to `main`
- Environment variables via Vercel dashboard
- Analytics, edge caching included

### Backend (Railway)
- Docker image pushed to Railway registry
- PostgreSQL database provisioned automatically
- Health checks and auto-restart on failure

### Local Testing
```bash
# Terminal 1: Frontend
npm run dev

# Terminal 2: Backend (see backend repo for setup)
python run.py
```

---

## Links

- **Live Demo:** https://neuralpulse-engine.vercel.app
- **Backend Repo:** https://github.com/Joeltabe/neuralpulse-engine
- **Docs:** [Full documentation](./docs/README.md)
- **Issues:** [GitHub Issues](https://github.com/Joeltabe/Neuralpulse-engine/issues)

---

## License

MIT — See [LICENSE](./LICENSE) for details.

---

## Citation

If you use NeuralPulse Engine in research or production, please cite:

```bibtex
@software{neuralpulse2025,
  title={NeuralPulse Engine: Computational Neuromarketing Platform},
  author={Tabe, Joel},
  year={2025},
  url={https://github.com/Joeltabe/Neuralpulse-engine}
}
```

---

## Support

- **Questions?** Open an issue
- **Bug report?** Include OS, browser, and error stack
- **Feature request?** Describe the use case

---

**Made with ❤️ by neuromarketing enthusiasts**
