#!/usr/bin/env bash
# iPhone News Daily Agent — runner script
# Runs the Claude agent with the AGENT.md prompt.
# Scheduled via cron: 0 1 * * * (01:00 UTC = 09:00 SGT daily)

set -euo pipefail

REPO_DIR="/home/user/test-repo"
AGENT_PROMPT="$REPO_DIR/iphone-news-agent/AGENT.md"
LOG_DIR="$REPO_DIR/iphone-news-agent/logs"
LOG_FILE="$LOG_DIR/run-$(date -u +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

echo "=== iPhone News Agent run started at $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG_FILE"

# Run Claude Code with the agent prompt in non-interactive mode
claude \
  --print \
  --output-format text \
  "$(cat "$AGENT_PROMPT")" \
  2>&1 | tee -a "$LOG_FILE"

echo "=== Run finished at $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG_FILE"
