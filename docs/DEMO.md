# Demo script (30 minutes)

**Story:** *"Our developers ship Docker images. How do we know what's vulnerable inside them,
stop new risk from reaching `main`, and keep watching once they're shipped?"*

## Before the session

- [ ] Run `scripts/setup-repo.sh`. The ruleset **"Block merges on Trivy HIGH+ alerts"** should exist.
- [ ] `main` has a green **Container scan (Trivy)** run and a **SBOM (Trivy)** run.
- [ ] Security tab → Code scanning shows the Trivy alerts (filter `tool:Trivy`).
- [ ] Run `scripts/create-demo-pr.sh` about 10 minutes before the demo so its checks have finished.
- [ ] Optional backup: a pre-made fix PR built from `docs/solution/`, in case the coding agent is slow.

---

## 1. Setup and context (0–3 min)

- Show `Dockerfile`: `node:16` (end of life, Debian 10), root user, `ADD`, no healthcheck.
- Show `app/package.json`: dependencies pinned years ago.
- Show `.github/workflows/container-scan.yml`. Trivy runs inside GitHub Actions and SARIF is the bridge into GHAS.
  - Actions are **pinned by SHA**. This is a good moment to mention supply-chain hygiene for the scanner itself.

## 2. PR gate with SARIF (3–10 min)

- Open the PR created by `create-demo-pr.sh` (*"feat: add ejs template engine"*).
- **Checks:** the *Code scanning results / Trivy* check reports a **new CRITICAL** alert
  (CVE-2022-29078 in `ejs@3.1.6`).
- **Merge box:** the merge is **blocked by the ruleset** (code scanning merge protection, `high_or_higher`).
- Talking points:
  - Only alerts **new to this PR** block it. Existing debt on `main` doesn't stop every PR.
  - Image npm findings are mapped to changed version lines in `app/package-lock.json`.
    Raw container paths are outside the PR diff and would not block the merge.
    OS and bundled npm findings remain visible but are not covered by this source-mapped gate.
  - Two SARIF categories: `trivy-image` (what's inside the image) and `trivy-dockerfile` (how it's built).
  - The job summary has the full Trivy table for developers who don't want to leave the run.
- Close or leave the PR. *"The gate works. Now, what about the debt already on main?"*

## 3. Triage (10–15 min)

- **Security tab → Code scanning → `tool:Trivy`**. Filter by severity and open a CRITICAL alert:
  rule help, affected package, installed vs. fixed version, and the branches it affects.
- **Dismiss** an alert from the UI (*"Won't fix"* / *"Used in tests"*) with a comment.
  The dismissal is audited and appears in Security Overview.
- **Policy-as-code suppressions** (reviewable in PRs, unlike UI clicks):
  - `.trivyignore`: CVE-2019-8457 (libdb, Debian *will_not_fix*) with owner and **`exp:2027-06-30`**.
    When it expires, the alert comes back automatically.
  - `vex.openvex.json`: CVE-2022-23539 in `jsonwebtoken` is **`not_affected`** because
    `vulnerable_code_not_in_execute_path`. VEX is an industry standard, so you can also share it with customers.
- Dockerfile alerts (`trivy-dockerfile`) point to the **exact line** in the `Dockerfile`.

## 4. Fix with Copilot (15–22 min)

> Note: Copilot **Autofix** generates fixes for CodeQL alerts. For third-party tools such as Trivy,
> use the **Copilot coding agent**.

- Create an issue (or start from a Trivy alert) and **assign it to Copilot**. Suggested prompt:

  > Harden the container image to eliminate the Trivy HIGH/CRITICAL findings: move to a current
  > LTS Node.js base with a multi-stage build and a distroless non-root runtime, add a HEALTHCHECK,
  > replace ADD with COPY, and upgrade the vulnerable npm dependencies in app/.

- Copilot follows `.github/copilot-instructions.md` (distroless, non-root, no new suppressions).
- On its PR, the Container scan shows **alerts fixed** and the code scanning check is green.
- Reference result in `docs/solution/`: **~430 → 2** HIGH/CRITICAL. The remaining 2 are OpenSSL CVEs
  with **no fix available yet** (talking point: `ignore-unfixed` vs. visibility).
- Merge. On `main` the alerts move to **Closed** with no manual work.

## 5. SBOM and Dependency Graph (22–26 min)

- **Actions → SBOM (Trivy)** run → download the **CycloneDX** artifact (for compliance and customer requests).
- **Insights → Dependency graph**: there's a snapshot detected by `trivy` for the *image* in addition to the
  `package-lock.json` manifest. It includes packages that only exist in the image, such as the npm CLI's
  bundled modules in `/usr/local/lib/node_modules`.
- **Security → Dependabot**: alerts on those submitted packages, so the image contents now go through
  the same Dependabot workflow.
  - Caveat: Dependabot covers language ecosystems (npm etc.). **OS packages (deb/apk)** are covered by
    the Trivy code scanning alerts.

## 6. Continuous monitoring (26–30 min)

- `container-scan.yml` also runs on `schedule: "0 3 * * *"`.
- Message: *"The image didn't change, but the world did."* New CVEs are published every day. The nightly
  run rescans `main` and **opens new alerts** with no commit needed. Show the run history with the `schedule` trigger.
- Wrap up in **Security Overview**: the same Trivy alerts roll up across every repo in the org.

---

## Backup / Q&A

| Question | Answer |
|---|---|
| Scan the image in the registry instead of rebuilding? | Yes: `image-ref: ghcr.io/org/app:tag`, with a `docker login` step first. |
| Why Trivy and not only Dependabot? | Dependabot doesn't cover OS packages or the final image. Trivy scans what actually ships. |
| Too many alerts? | Use `severity`, `ignore-unfixed: true`, VEX and `.trivyignore` with expiry. Start with CRITICAL only. |
| Fail the build in CI too? | Add a Trivy step with `exit-code: 1`. The ruleset approach is preferred because it only blocks **new** risk. |
| Alerts per image when there are many images? | Use a distinct SARIF `category` per image, e.g. `trivy-image-api`, `trivy-image-web`. |
