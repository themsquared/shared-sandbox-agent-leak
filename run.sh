#!/usr/bin/env bash
# Runs both scenarios back to back and prints the comparison.
set -euo pipefail
cd "$(dirname "$0")"

echo "=== VULNERABLE: finance-agent and slack-agent share one sandbox (one volume) ==="
docker compose -f docker-compose.vulnerable.yml up --abort-on-container-exit --exit-code-from slack-agent 2>&1 \
  | grep -E "finance-agent-1|slack-agent-1|mock-slack-1" || true
docker compose -f docker-compose.vulnerable.yml down -v >/dev/null 2>&1

echo
echo "=== ISOLATED: finance-agent and slack-agent each get their own sandbox ==="
docker compose -f docker-compose.isolated.yml up --abort-on-container-exit --exit-code-from slack-agent 2>&1 \
  | grep -E "finance-agent-1|slack-agent-1|mock-slack-1" || true
docker compose -f docker-compose.isolated.yml down -v >/dev/null 2>&1
