#!/bin/bash
# Capture one explicitly chosen window. There is no whole-display fallback.
# Run in your own terminal after completing sign-ins and private-data entry.
# Usage: record_timelapse.sh --window-id ID OUT_DIR [INTERVAL_SECONDS]
set -euo pipefail
umask 077
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: record_timelapse.sh --window-id ID OUT_DIR [INTERVAL_SECONDS]"
  echo "Use the Core Graphics window ID of the app or simulator you intend to record."
  echo "Keep footage outside repositories. Stop with Ctrl-C or touch OUT_DIR/STOP."
  exit 0
fi
if [[ $# -lt 3 || $# -gt 4 || "${1:-}" != "--window-id" || ! "${2:-}" =~ ^[1-9][0-9]*$ ]]; then
  echo "An explicit window is required. Run with --help for usage." >&2
  exit 2
fi
WINDOW_ID=$2
OUT=$3
INT=${4:-3}
# Arguments are --window-id ID OUT_DIR [INTERVAL_SECONDS].
if [[ ! "$INT" =~ ^[1-9][0-9]*$ ]]; then
  echo "Interval must be a positive integer." >&2
  exit 2
fi
mkdir -p "$OUT"
if git -C "$OUT" rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "Keep raw captures outside Git repositories." >&2
  exit 2
fi
rm -f "$OUT/STOP"
echo "Recording only window $WINDOW_ID. Stop with Ctrl-C or the STOP file."
n=0
while [[ ! -f "$OUT/STOP" ]]; do
  f="$OUT/$(date +%s).jpg"
  if ! screencapture -x -o -l "$WINDOW_ID" -t jpg "$f" 2>/dev/null; then
    echo "Window capture failed; recording stopped. Check the window and Screen Recording permission." >&2
    exit 1
  fi
  n=$((n+1))
  if [[ $((n % 100)) -eq 0 ]]; then echo "$n frames captured"; fi
  sleep "$INT"
done
echo "Stopped after $n frames."
