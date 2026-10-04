#!/usr/bin/env bash
# REVIX P1 pilot-002 launcher (orkestrator, preregistration/v1.13). pilot-001 YAROQSIZ, tahlil qilinmaydi.
# Pilot: preregistration/v1.12, seed 20261006, 120 trial, schedule_digest 69ae399e...b2dc.
set -u
EXPECT_HEAD="${1:?kutilgan git HEAD}"
RUN="$HOME/revix-runs/p1-pilot-002"
SIDE="$RUN.pilot"
WORK="$HOME/revix-work"
SEED=20261006
EXPECT_DIGEST=69ae399edbb20b5a0271d4b6657a3b5c1ec45b61b19a04a2bf9e0b6e8decb2dc

[ -e "$RUN" ] && { echo "run dir allaqachon bor: $RUN (append-only, qayta ishlatilmaydi)"; exit 9; }
mkdir -p "$SIDE"
log() { echo "[$(date -u +%H:%M:%SZ)] $*" | tee -a "$SIDE/launcher.log"; }

mkdir "$HOME/.revix-exclusive" 2>/dev/null && echo "pilot $(date -u +%FT%TZ)" > "$HOME/.revix-exclusive/holder" \
  || { log "QULF BAND: $(cat $HOME/.revix-exclusive/holder 2>/dev/null)"; exit 9; }
trap 'rm -rf "$HOME/.revix-exclusive"; log "qulf bo'"'"'shatildi"' EXIT

marker() { python3 - "$1" <<'PY'
import json, sys, time
d = {"phase": sys.argv[1]}
d["boot_id"] = open("/proc/sys/kernel/random/boot_id").read().strip()
d["pid1_starttime_ticks"] = int(open("/proc/1/stat").read().rsplit(")",1)[1].split()[19])
m = time.clock_gettime_ns(time.CLOCK_MONOTONIC)//1000; r = time.clock_gettime_ns(time.CLOCK_REALTIME)//1000
d["real_minus_mono_us"] = r - m
d["oom_kill"] = int([l.split()[1] for l in open("/proc/vmstat") if l.startswith("oom_kill ")][0])
d["loadavg"] = open("/proc/loadavg").read().strip()
d["uptime_s"] = float(open("/proc/uptime").read().split()[0])
print(json.dumps(d))
PY
}

log "== pre-flight"
pgrep -a 'VBoxHeadless|mmdebstrap|mksquashfs|pytest' && { log "OG'IR JARAYON BOR -- to'xtadi"; exit 9; }
# VirtualBox WINDOWS host'da ishlaydi -- WSL ichidagi pgrep uni KO'RMAYDI (pilot-001 da shunday edi).
PS=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
VMS=$($PS -NoProfile -Command "@(Get-Process VBoxHeadless,VirtualBoxVM -ErrorAction SilentlyContinue).Count" 2>/dev/null | tr -d '')
log "host VirtualBox jarayonlari=$VMS"
[ "$VMS" = "0" ] || { log "HOST'DA VIRTUALBOX VM ISHLAYAPTI (yoki tekshirib bo'lmadi: '$VMS') -- to'xtadi"; exit 9; }
LOAD=$(cut -d' ' -f1 /proc/loadavg); log "loadavg(1m)=$LOAD"
python3 -c "import sys; sys.exit(0 if float('$LOAD') < 0.3 else 1)" || { log "yuk baland (>=0.3) -- to'xtadi"; exit 9; }
cd "$WORK" || exit 9
HEAD=$(git rev-parse HEAD); log "git HEAD=$HEAD"
[ "$HEAD" = "$EXPECT_HEAD" ] || { log "HEAD kutilgandan farq qiladi ($EXPECT_HEAD)"; exit 9; }
[ -z "$(git status --porcelain)" ] || { log "daraxt IFLOS -- to'xtadi"; git status --porcelain | head -5 | tee -a "$SIDE/launcher.log"; exit 9; }
UNITS=$(systemctl --user list-units 'revix*' --all --no-legend | wc -l); log "revix unit soni=$UNITS"
[ "$UNITS" = "0" ] || { log "qoldiq unit bor -- to'xtadi"; exit 9; }
DIG=$(python3 -m revix.cli run --dry-run --run-dir "$HOME/revix-runs/_dry_never" --seed $SEED --json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('schedule_digest') or d.get('digest') or '')")
log "schedule_digest=$DIG"
[ "$DIG" = "$EXPECT_DIGEST" ] || { log "DIGEST MOS EMAS (kutilgan $EXPECT_DIGEST) -- to'xtadi"; exit 9; }
marker pre | tee "$SIDE/marker-pre.json"
cp /proc/loadavg "$SIDE/loadavg-pre.txt"

# soat uzilishini jonli kuzatish (faqat LOG, run'ga tegmaydi)
( OFF0=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_REALTIME)//1000 - time.clock_gettime_ns(time.CLOCK_MONOTONIC)//1000)")
  while [ -e "$HOME/.revix-exclusive" ]; do
    sleep 20
    OFF=$(python3 -c "import time; print(time.clock_gettime_ns(time.CLOCK_REALTIME)//1000 - time.clock_gettime_ns(time.CLOCK_MONOTONIC)//1000)")
    D=$(( OFF - OFF0 )); [ $D -lt 0 ] && D=$(( -D ))
    echo "$(date -u +%H:%M:%SZ) |dreal-dmono|_us=$D" >> "$SIDE/clock-watch.log"
    [ $D -gt 1000000 ] && echo "$(date -u +%H:%M:%SZ) !!! SOAT UZILISHI $D us" >> "$SIDE/clock-watch.ALERT"
  done ) &

log "== PILOT BOSHLANDI seed=$SEED"
T0=$(date +%s)
python3 -m revix.cli run --run-dir "$RUN" --seed $SEED --allow-pressure --json > "$SIDE/driver.json" 2> "$SIDE/driver.stderr"
RC=$?
log "driver rc=$RC wall_s=$(( $(date +%s) - T0 ))"

log "== post-flight"
marker post | tee "$SIDE/marker-post.json"
systemctl --user list-units 'revix*' --all --no-legend | tee "$SIDE/units-post.txt"
ls /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/ | grep revix | tee "$SIDE/cgroups-post.txt"
grep "^oom_kill" /proc/vmstat | tee "$SIDE/oomkill-post.txt"
python3 -m revix.validate --run-dir "$RUN" --sut-unit revix-sut.service --sut-target sut > "$SIDE/validate.txt" 2>&1
echo "validate rc=$?" | tee -a "$SIDE/validate.txt"
grep -E "^(ERROR|WARNING)|NATIJA|xato:" "$SIDE/validate.txt" | head -40 | tee -a "$SIDE/launcher.log"
log "== TUGADI"
