# Security

Status: current-state security and release verification notes.

## Supported Releases

Security fixes target the latest GitHub release and the current default
branch. Older prereleases may be replaced instead of patched.

## Release Integrity

Horticalc release archives are built by `.github/workflows/release.yml`.
The release workflow:

- builds platform archives with PyInstaller onedir packaging;
- smoke-tests the packaged application with `HORTICALC_NO_BROWSER=1`;
- publishes a `.sha256` checksum file beside each release archive;
- creates GitHub Artifact Attestations for each archive and checksum file.

The Windows executable is not Authenticode code-signed. Git commit signing,
tag signing, checksums, and GitHub Artifact Attestations prove source and build
provenance, but they do not make Windows show a verified publisher for
`Horticalc.exe`.

## Verify A Download

Compare the checksum file against the downloaded archive.

Windows PowerShell:

```powershell
Get-FileHash -Algorithm SHA256 .\horticalc-vX.Y.Z-windows.zip
Get-Content .\horticalc-vX.Y.Z-windows.zip.sha256
```

Linux:

```bash
sha256sum -c horticalc-vX.Y.Z-linux.tar.gz.sha256
```

If the GitHub CLI is available, verify the build attestation against this
repository:

```bash
gh attestation verify horticalc-vX.Y.Z-windows.zip --repo onethree7/Horticalc
gh attestation verify horticalc-vX.Y.Z-linux.tar.gz --repo onethree7/Horticalc
```

## Antivirus False Positives

Horticalc is an open-source local calculator packaged as a portable app. The
launcher starts a FastAPI server bound to `127.0.0.1`, opens a local browser
window, and writes runtime data only below the extracted app folder. The
runtime model is documented in `docs/release_build.md` and implemented in
`src/horticalc/launcher.py` and `src/horticalc/paths.py`.

Unsigned PyInstaller-built Windows executables can trigger reputation or
heuristic detections. If a vendor flags a release archive or executable, please
include the GitHub release URL, file SHA-256, and this repository URL in a
false-positive report.

## Report A Security Issue

Please open a GitHub security advisory or contact the maintainer privately if
the issue should not be public yet. Include reproduction steps, affected
version, operating system, and whether the issue affects source usage,
packaged releases, or both.
