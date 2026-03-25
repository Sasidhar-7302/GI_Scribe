# Contributing to GI Scribe

Thank you for your interest in improving GI Scribe. This guide covers how to set up your development environment and submit changes.

## Development Setup

1. **Fork and clone** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Set up the Python backend**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```
4. **Set up the frontend**:
   ```bash
   cd frontend && npm install
   ```

## Code Standards

- **Python**: Follow PEP 8. Use type hints for function signatures.
- **TypeScript/React**: Use functional components with hooks. No `any` types.
- **Commits**: Use clear, descriptive commit messages in imperative mood.

## Pull Request Guidelines

1. **One feature per PR** — keep changes focused
2. **Test your changes** — run `npx next build` for frontend, verify backend starts cleanly
3. **No PHI in code** — never commit patient data, audio files, or database files
4. **Update docs** — if you change behavior, update the README

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system design. Key modules:

| Module | Purpose |
|--------|---------|
| `app/api.py` | FastAPI REST + WebSocket endpoints |
| `app/two_pass_summarizer.py` | Clinical note generation |
| `app/preference_learner.py` | Self-learning preference extraction |
| `frontend/src/components/` | React UI components |

## Security

- **Never commit `config.json`** — use `config.example.json` as template
- **Never commit audio files** (`.mp3`, `.wav`)
- **Never commit `medrec.db`** — contains session data

## Questions?

Open an issue on GitHub or reach out to the maintainers.
