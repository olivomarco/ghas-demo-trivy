# GHAS + Trivy: container image vulnerability demo

This repo shows how **GitHub Advanced Security** and **Trivy** work together to find, gate,
triage, fix and continuously monitor vulnerabilities inside a **Docker image**.

> ⚠️ The app and `Dockerfile` are **intentionally insecure**. Do not deploy them.

## What's inside

| Path | Purpose |
|---|---|
| `app/` | Tiny Express app with outdated npm dependencies (axios, express, jsonwebtoken, lodash) |
| `Dockerfile` | Vulnerable image: EOL `node:16` (Debian 10), runs as root, `ADD`, no `HEALTHCHECK` |
| `.github/workflows/container-scan.yml` | Builds the image, then Trivy **image** + **Dockerfile** scans → SARIF → code scanning. Runs on PR, push, **nightly** and manually |
| `.github/workflows/sbom.yml` | Trivy SBOM → **Dependency Graph** (dependency submission API) + CycloneDX artifact |
| `.trivyignore` | Accepted risk with justification, owner and **expiry** |
| `vex.openvex.json` | OpenVEX `not_affected` statement (exploitability-based suppression) |
| `.github/copilot-instructions.md` | Guidance for Copilot coding agent when it fixes the image |
| `scripts/setup-repo.sh` | Enables security features and creates the **merge-blocking ruleset** |
| `scripts/create-demo-pr.sh` | Opens the "bad PR" that adds a CRITICAL vulnerability |
| `scripts/map-trivy-sarif.py` | Maps image application npm findings to lockfile version lines so GitHub can gate PRs |
| `docs/DEMO.md` | Step-by-step 30-minute demo script |
| `docs/solution/` | Reference hardened `Dockerfile` + dependencies (the "after" state) |

## Lifecycle covered

```
 PR gate ──► Triage ──► Fix (Copilot) ──► SBOM / Dependency graph ──► Nightly re-scan
   ▲                                                                       │
   └──────────────────────── new CVEs raise new alerts ◄───────────────────┘
```

## Setup

1. Push this repo to GitHub (public, or private with GitHub Code Security enabled).
2. Run `scripts/setup-repo.sh` (requires `gh` with admin rights on the repo).
3. Wait for the first **Container scan (Trivy)** and **SBOM (Trivy)** runs on `main` to finish.
   This creates the baseline alerts in the Security tab.
4. Optional: enable **Copilot coding agent** for the repo so you can assign the fix to Copilot.

### How the PR gate works

Trivy's image SARIF points at files inside the container, not files changed by a PR.
Before upload, application npm findings are mapped to their installed-version lines in
`app/package-lock.json`. This lets GitHub's code scanning ruleset block new HIGH/CRITICAL
alerts on changed dependency lines while keeping the existing baseline visible.
Base-image findings retain their original locations: they remain visible in code scanning,
but this source mapping does not provide PR merge protection for OS or bundled npm packages.
The scan jobs report findings without failing; the **Trivy code scanning check** enforces the gate.
After installing or changing this mapping, run the scan on `main` to establish the mapped
baseline before scanning demo PRs.

## Numbers you can expect (scan date: Nov 2026)

| Image | HIGH + CRITICAL | Dockerfile misconfigs |
|---|---|---|
| `Dockerfile` (node:16 / Debian 10) | ~430 | 3 (DS-0002 root, DS-0005 ADD, DS-0026 HEALTHCHECK) |
| `docs/solution/Dockerfile` (distroless nodejs24) | 2 (unfixed OpenSSL, no patch yet) | 0 |

## Run locally

```bash
docker build -t trivy-demo .
trivy image --severity HIGH,CRITICAL --vex vex.openvex.json trivy-demo
trivy config .
```
