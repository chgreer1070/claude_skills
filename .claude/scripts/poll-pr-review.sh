#!/usr/bin/env bash
# poll-pr-review.sh — Background poller for PR reviews/comments from a bot
# Usage: bash .claude/scripts/poll-pr-review.sh [pr_number] [repo] [bot_substring] [timeout_seconds]
#
# Writes a JSON notification file to .claude/notifications/ when found.
# The check-notifications.cjs UserPromptSubmit hook picks it up on the next user message.

set -euo pipefail

PR_NUMBER="${1:-483}"
REPO="${2:-Jamie-BitFlight/claude_skills}"
BOT_FILTER="${3:-copilot}"
TIMEOUT="${4:-600}" # 10 minutes
INTERVAL=30         # poll every 30 seconds

PROJECT_ROOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
NOTIF_DIR="$PROJECT_ROOT/.claude/notifications"
mkdir -p "$NOTIF_DIR"

echo "[poll-pr-review] Watching PR #$PR_NUMBER on $REPO for '$BOT_FILTER' review (timeout: ${TIMEOUT}s, interval: ${INTERVAL}s)"
echo "[poll-pr-review] Notifications will be written to: $NOTIF_DIR"

elapsed=0
while [ "$elapsed" -lt "$TIMEOUT" ]; do
    timestamp=$(date -u +%Y%m%dT%H%M%S)

    # Check formal PR reviews via REST API
    reviews=$(gh api "repos/$REPO/pulls/$PR_NUMBER/reviews" 2>/dev/null || echo "[]")
    found_review=$(
        BOT_FILTER="$BOT_FILTER" PAYLOAD="$reviews" python3 <<'PYEOF'
import json, os
bot = os.environ.get("BOT_FILTER", "copilot")
try:
    items = json.loads(os.environ.get("PAYLOAD", "[]"))
    for r in items:
        login = r.get("user", {}).get("login", "")
        if bot.lower() in login.lower() and r.get("body", "").strip():
            print(json.dumps({
                "type": "review",
                "state": r.get("state", ""),
                "body": r.get("body", ""),
                "user": login,
                "url": r.get("html_url", ""),
                "submitted_at": r.get("submitted_at", ""),
            }))
            break
except Exception:
    pass
PYEOF
    ) || true

    if [ -n "$found_review" ]; then
        notif_file="$NOTIF_DIR/pr${PR_NUMBER}-review-${timestamp}.json"
        echo "$found_review" >"$notif_file"
        echo "[poll-pr-review] Review found after ${elapsed}s! -> $notif_file"
        exit 0
    fi

    # Also check issue comments (some bots post as comments, not formal reviews)
    comments=$(gh api "repos/$REPO/issues/$PR_NUMBER/comments" 2>/dev/null || echo "[]")
    found_comment=$(
        BOT_FILTER="$BOT_FILTER" PAYLOAD="$comments" python3 <<'PYEOF'
import json, os
bot = os.environ.get("BOT_FILTER", "copilot")
try:
    items = json.loads(os.environ.get("PAYLOAD", "[]"))
    for c in items:
        login = c.get("user", {}).get("login", "")
        if bot.lower() in login.lower() and c.get("body", "").strip():
            print(json.dumps({
                "type": "comment",
                "body": c.get("body", ""),
                "user": login,
                "url": c.get("html_url", ""),
                "created_at": c.get("created_at", ""),
            }))
            break
except Exception:
    pass
PYEOF
    ) || true

    if [ -n "$found_comment" ]; then
        notif_file="$NOTIF_DIR/pr${PR_NUMBER}-comment-${timestamp}.json"
        echo "$found_comment" >"$notif_file"
        echo "[poll-pr-review] Comment found after ${elapsed}s! -> $notif_file"
        exit 0
    fi

    echo "[poll-pr-review] ${elapsed}s elapsed — no '${BOT_FILTER}' activity yet, checking again in ${INTERVAL}s..."
    sleep "$INTERVAL"
    elapsed=$((elapsed + INTERVAL))
done

# Timeout — write a notification so Claude knows it expired
notif_file="$NOTIF_DIR/pr${PR_NUMBER}-timeout-${timestamp}.json"
echo "{\"type\":\"timeout\",\"pr\":$PR_NUMBER,\"repo\":\"$REPO\",\"bot\":\"$BOT_FILTER\",\"elapsed\":$elapsed,\"message\":\"No '${BOT_FILTER}' review or comment found within ${TIMEOUT}s\"}" >"$notif_file"
echo "[poll-pr-review] Timed out after ${elapsed}s -> $notif_file"
exit 1
