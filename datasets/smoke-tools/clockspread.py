"""Spread of consecutive (dreal - dmono) in real REVIX run files.

Read-only. For every JSONL file: records grouped by `emitter`, in file
(write) order. For CSV files with mono/real column pairs: rows in file order.
Reports per-stream n, max |d|, p99.9 |d| and the offset range, plus a global
summary. Usage: python3 clockspread.py <dir> [<dir> ...]
"""
import csv, glob, io, json, os, sys, subprocess

PAIRS = (("mono_us", "real_us"), ("mono_us_send", "real_us_send"))


def opener(path):
    if path.endswith(".zst"):
        out = subprocess.run(["zstd", "-dc", path], capture_output=True, check=True).stdout
        return io.StringIO(out.decode("utf-8", "replace"))
    return open(path, encoding="utf-8", errors="replace")


def pct(xs, q):
    if not xs:
        return None
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def streams(path):
    base = os.path.basename(path).replace(".zst", "")
    out = {}
    with opener(path) as fh:
        if base.endswith(".jsonl"):
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if not isinstance(r, dict):
                    continue
                m, re_ = r.get("mono_us"), r.get("real_us")
                if isinstance(m, int) and isinstance(re_, int):
                    key = (base, str(r.get("emitter")))
                    out.setdefault(key, []).append((m, re_, r.get("record_type")))
        elif base.endswith(".csv"):
            rd = csv.DictReader(fh)
            cols = rd.fieldnames or []
            pair = next(((a, b) for a, b in PAIRS if a in cols and b in cols), None)
            if pair is None:
                return out
            for row in rd:
                try:
                    m, re_ = int(row[pair[0]]), int(row[pair[1]])
                except Exception:
                    continue
                out.setdefault((base, pair[0]), []).append((m, re_, None))
    return out


def main(dirs):
    glob_d = []
    glob_d_norm = []
    rows = []
    for d in dirs:
        for path in sorted(glob.glob(os.path.join(d, "*"))):
            if not (path.endswith((".jsonl", ".csv", ".jsonl.zst", ".csv.zst"))):
                continue
            for (base, em), recs in streams(path).items():
                if len(recs) < 2:
                    continue
                ds = []
                dm = []
                for (m0, r0, _), (m1, r1, rt) in zip(recs, recs[1:]):
                    ds.append((r1 - r0) - (m1 - m0))
                    dm.append(m1 - m0)
                offs = [r - m for m, r, _ in recs]
                a = [abs(x) for x in ds]
                rows.append((os.path.basename(d.rstrip("/")), base, em, len(recs),
                             max(a), pct(a, 0.999), pct(dm, 0.5), max(dm),
                             max(offs) - min(offs)))
                glob_d.extend(a)
    print(f"{'run':24} {'file':16} {'emitter':22} {'n':>7} {'max|d| s':>12} {'p99.9 s':>10} {'dmono p50 s':>11} {'dmono max s':>11} {'off range s':>12}")
    for r in rows:
        print(f"{r[0]:24} {r[1]:16} {r[2][:22]:22} {r[3]:7d} {r[4]/1e6:12.6f} {r[5]/1e6:10.6f} {r[6]/1e6:11.3f} {r[7]/1e6:11.3f} {r[8]/1e6:12.6f}")
    print("GLOBAL n_pairs", len(glob_d))
    for q in (0.5, 0.99, 0.999, 0.9999, 1.0):
        print(f"  |d| q{q}: {pct(glob_d, q)/1e6:.6f} s")
    for thr in (0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0):
        print(f"  pairs with |d| > {thr} s: {sum(1 for x in glob_d if x > thr*1e6)}")


if __name__ == "__main__":
    main(sys.argv[1:])
