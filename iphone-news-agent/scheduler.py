#!/usr/bin/env python3
"""
iPhone News Daily Agent — persistent scheduler.

Runs the Claude agent once immediately (optional) and then every 24 hours
at 09:00 Singapore Time (01:00 UTC).

Usage:
    python3 scheduler.py            # start scheduler (next run at 01:00 UTC)
    python3 scheduler.py --now      # run once immediately, then schedule
    python3 scheduler.py --test     # dry-run: print what would execute and exit

Requirements:  Python 3.6+, no external packages needed.
"""

import argparse
import datetime
import logging
import os
import subprocess
import sys
import time

# ── Config ────────────────────────────────────────────────────────────────────

REPO_DIR    = "/home/user/test-repo"
AGENT_FILE  = os.path.join(REPO_DIR, "iphone-news-agent", "AGENT.md")
LOG_DIR     = os.path.join(REPO_DIR, "iphone-news-agent", "logs")
CLAUDE_BIN  = "/opt/node22/bin/claude"

# Fire at this UTC hour:minute each day (01:00 UTC = 09:00 SGT)
RUN_HOUR_UTC   = 1
RUN_MINUTE_UTC = 0

# ── Logging ───────────────────────────────────────────────────────────────────

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s UTC [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOG_DIR, "scheduler.log")),
    ],
)
log = logging.getLogger("iphone-news-scheduler")

# ── Core ──────────────────────────────────────────────────────────────────────

def load_prompt() -> str:
    with open(AGENT_FILE, "r") as f:
        return f.read()


def run_agent():
    """Invoke Claude Code with the AGENT.md prompt in non-interactive mode."""
    log.info("Starting agent run…")
    prompt = load_prompt()

    run_log = os.path.join(
        LOG_DIR,
        f"run-{datetime.datetime.utcnow().strftime('%Y-%m-%d_%H-%M')}.log",
    )

    try:
        result = subprocess.run(
            [CLAUDE_BIN, "--print", "--output-format", "text",
             "--allowedTools", "WebSearch,WebFetch", prompt],
            capture_output=True,
            text=True,
            cwd=REPO_DIR,
        )
        with open(run_log, "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n--- STDERR ---\n")
                f.write(result.stderr)

        if result.returncode == 0:
            log.info(f"Agent run completed successfully. Log: {run_log}")
        else:
            log.error(f"Agent exited with code {result.returncode}. Log: {run_log}")

    except Exception as e:
        log.exception(f"Failed to launch agent: {e}")


def seconds_until_next_run() -> float:
    """Return seconds until the next scheduled 01:00 UTC window."""
    now = datetime.datetime.utcnow()
    next_run = now.replace(
        hour=RUN_HOUR_UTC, minute=RUN_MINUTE_UTC, second=0, microsecond=0
    )
    if next_run <= now:
        next_run += datetime.timedelta(days=1)
    delta = (next_run - now).total_seconds()
    return delta


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="iPhone News Agent scheduler")
    parser.add_argument("--now",  action="store_true", help="Run agent immediately before scheduling")
    parser.add_argument("--test", action="store_true", help="Print next-run time and exit without running")
    args = parser.parse_args()

    log.info("iPhone News Daily Agent scheduler starting.")
    log.info(f"Agent prompt: {AGENT_FILE}")
    log.info(f"Scheduled fire time: {RUN_HOUR_UTC:02d}:{RUN_MINUTE_UTC:02d} UTC (09:00 SGT) daily")

    if args.test:
        wait = seconds_until_next_run()
        next_dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=wait)
        log.info(f"[DRY RUN] Next run in {wait/3600:.2f} h at {next_dt.strftime('%Y-%m-%d %H:%M UTC')}")
        sys.exit(0)

    if args.now:
        log.info("--now flag set: running agent immediately.")
        run_agent()

    # Main loop
    while True:
        wait = seconds_until_next_run()
        next_dt = datetime.datetime.utcnow() + datetime.timedelta(seconds=wait)
        log.info(f"Next run in {wait/3600:.1f} h at {next_dt.strftime('%Y-%m-%d %H:%M UTC')} (= {(RUN_HOUR_UTC+8)%24:02d}:{RUN_MINUTE_UTC:02d} SGT)")
        time.sleep(wait)
        run_agent()


if __name__ == "__main__":
    main()
