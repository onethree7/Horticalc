# Horticalc

Horticalc is a local, open-source horticultural fertilizer calculator. It
combines fertilizer composition, water composition, batch size, and optional
reverse-osmosis mixing to calculate the nutrient profile of a solution, and its
solver can work backwards from nutrient targets to suggest fertilizer doses.

## Quick Start

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m horticalc.launcher
```

On Windows, replace `./.venv/bin/python` with `.\.venv\Scripts\python.exe`.

Download the latest release archive from the [releases page](https://github.com/onethree7/Horticalc/releases), extract it to a writable folder, and run `Horticalc.exe` (Windows) or `./horticalc` (Linux).

## Documentation

- [Quickstart](docs/quickstart.md)
- [User guide](docs/user_guide.md)
- [CLI reference](docs/cli_reference.md)
- [Commands](docs/commands.md)
- [Development guide](docs/development.md)
- [Architecture](docs/architecture.md)
- [API reference](docs/api_reference.md)
- [Data model](docs/data_model.md)
- [Release builds](docs/release_build.md)

See [docs/index.md](docs/index.md) for the full map and [docs/documentation_architecture.md](docs/documentation_architecture.md) for the docs charter.

## License

Copyright © 2026 Horticalc contributors.

Horticalc is free software licensed under the GNU General Public License,
version 3 or (at your option) any later version. See [LICENSE](LICENSE).
