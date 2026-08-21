# Security

Security fixes target the latest GitHub release and the current default branch.
Older prereleases may be replaced instead of patched.

## Release integrity

Official archives and the Windows installer are produced by
`.github/workflows/release.yml`. Published releases include SHA-256 checksum
files and GitHub Artifact Attestations. Verification commands and the release
process are documented in [RELEASE.md](RELEASE.md#verify-a-download).

The Windows application is not Authenticode-signed. A checksum verifies file
integrity and an attestation verifies GitHub Actions provenance; neither makes
Windows display a verified publisher.

## Antivirus reports

Horticalc packages Python as a local desktop application and starts a FastAPI
service bound to `127.0.0.1`. Unsigned PyInstaller applications can trigger
reputation or heuristic warnings.

When reporting a detection, include the release URL, file name, SHA-256 hash,
operating system, security product and version, exact detection text, and when
the warning occurred. A screenshot or relevant event-log excerpt is helpful.

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/onethree7/Horticalc/security/advisories/new).
Include reproduction steps, the affected Horticalc version, operating system,
distribution method, and expected security boundary.
