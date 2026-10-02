#!/usr/bin/env python3
"""
Dataset checks of Table 1 (rows 1-5) of the paper, recomputed from the public CSVs.

  1. N = blow2 + blow3 on every borelog row that carries all three (ASTM D-1586: the first
     6-inch increment is the seating drive). Text-layer reports and the Bridge 33 borehole logs (scans)
     (Bridge 33) are counted separately.
  2. Laboratory-summary N against the borelog N at the same report, borehole and depth.
  3. Computation-sheet N against the borelog N, for Bridge 33 (both read visually from rendered pages).
  4. The reports' own equations re-derived during extraction (columns check_CSR, check_FOS,
     check_N160cs of ds06_liquefaction_rows.csv: "ok" where the re-derived value matched).
  5. The stress reduction coefficient r_d: the printed value against Youd et al. (2001, Eq. 2),
     r_d = 1.0 - 0.00765 z (z <= 9.15 m) and 1.174 - 0.0267 z (9.15 < z <= 23 m), at 2 dp.
     The other two relations of row 5 ((N1)60cs from fines content; CRR_M7.5) are checked
     in ds06_tables7_8.py ("VALIDATION" line).

Row 6 (the conclusion column re-read from the PDF pages) needs the source reports, which are
not public. Every join is keyed on report + borehole + depth.
"""
import csv
import os
from collections import Counter

DATA = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
SCANNED = "Bridge 33"


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def key(r):
    return (r["report"], r["borehole"].strip().upper(), round(float(r["depth_m"]), 2))


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


spt, lab, liq = load("ds06_spt.csv"), load("ds06_lab.csv"), load("ds06_liquefaction_rows.csv")

print("TABLE 1 - dataset checks recomputed from the public CSVs")

# 1. N = blow2 + blow3 (all rows that carry the three numbers, duplicates included, as in Table 1)
c = Counter()
for r in spt:
    b2, b3, n = f(r["blow2"]), f(r["blow3"]), f(r["N"])
    if None in (b2, b3, n):
        continue
    src = "scans" if r["report"] == SCANNED else "text layer"
    c[(src, abs(b2 + b3 - n) < 1e-9)] += 1
for src in ("text layer", "scans"):
    ok, bad = c[(src, True)], c[(src, False)]
    print(f"  1. N = blow2 + blow3 ({src}): {ok} / {ok + bad}")

# borelog N by (report, borehole, depth), duplicate records excluded
borelog = {key(r): f(r["N"]) for r in spt if not r.get("duplicate_record") and f(r["N"]) is not None}

# 2. laboratory-summary N against borelog N
c = Counter()
for r in lab:
    k, n = key(r), f(r["N"])
    if k in borelog and n is not None:
        c[abs(borelog[k] - n) < 1e-9] += 1
print(f"  2. laboratory-summary N = borelog N: {c[True]} / {c[True] + c[False]}")

# 3. computation-sheet N against borelog N, Bridge 33
c = Counter()
for r in liq:
    if r["report"] != SCANNED:
        continue
    k, n = key(r), f(r["N_observed"])
    if k in borelog and n is not None:
        c[abs(borelog[k] - n) < 1e-9] += 1
print(f"  3. computation-sheet N = borelog N ({SCANNED}, read visually): {c[True]} / {c[True] + c[False]}")

# 4. re-derived equations (text-layer sheets)
for col, what in (("check_CSR", "CSR"), ("check_FOS", "FOS = CRR / CSR"), ("check_N160cs", "(N1)60cs = alpha + beta (N1)60")):
    rows = [r for r in liq if r["report"] != SCANNED and r[col]]
    ok = sum(1 for r in rows if r[col] == "ok")
    print(f"  4. {what} re-derived (text layer): {ok} checked, {len(rows) - ok} mismatches")


# 5. r_d against Youd et al. (2001, Eq. 2)
def rd(z):
    return 1.0 - 0.00765 * z if z <= 9.15 else 1.174 - 0.0267 * z


c = Counter()
for r in liq:
    z, p = f(r["depth_m"]), f(r["rd"])
    if z is None or p is None:
        continue
    c[abs(round(rd(z), 2) - p) < 1e-9] += 1
print(f"  5. r_d reproduced by Youd et al. (2001, Eq. 2) at 2 dp: {c[True]} / {c[True] + c[False]}")
