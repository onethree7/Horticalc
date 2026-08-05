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

The desktop GUI supports Windows 10/11 with the Microsoft WebView2 Runtime. The
Linux x86_64 release uses the system GTK 3/WebKitGTK 4.1 runtime and is tested
on Ubuntu 22.04/24.04, Debian 13, Fedora 44, and manually on Linux Mint 22.3.
Install the Linux runtime before starting Horticalc:

```bash
# Ubuntu, Debian, and Linux Mint
sudo apt update && sudo apt install -y gir1.2-webkit2-4.1

# Fedora
sudo dnf install -y webkit2gtk4.1
```

Horticalc runs in its own native window; an installed Edge, Chrome, or Chromium
browser is not required.
Source installs currently support Python 3.10 through 3.13.

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
