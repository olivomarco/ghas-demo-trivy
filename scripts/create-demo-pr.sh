#!/usr/bin/env bash
# Opens the "bad PR" used in the PR-gate scene of the demo.
# The PR adds ejs@3.1.6 (CVE-2022-29078, CRITICAL) to the app, which ends up in the
# container image. Trivy reports a NEW critical alert and the ruleset blocks the merge.
#
# Usage: scripts/create-demo-pr.sh
set -euo pipefail

BRANCH="demo/add-template-engine-$(date +%Y%m%d%H%M%S)"
ROOT="$(git rev-parse --show-toplevel)"
cd "${ROOT}"

git fetch origin main --quiet
git switch -c "${BRANCH}" origin/main

(cd app && npm install ejs@3.1.6 --save-exact --package-lock-only --silent)

git add app/package.json app/package-lock.json
git commit --quiet -m "feat: add ejs template engine for HTML views"
git push --quiet -u origin "${BRANCH}"

gh pr create --base main --head "${BRANCH}" \
  --title "feat: add ejs template engine for HTML views" \
  --body "Adds \`ejs\` so we can render HTML views. Let's see what the container scan says 👀"

git switch --quiet -
