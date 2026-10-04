import json, collections, os, time, glob
R = os.path.expanduser("~/revix-runs/p1-pilot-002")
SIDE = R + ".pilot"
begin = {}; ends = {}; guard = []; faults = 0
for l in open(R + "/events.jsonl"):
    try: r = json.loads(l)
    except Exception: continue
    t = r.get("record_type")
    if t == "trial_begin": begin[r["trial_id"]] = r
    elif t == "trial_end": ends[r["trial_id"]] = r
    elif t == "fault_inject": faults += 1
cell = collections.defaultdict(collections.Counter)
for tid, e in ends.items():
    b = begin.get(tid, {})
    arm = b.get("arm") or (b.get("levels") or {}).get("arm")
    lv = b.get("pressure_band") or (b.get("levels") or {}).get("pressure_level")
    cell[f"{arm}/{lv}"][e.get("disposition")] += 1
n = len(ends)
now = time.strftime("%H:%M:%SZ", time.gmtime())
print(f"{now}  trial_end={n}/120  trial_begin={len(begin)}  fault_inject={faults}")
for k in sorted(cell): print(f"  {k:14s}", dict(cell[k]))
gj = R + "/guard.jsonl"
if os.path.exists(gj):
    trips = []
    for l in open(gj):
        try: g = json.loads(l)
        except Exception: continue
        if g.get("record_type") == "guard_event": trips.append((g.get("reason"), round(g.get("rate", 0) or 0, 4)))
    print("  guard_event:", len(trips), collections.Counter(x[0] for x in trips))
cw = SIDE + "/clock-watch.log"
last = open(cw).read().strip().splitlines()[-1] if os.path.exists(cw) else "-"
print("  soat:", last, "| ALERT:", "BOR !!!" if os.path.exists(SIDE + "/clock-watch.ALERT") else "yo'q")
print("  load:", open("/proc/loadavg").read().split()[0], " boot_id:", open("/proc/sys/kernel/random/boot_id").read()[:8],
      " oom_kill:", [l.split()[1] for l in open("/proc/vmstat") if l.startswith("oom_kill ")][0])
fin = os.path.exists(SIDE + "/marker-post.json")
print("  holat:", "TUGADI" if fin else "ishlayapti")
if n:
    t0 = min(b["mono_us"] for b in begin.values() if "mono_us" in b); t1 = max(e["mono_us"] for e in ends.values())
    per = (t1 - t0) / 1e6 / n
    print(f"  o'rtacha trial: {per:.1f} s -> qolgan ~{(120-n)*per/60:.0f} daqiqa")
