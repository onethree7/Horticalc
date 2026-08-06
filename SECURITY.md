# Security

Status: `current-state`.

Security and release verification notes for Horticalc.

## Supported Releases

Security fixes target the latest GitHub release and the current default branch.
Older prereleases may be replaced instead of patched.

## Release Integrity

Horticalc release archives are built by `.github/workflows/release.yml`.
The release workflow:

- builds platform archives with PyInstaller onedir packaging;
- smoke-tests the packaged application with `HORTICALC_NO_GUI=1`;
- publishes a `.sha256` checksum file beside each release archive;
- creates GitHub Artifact Attestations for each archive and checksum file.

The Windows executable is not Authenticode code-signed. Git commit signing, tag
signing, checksums, and GitHub Artifact Attestations prove source and build
provenance, but they do not make Windows show a verified publisher for
`Horticalc.exe`.

## Verify A Download

For the exact checksum and attestation commands, see the release verification
section in [docs/release_build.md](docs/release_build.md).

## Antivirus False Positives

Horticalc is an open-source local calculator packaged as a portable app. The
launcher starts a FastAPI server bound to `127.0.0.1`, opens a native pywebview
window, and writes runtime data only below the extracted app folder. The runtime
model is documented in `docs/release_build.md` and implemented in
`src/horticalc/launcher.py` and `src/horticalc/paths.py`.

Unsigned PyInstaller-built Windows executables can trigger reputation or
heuristic detections. If a vendor flags a release archive or executable, please
include the GitHub release URL, file SHA-256, and this repository URL in a
false-positive report.

If you report an antivirus or operating-system warning to this project, include
the exact environment and detection details:

- operating system and version, for example Windows 11 24H2;
- security product name and version, for example Microsoft Defender,
  SentinelOne, Avast, or another product;
- whether the warning appeared on download, extraction, first launch, or after
  the app was already running;
- exact warning text, detection name, quarantine reason, or event-log text;
- screenshot of the warning when possible;
- file name and SHA-256 hash of the flagged file;
- download source, such as the GitHub release URL.

## Report A Security Issue

Please use GitHub's private vulnerability reporting. Include reproduction steps,
affected version, operating system, and affected distribution.
