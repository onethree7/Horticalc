# Release Builds

Status: `operation-guide`.

Horticalc releases use PyInstaller onedir builds. Windows publishes that build
both through an Inno Setup installer and as a portable ZIP; Linux publishes a
portable archive. The packaged executable starts the local API, serves the
frontend, opens a native pywebview window, and writes only inside its AppRoot.

## Runtime Model

1. The launcher starts a FastAPI/uvicorn server on `127.0.0.1`.
2. The server exposes API routes and serves `frontend/` at `/`.
3. The launcher waits for `/health`.
4. The launcher opens one native pywebview window using WebView2 on Windows or GTK/WebKitGTK on Linux.
5. If the app is already running, a second launch restores and focuses the existing window.
6. Runtime writes go to `AppRoot/user/` and `AppRoot/logs/`.
7. Persistent WebView state is stored under `AppRoot/user/webview/`.
8. Runtime logs rotate at 2 MiB with two backups.

Before a packaged Windows GUI start imports pythonnet or starts the local
server, the launcher reads the `Zone.Identifier` stream on
`_internal/pythonnet/runtime/Python.Runtime.dll`. `ZoneId=3` or `ZoneId=4`
produces the portable-unblock message and exits. Source, Linux, and
`HORTICALC_NO_GUI=1` starts skip this renderer-specific check. The launcher
never changes or removes attachment metadata.

Lock ownership is claimed exclusively before uvicorn starts. Concurrent launches
wait for the owner to become healthy. Dead, malformed, or obsolete locks are
removed safely. The lock contains a random per-run token used only by the local
`/_launcher/activate` endpoint. Native window close is the lifecycle source for
server shutdown; there is no external-browser fallback.

`pyproject.toml` owns runtime dependency declarations. `constraints-release.txt` pins the complete release build environment used by CI and local release builds.
`pywebview` is pinned to `6.2.1`. The PyInstaller spec includes only the selected
platform backend and excludes Qt, PySide, CEF, MSHTML, and backends for other
operating systems. On Linux, `Analysis.exclude_system_libraries()` removes the
build host's C++ runtime, GLib, GTK, ICU, and related system libraries. The spec
also removes PyInstaller's GTK/GI runtime hooks, system typelibs, pixbuf loaders,
schemas, themes, and icons. This prevents a bundled Ubuntu GTK subset from being
mixed with WebKitGTK from the target host. Python, Horticalc, PyGObject,
NumPy/SciPy, and wheel-owned native libraries remain packaged.
Source installations are constrained to Python 3.10 through 3.13 because the
GTK dependency pinned by pywebview 6.2.1 does not support Python 3.14. Release
artifacts continue to use Python 3.11.9.

## Platform Requirements

- Windows 10/11: system-installed Microsoft WebView2 Runtime. Horticalc forces
  `edgechromium` and does not fall back to MSHTML or an external browser.
- Ubuntu 22.04/24.04, Debian 13, and Linux Mint 22.3:
  `sudo apt update && sudo apt install -y libgirepository-1.0-1 gir1.2-webkit2-4.1`.
- Fedora 44: `sudo dnf install -y webkit2gtk4.1`.
- Ubuntu 22.04/24.04, Debian 13, and Fedora 44 are tested automatically. Linux
  Mint 22.3 is a required manual VM gate. Other distributions are best effort.
- Horticalc detects `/etc/os-release` to show the matching command when
  WebKitGTK is absent. It never installs packages or invokes `sudo` itself.
- Windows 7/8/8.1 and macOS: not supported by the desktop release.

## AppRoot Layout

Windows:

```text
dist/Horticalc/
  Horticalc.exe
  _internal/
  frontend/
  data/
  recipes/
  README.txt
  LICENSE
  user/      created at runtime
    webview/ persistent WebView state
  logs/      created at runtime
```

Inno Setup installs the same layout per user under
`%LocalAppData%\Programs\Horticalc`. Its stable AppId lets later setup builds
replace shipped files in place. Updates preserve `user/`; uninstall preserves
`user/`, removes `logs/`, and removes the registered program files. The setup
does not require elevation.

Linux:

```text
dist/horticalc/
  horticalc
  _internal/
  frontend/
  data/
  recipes/
  README.txt
  LICENSE
  user/      created at runtime
    webview/ persistent WebView state
  logs/      created at runtime
```

## Build Locally

Install build requirements with the release constraints, then run the platform build script.

For the exact commands, see [commands.md](commands.md#release-build-pyinstaller).

The build scripts run PyInstaller with `scripts/packaging/horticalc.spec`, then copy `frontend/`, `data/`, and `recipes/` into the onedir app root and add the portable `README.txt` and GPLv3 `LICENSE`. The portable README states that Horticalc is independent from named manufacturers and data sources, and that bundled product data are point-in-time snapshots without warranty.

On Windows, `scripts/packaging/build_windows.ps1` also generates a version
resource with `scripts/packaging/write_windows_version_info.py`.
`scripts/packaging/build_windows_installer.ps1` then compiles
`scripts/packaging/horticalc.iss` with Inno Setup 6. CI passes the canonical
package version through `HORTICALC_VERSION`; local builds derive it from
`horticalc.__version__` unless the environment variable is explicit. The
installer build fails with an actionable message if `ISCC.exe` cannot be found.

## CI Release Workflow

`.github/workflows/release.yml` runs on:

- manual workflow dispatch
- the exact release tag `v0.6.3`

Matrix:

- Build hosts: `ubuntu-22.04` and `windows-latest`.
- Linux packaged-GUI compatibility: Ubuntu 22.04, Ubuntu 24.04, Debian 13, and
  Fedora 44 containers under Xvfb/Openbox.
- Python `3.11.9`

The Linux compatibility jobs first confirm the distro-specific missing-runtime
message without WebKitGTK, then install the documented package and find a
visible `Horticalc GUI` window with `xdotool`. Closing that window must stop the
process and server and remove the lock. Before closing it, the smoke test starts
the packaged executable a second time and verifies that the original process,
server, lock owner, and single window remain active.
`scripts/packaging/verify_linux_bundle.py` also rejects bundled
GTK/GLib/ICU/C++ system libraries, GI system data, and Qt/CEF/Chromium renderers.

The Windows job keeps `horticalc-<version>-windows.zip` and additionally builds
`horticalc-<version>-windows-setup.exe`. Its installer smoke test applies a
synthetic Internet Zone stream to the setup, silently installs it, verifies the
installed pythonnet DLL is unmarked, starts the installed headless server,
reinstalls over a user-data sentinel, and uninstalls. Program files and logs
must be removed while the sentinel remains.

`scripts/check_release_version.py` rejects a tag that does not exactly match
`v` plus `horticalc.__version__`. Manual workflow builds retain short-commit
artifact names. Tagged builds use `v0.6.3`, and release assets are published
only after every build and Linux compatibility job succeeds. The publish job
uses `.github/release-notes/v0.6.3.md` as the versioned GitHub release body so
the published description is reviewed with the code and packaging workflow.

## Release Verification

`.github/workflows/release.yml` owns checksums and GitHub Artifact Attestations
for the portable archives and Windows setup. These prove file integrity and
GitHub Actions build provenance; they are not Windows Authenticode signatures
and do not make Windows show a verified publisher for the setup or
`Horticalc.exe`.

For the exact checksum and attestation commands, see [commands.md](commands.md#release-verification).

## Portable Data Policy

`src/horticalc/paths.py` owns this policy:

- AppRoot is the repo root in dev and the executable folder in release. For a
  setup installation that folder is `%LocalAppData%\Programs\Horticalc`.
- Shipped defaults live in `data/` and `recipes/`.
- User-created and edited overrides live in `user/`.
- Rotating logs live in `logs/`.
- If AppRoot is not writable, startup fails fast with:

```text
Extract to a writable folder (e.g. Desktop/Downloads). Do not run from Program Files.
```

Do not introduce Horticalc application-data writes to OS user directories, the
registry, XDG paths, `%APPDATA%`, or `%LOCALAPPDATA%`. WebView state is directed
explicitly to `AppRoot/user/webview/`.

## Verification

Standard tests, packaging smoke, and headless smoke are in [commands.md](commands.md#run-tests) and [commands.md](commands.md#release-build-pyinstaller).

Before publishing a desktop release, run the packaged GUI on clean Windows 10
and Windows 11 VMs and on Linux Mint 22.3. Automated packaged tests cover Ubuntu
22.04/24.04, Debian 13, and Fedora 44. On each manual platform verify first start,
Calculator, Solver, clipboard, scrolling, persisted preferences, a second launch
restoring the existing window, and window close removing the server and lock.
On Windows also test with Chrome absent and before Edge has ever been opened.
Test a missing WebView2 or WebKitGTK runtime separately and require the
documented error without an MSHTML, Qt, or external-browser fallback. Compare
the printed artifact size with the previous equivalent build and investigate an
increase above 25 percent.

On Windows, also download the setup and ZIP through a browser so they receive
Mark of the Web. Require the setup-installed GUI to start normally. Require a
blocked portable extraction to show the unblock instructions before server or
WebView startup, then unblock the original ZIP, extract it again, and require a
normal GUI start. Verify an installer update preserves profiles and uninstall
preserves `user/` while deleting `logs/`.
