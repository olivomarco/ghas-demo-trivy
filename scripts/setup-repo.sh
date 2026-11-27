#!/usr/bin/env bash
# Configures the demo repository on GitHub:
#   - Enables Dependency graph, Dependabot alerts and (for private repos) GHAS / Code Security
#   - Creates a ruleset on the default branch that blocks merges when Trivy
#     reports HIGH or CRITICAL alerts (code scanning merge protection)
#
# Usage: scripts/setup-repo.sh [owner/repo]   (defaults to the current gh repo)
set -euo pipefail

REPO="${1:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"
echo "Configuring ${REPO}"

VISIBILITY=$(gh api "repos/${REPO}" -q .visibility)
if [[ "${VISIBILITY}" != "public" ]]; then
  echo "• Enabling GitHub Code Security / Advanced Security (private repo)"
  gh api -X PATCH "repos/${REPO}" --silent \
    -F 'security_and_analysis[advanced_security][status]=enabled' \
    || echo "  ⚠️  Could not enable GHAS – check your org licensing/policies."
fi

echo "• Enabling Dependabot alerts (also enables the dependency graph)"
gh api -X PUT "repos/${REPO}/vulnerability-alerts" --silent

echo "• Enabling secret scanning + push protection"
gh api -X PATCH "repos/${REPO}" --silent \
  -F 'security_and_analysis[secret_scanning][status]=enabled' \
  -F 'security_and_analysis[secret_scanning_push_protection][status]=enabled' \
  || echo "  ⚠️  Could not enable secret scanning."

RULESET_NAME="Block merges on Trivy HIGH+ alerts"
EXISTING_ID=$(gh api "repos/${REPO}/rulesets" -q ".[] | select(.name == \"${RULESET_NAME}\") | .id" || true)

read -r -d '' RULESET <<JSON || true
{
  "name": "${RULESET_NAME}",
  "target": "branch",
  "enforcement": "active",
  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
  "rules": [
    { "type": "pull_request", "parameters": {
        "required_approving_review_count": 0,
        "dismiss_stale_reviews_on_push": false,
        "require_code_owner_review": false,
        "require_last_push_approval": false,
        "required_review_thread_resolution": false } },
    { "type": "code_scanning", "parameters": {
        "code_scanning_tools": [
          { "tool": "Trivy", "security_alerts_threshold": "high_or_higher", "alerts_threshold": "errors" }
        ] } }
  ]
}
JSON

if [[ -n "${EXISTING_ID}" ]]; then
  echo "• Updating ruleset '${RULESET_NAME}' (id ${EXISTING_ID})"
  gh api -X PUT "repos/${REPO}/rulesets/${EXISTING_ID}" --input - --silent <<<"${RULESET}"
else
  echo "• Creating ruleset '${RULESET_NAME}'"
  gh api -X POST "repos/${REPO}/rulesets" --input - --silent <<<"${RULESET}"
fi

echo "✅ Done. Security tab: https://github.com/${REPO}/security"
