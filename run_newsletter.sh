#!/bin/bash
# run_newsletter.sh
# Runs on every Mac wake-up. Checks if the newsletter has already been
# sent today — if not, sends it. This prevents duplicate emails if your
# Mac wakes up multiple times in one day.

SCRIPT_DIR="/Users/liambarnhart/market_newsletter"
SENT_FLAG="$SCRIPT_DIR/.last_sent"
TODAY=$(date +%Y-%m-%d)

# Skip weekends (6=Saturday, 0=Sunday in date's %u is 1-7, so check day)
DAY_OF_WEEK=$(date +%u)  # 1=Mon, 7=Sun
if [ "$DAY_OF_WEEK" -ge 6 ]; then
  echo "Weekend — skipping."
  exit 0
fi

# Check if already sent today
if [ -f "$SENT_FLAG" ]; then
  LAST_SENT=$(cat "$SENT_FLAG")
  if [ "$LAST_SENT" = "$TODAY" ]; then
    echo "Already sent today ($TODAY) — skipping."
    exit 0
  fi
fi

# Wait 30 seconds after wake to make sure network is up
sleep 30

# Run the newsletter script
/usr/bin/python3 "$SCRIPT_DIR/newsletter.py"

# If it succeeded, record today's date so we don't send again
if [ $? -eq 0 ]; then
  echo "$TODAY" > "/Users/liambarnhart/market_newsletter/.last_sent"
  echo "Newsletter sent and flagged for $TODAY."
fi
