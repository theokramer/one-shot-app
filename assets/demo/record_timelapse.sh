#!/bin/bash
# Time-lapse recorder for a one-shot run: one silent screenshot every N seconds.
# Run it in YOUR terminal (macOS asks once for Screen Recording permission for that app).
#
#   record_timelapse.sh ~/Movies/oneshot-demo/frames 3      # start (interval in seconds, default 3)
#   touch ~/Movies/oneshot-demo/frames/STOP                  # stop from anywhere (or Ctrl-C)
#
# A 5-hour run at 3 s ≈ 6,000 JPGs ≈ 2–4 GB. Frames are named by Unix time, so
# make_demo.py can print the real elapsed clock on every frame.
set -u
OUT=${1:-$HOME/Movies/oneshot-demo/frames}
INT=${2:-3}
DISPLAY_N=${DISPLAY_N:-1}       # which display: 1 = main
mkdir -p "$OUT"; rm -f "$OUT/STOP"
echo "Recording display $DISPLAY_N every ${INT}s into $OUT. Stop: Ctrl-C or touch $OUT/STOP"
n=0
while [ ! -f "$OUT/STOP" ]; do
  f="$OUT/$(date +%s).jpg"
  if ! screencapture -x -C -D "$DISPLAY_N" -t jpg "$f" 2>/dev/null; then
    echo "screencapture failed: allow Screen Recording for this terminal in System Settings → Privacy & Security, then restart it."
    exit 1
  fi
  n=$((n+1)); [ $((n % 100)) -eq 0 ] && echo "$n frames ($(du -sh "$OUT" | cut -f1))"
  sleep "$INT"
done
echo "Stopped after $n frames."
