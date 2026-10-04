#!/usr/bin/env bash
# Pilot kuzatuvchisi: faqat O'QIYDI. Anomaliyada yoki 20 daqiqadan keyin chiqadi.
R="$HOME/revix-runs/p1-pilot-002"; SIDE="$R.pilot"
STATUS="$1"
END=$(( $(date +%s) + 1200 ))
reason="vaqt (20 daqiqa)"
while [ "$(date +%s)" -lt "$END" ]; do
  [ -e "$SIDE/marker-post.json" ] && { reason="PILOT TUGADI"; break; }
  [ -e "$SIDE/clock-watch.ALERT" ] && { reason="SOAT UZILISHI"; break; }
  grep -q '"reason": *"sustained_pressure"' "$R/guard.jsonl" 2>/dev/null && { reason="SUSTAIN TRIP"; break; }
  pgrep -f "revix.cli run --run-dir $R" >/dev/null || { [ -e "$SIDE/marker-post.json" ] || { reason="DRIVER JARAYONI YO'Q"; break; }; }
  sleep 20
done
echo "=== kuzatuvchi chiqdi: $reason ==="
python3 "$STATUS"
