# Contributing to NeuralPulse Engine

## Getting Started

1. Fork the repository.
2. Clone your fork: `git clone https://github.com/your-username/Neuralpulse-engine.git`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy and configure environment: `cp .env.example .env`
5. Start the server: `python run.py`

## Code Style

- Python: Follow PEP 8. Use type hints for all function signatures.
- Imports: Group as standard library, third-party, local (separated by blank lines, sorted alphabetically).
- No commented-out code — delete it.
- No debug print statements — use the `logging` module.

## Branching

- `main` — stable, deployable.
- Feature branches: `feat/<short-description>`
- Fix branches: `fix/<short-description>`

## Commit Messages

Write concise, descriptive commit messages. Prefix with the module:

```
api: add thumbnail export endpoint
neuromarketing: fix ROI index out of bounds in tribe adapter
frontend: add loading spinner to dashboard
```

## Pull Request Process

1. Ensure the server starts without errors (`python run.py`).
2. Update documentation (README, API docs) if you change behavior.
3. Keep PRs focused — one feature or fix per PR.
4. Reference any related issues.

## Development Notes

- The `USE_REAL_TRIBE=false` mode uses simulation, so you don't need a GPU to develop or test.
- The database auto-falls back to SQLite if Neon PostgreSQL is unavailable.
- Tests are not yet set up. If adding test coverage, place tests in a `tests/` directory mirroring the source structure.

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file, or if absent, default to MIT).
