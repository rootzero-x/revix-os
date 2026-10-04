#!/usr/bin/env python3
"""Pilot run uchun reduksiya: SUT-only KO'RINISH + guard logi, keyin revix.reduce.

NEGA bu qadam kerak: xom probe.csv ikkala target'ni (sut va bystander) saqlaydi;
filtrlanmagan reduksiya bystander probe'larini aralashtiradi
(tests/integration/test_chain.py 524-qator). Validator reducerga shu ko'rinishni beradi
(`validate.reducer_view`); bu skript AYNAN o'sha filtrni qo'llaydi va faylga yozadi.
Run papkasiga HECH NARSA yozilmaydi.
"""
import csv, json, os, subprocess, sys

from revix import validate as V
from revix.prober import PROBE_FIELDS

run_dir, out_dir = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
run, findings = V.load_run_dir(run_dir)
if findings:
    print("load findings:", [str(f) for f in findings][:5])
view = V.reducer_view(run, "revix-sut.service", "sut")

ev = os.path.join(out_dir, "view-events.jsonl")
with open(ev, "w", encoding="utf-8") as f:
    for r in view.records:
        f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
pr = os.path.join(out_dir, "view-probe.csv")
# DIQQAT (vr-audit, doc 18 2): validate.load_run_dir har probe qatoriga progress ni progress_counter dan
# qo'shadi (04 4.5 adapteri). progress PROBE_FIELDS da YO'Q: faqat PROBE_FIELDS yozilsa u JIMGINA tashlanadi
# va R_ref 120/120 trialda hisoblanmaydi. Shu sabab BARCHA kalitlar yoziladi.
extra = []
for p in view.probes:
    for k in p:
        if k not in PROBE_FIELDS and k not in extra:
            extra.append(k)
fields = list(PROBE_FIELDS) + extra
print("probe ustunlari: PROBE_FIELDS +", extra)
with open(pr, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for p in view.probes:
        w.writerow({k: p.get(k) for k in fields})
print(f"view: {len(view.records)} record, {len(view.probes)} probe (xomda {len(run.records)} / {len(run.probes)})")

red = os.path.join(out_dir, "reduced")
os.makedirs(red, exist_ok=True)
cmd = [sys.executable, "-m", "revix.reduce", "--jsonl", ev, "--probe-csv", pr,
       "--out-dir", red, "--sweep", "--json"]
res = subprocess.run(cmd, capture_output=True, text=True)
open(os.path.join(red, "reduce-summary.json"), "w").write(res.stdout)
open(os.path.join(red, "reduce.stderr"), "w").write(res.stderr)
print("reduce rc =", res.returncode)
if res.returncode == 0:
    s = json.loads(res.stdout)["summary"]
    print("disposition_counts:", s["disposition_counts"])
    print("source:", s["disposition_source_counts"])
    print("n_primary:", s["n_primary"], " n_survival:", s["n_survival"], " n_episodes:", s["n_episodes"])
