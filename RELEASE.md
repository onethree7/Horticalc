# Releases

Horticalc uses PyInstaller onedir packages. Windows publishes the onedir build
through a per-user installer and a portable ZIP; Linux publishes a portable
archive.

## Artifacts

| Platform | Artifact | Use |
| --- | --- | --- |
| Windows | `horticalc-vX.Y.Z-windows-setup.exe` | Recommended user download |
| Windows | `horticalc-vX.Y.Z-windows.zip` | Portable application directory |
| Linux x86_64 | `horticalc-vX.Y.Z-linux.tar.gz` | Portable application directory |

`Horticalc.exe` is not a standalone binary: it requires the other files in its
onedir application folder. The setup installs that folder under
`%LocalAppData%\Programs\Horticalc` without elevation. Updates and uninstall
preserve `user/`; uninstall removes application files and `logs/`.

## Build locally

Install the release environment using the constraints file.

Linux:

```bash
PIP_CONSTRAINT=constraints-release.txt python -m pip install . pyinstaller
chmod +x scripts/packaging/build_linux.sh
./scripts/packaging/build_linux.sh
```

Windows PowerShell:

```powershell
$env:PIP_CONSTRAINT = "constraints-release.txt"
python -m pip install . pyinstaller
.\scripts\packaging\build_windows.ps1
.\scripts\packaging\build_windows_installer.ps1
```

The installer step requires Inno Setup 6. Set `ISCC_PATH` when `ISCC.exe` is not
in its standard installation directory. Build behavior is owned by
`scripts/packaging/horticalc.spec`, the platform build scripts, and
`scripts/packaging/horticalc.iss`.

The Linux application is written to `dist/horticalc/`; the Windows application
is written to `dist/Horticalc/`; and the installer is written to the repository
root. Launch `dist/horticalc/horticalc` or
`dist/Horticalc/Horticalc.exe` and perform the applicable checks from
[Before publishing](#before-publishing). A local build has no published checksum or
attestation and is not an official release artifact.

## Release workflow

`.github/workflows/release.yml` builds both platforms, smoke-tests each packaged
application, verifies the Linux bundle boundary, exercises the Windows
installer, creates SHA-256 files and GitHub Artifact Attestations, and publishes
tagged assets only after required jobs pass.

Before tagging a release:

1. Update the package version in `src/horticalc/__init__.py`.
2. Update the accepted tag and versioned release-note path in
   `.github/workflows/release.yml`.
3. Add the matching `.github/release-notes/v<version>.md`.
4. Run `python scripts/check_release_version.py` and the standard test suite.
5. Create the exact `v<version>` tag only after the reviewed commit is ready.

Manual workflow builds use the short commit identifier in artifact names.
Tagged builds use the release tag.

## Verify a download

Compare the downloaded file with its published checksum.
Download the matching `horticalc-vX.Y.Z-windows-setup.exe.sha256`,
`horticalc-vX.Y.Z-windows.zip.sha256`, or Linux `.sha256` file beside the
artifact before running these commands.

Windows PowerShell:

```powershell
$file = ".\horticalc-vX.Y.Z-windows-setup.exe"
$expected = (Get-Content "$file.sha256").Split()[0]
$actual = (Get-FileHash -Algorithm SHA256 $file).Hash
if ($actual -ne $expected) { throw "Checksum mismatch: $file" }

$file = ".\horticalc-vX.Y.Z-windows.zip"
$expected = (Get-Content "$file.sha256").Split()[0]
$actual = (Get-FileHash -Algorithm SHA256 $file).Hash
if ($actual -ne $expected) { throw "Checksum mismatch: $file" }
```

Linux:

```bash
sha256sum -c horticalc-vX.Y.Z-linux.tar.gz.sha256
```

Verify GitHub Actions provenance with the GitHub CLI:

```bash
gh attestation verify horticalc-vX.Y.Z-windows-setup.exe --repo onethree7/Horticalc
gh attestation verify horticalc-vX.Y.Z-windows.zip --repo onethree7/Horticalc
gh attestation verify horticalc-vX.Y.Z-linux.tar.gz --repo onethree7/Horticalc
```

Checksums and attestations do not provide Authenticode publisher identity.

## Before publishing

Automated Linux GUI tests cover Ubuntu 22.04/24.04, Debian 13, and Fedora 44.
Check the release candidates once more on clean Windows 10 and 11 systems and
Linux Mint 22.3. Open Calculator and Solver, copy a result, save a preference,
launch Horticalc a second time, and confirm that closing the window stops the
application cleanly.

If you contribute to Horticalc, especially to its launcher, dependencies, or
packaging, make sure your changes do not trigger basic Windows security
heuristics. Treat a new antivirus detection or quarantine as a code or packaging
regression to investigate, never as something users should work around by
disabling protection.

The supported runtime requirements and portable ZIP recovery procedure are in
[README.md](README.md#system-requirements-and-startup-help).
