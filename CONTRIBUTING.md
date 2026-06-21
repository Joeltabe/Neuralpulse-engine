# Contributing to NeuralPulse Engine

## Getting Started

### Backend Setup

1. Fork the repository.
2. Clone your fork: `git clone https://github.com/your-username/Neuralpulse-engine.git`
3. Create and activate a virtual environment: `python -m venv .venv && source .venv/bin/activate`
4. Install Python dependencies: `pip install -r requirements.txt`
5. Copy and configure environment: `cp .env.example .env`
6. Start the API server: `python run.py`

### Frontend Setup

1. Ensure Node.js 18+ and npm are installed.
2. Install dependencies: `npm install`
3. Start the dev server: `npm run dev`

Run both servers simultaneously for full-stack development.

## Code Style

### Python
- Follow PEP 8. Use type hints for all function signatures.
- Imports: Group as standard library, third-party, local (separated by blank lines, sorted alphabetically).
- No commented-out code — delete it.
- No debug print statements — use the `logging` module.

### TypeScript / Svelte
- Use strict TypeScript (`strict: true` in tsconfig.json).
- Prefer Svelte 5 runes (`$state`, `$derived`, `$effect`) over stores where appropriate.
- Follow SvelteKit file-based routing conventions.
- Use the existing Tailwind design tokens (neural-, dopamine-, memory-, surface-).

## Branching

- `main` — stable, deployable.
- Feature branches: `feat/<short-description>`
- Fix branches: `fix/<short-description>`
- Frontend-only branches: `ui/<short-description>`

## Commit Messages

Write concise, descriptive commit messages. Prefix with the module:

```
api: add thumbnail export endpoint
neuromarketing: fix ROI index out of bounds in tribe adapter
frontend: add loading spinner to dashboard
api/routers/analysis: add graceful brain_viz import fallback
```

## Pull Request Process

1. Ensure the API server starts without errors (`python run.py`).
2. Ensure the frontend builds without errors (`npm run build`).
3. Type-check the frontend (`npm run check`).
4. Update documentation (README, API docs) if you change behavior.
5. Keep PRs focused — one feature or fix per PR.
6. Reference any related issues.

## Development Notes

- The `USE_REAL_TRIBE=false` mode uses simulation, so you don't need a GPU to develop or test.
- The database auto-falls back to SQLite if Neon PostgreSQL is unavailable.
- Tests are not yet set up. If adding test coverage, place tests in a `tests/` directory mirroring the source structure.
- The frontend proxies API requests; the backend must be running separately during frontend dev.
- Generated files (brain_viz HTML, thumbnails, database, logs) are gitignored.
- The frontend `/payment` page supports mobile money (Orange Money, MTN MoMo) and Stripe card. Test with the demo package endpoint via `/billing/packages`.
- Card type detection (`src/lib/utils/card.ts`) runs client-side with zero dependencies. No API call is needed for validation.
- GSAP animations must use `opacity-0` CSS classes + `gsap.to()` — never `gsap.from()` — to prevent SSR content flash.
- Allowed billing proxy actions are maintained in `src/lib/utils/validation.ts`. When adding a new billing endpoint, add it to `ALLOWED_BILLING_ACTIONS`.
- The billing proxy at `src/routes/api/billing/[action]/+server.ts` passes backend status codes through. A 402 status means insufficient tokens.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file, or if absent, default to MIT).
