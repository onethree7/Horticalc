# Horticalc

Horticalc is a fertilizer calculator with a Python backend and a browser-based UI, focused on stoichiometrically correct nutrient calculations for recipes and targets.

## Run

- **Portable app (recommended):**
  - Windows: double-click `Horticalc.exe` in the extracted folder.
  - Linux: run `./horticalc` in the extracted folder.
  - See [docs/release_build.md](docs/release_build.md) for build/release details.
- **Developer run (UI + API):**
  - Create a virtualenv, install requirements, then run:
    ```bash
    python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
    ```

## Documentation

- Deep-dive docs: [docs/index.md](docs/index.md)
- Contributor/automation guide: [AGENTS.md](AGENTS.md)
