# Copilot instructions

This repository demonstrates GitHub Advanced Security with Trivy container scanning.

When fixing container vulnerabilities or Trivy alerts:

- Prefer a current LTS Node.js base image (e.g. `node:24-alpine`) and, for the runtime stage,
  a minimal image such as `gcr.io/distroless/nodejs24-debian13:nonroot`. Use a multi-stage build.
- Run the container as a non-root user, use `COPY` instead of `ADD`, and define a `HEALTHCHECK`.
- Upgrade vulnerable npm dependencies in `app/package.json` to fixed versions and regenerate
  `app/package-lock.json` with `npm install --package-lock-only` inside `app/`.
- Do not "fix" findings by adding entries to `.trivyignore` or `vex.openvex.json`; suppressions
  require a human risk decision.
- Do not change `docs/solution/` – it is the reference answer used by presenters.
- Validate locally when possible: `docker build -t demo . && trivy image --severity HIGH,CRITICAL demo`
  and `trivy config .`.
