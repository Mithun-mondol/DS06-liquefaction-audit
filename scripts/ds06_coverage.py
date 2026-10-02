#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper; the label map that once translated report file names is therefore empty.
"""
Item 18: recompute index-test coverage of the OVERRIDDEN depths, keyed correctly.

An "overridden" depth is one the report declares non-liquefiable (NL) while its
own computed factor of safety is below 1.0 - the screen beating the arithmetic.

The earlier figures (11.5% Atterberg, 9.3% moisture, 0% both) predate the
report+borehole+depth keying fix and predate counting the laboratory-summary
columns as sources of LL and wn. Both are corrected here.

Every join is on (report, borehole, depth) - never on (borehole, depth).
"""
import csv
import os
from collections import defaultdict


# Public labels only (added 2026-09-28): report file names carry firm designations and
# must never be printed.
_SHORT = []  # labels are already in the data


def label(rep):
    for key, name in _SHORT:
        if key.lower() in rep.lower():
            return name
    return rep

OUT = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))  # folder holding the CSVs


def f(v):
    try:
        x = float(v)
        return x if x > 0 else None
    except Exception:
        return None


def dep(v):
    try:
        return round(float(v), 2)
    except Exception:
        return None


def ID(r):
    return (r.get("report", ""), r.get("borehole", "").strip().upper(),
            dep(r.get("depth_m")))


liq = list(csv.DictReader(open(f"{OUT}/ds06_liquefaction_rows.csv", encoding="utf-8")))
lab = list(csv.DictReader(open(f"{OUT}/ds06_lab.csv", encoding="utf-8")))
att = list(csv.DictReader(open(f"{OUT}/ds06_atterberg.csv", encoding="utf-8")))
moi = list(csv.DictReader(open(f"{OUT}/ds06_moisture.csv", encoding="utf-8")))

# ---- every source of LL and of wn, keyed properly
LL = defaultdict(list)
for a in att:
    if f(a.get("LL_pct")):
        LL[ID(a)].append(("atterberg sheet", f(a["LL_pct"]), f(a.get("PI_pct"))))
for r in lab:
    if f(r.get("LL_pct")):
        LL[ID(r)].append(("lab summary", f(r["LL_pct"]), f(r.get("PI_pct"))))

WN = defaultdict(list)
for r in moi:
    if f(r.get("wn_pct")):
        WN[ID(r)].append(("moisture sheet", f(r["wn_pct"])))
for r in lab:
    if f(r.get("nmc_pct")):
        WN[ID(r)].append(("lab summary", f(r["nmc_pct"])))

# ---- the overridden population
over, liqf, other = [], [], []
for r in liq:
    fos, cc = f(r.get("FOS")), r.get("conclusion", "")
    if fos is None or not cc:
        other.append(r); continue
    (over if (cc == "NL" and fos < 1.0) else liqf).append(r)

print("=" * 76)
print("POPULATION")
print("=" * 76)
print(f"  computation rows                         : {len(liq)}")
print(f"  rows with both a FOS and a conclusion    : {len(over) + len(liqf)}")
print(f"  OVERRIDDEN (conclusion NL, FOS < 1.0)    : {len(over)}")
print(f"  rows without FOS or conclusion (refusal) : {len(other)}")


def pct(n, d):
    return f"{n} of {d} ({100.0*n/d:.1f}%)" if d else "-"


def coverage(rows, label):
    hasLL = [r for r in rows if ID(r) in LL]
    haswn = [r for r in rows if ID(r) in WN]
    both = [r for r in rows if ID(r) in LL and ID(r) in WN]
    print(f"\n  {label}  (n = {len(rows)})")
    print(f"     liquid limit at that exact depth  : {pct(len(hasLL), len(rows))}")
    print(f"     moisture at that exact depth      : {pct(len(haswn), len(rows))}")
    print(f"     BOTH - criterion evaluable        : {pct(len(both), len(rows))}")
    return hasLL, haswn, both


print()
print("=" * 76)
print("INDEX-TEST COVERAGE, keyed on report + borehole + depth")
print("=" * 76)
oLL, own, oboth = coverage(over, "OVERRIDDEN depths (NL despite FOS < 1)")
coverage(liqf, "all other depths carrying a conclusion")
coverage(liq, "every computation row")

if oboth:
    print("\n  The overridden depths where the criterion IS evaluable:")
    for r in oboth:
        k = ID(r)
        print(f"     {label(k[0]):44} {k[1]:7} {k[2]:>6} m  FOS={r['FOS']:>5} "
              f"strata={r.get('strata',''):4} LL={LL[k][0][1]:.2f} wn={WN[k][0][1]:.2f}")

print("\n  The overridden depths with a liquid limit but NO moisture:")
n = 0
for r in oLL:
    k = ID(r)
    if k not in WN:
        n += 1
        print(f"     {label(k[0]):44} {k[1]:7} {k[2]:>6} m  FOS={r['FOS']:>5} "
              f"strata={r.get('strata',''):4} LL={LL[k][0][1]:.1f} PI={LL[k][0][2]}")
print(f"     -> {n} depths where the screen decided the outcome and LL exists "
      f"but wn does not")

# ---- restate the headline
print()
print("=" * 76)
print("HEADLINE, CORRECTED")
print("=" * 76)
fos_over = sorted(f(r["FOS"]) for r in over)
import statistics as st
print(f"  {len(over)} of {len(over)+len(liqf)} depths carrying a conclusion "
      f"({100.0*len(over)/(len(over)+len(liqf)):.1f}%) are declared non-liquefiable")
print(f"  with a computed FOS below 1.0. FOS range {min(fos_over):.2f}-{max(fos_over):.2f}, "
      f"median {st.median(fos_over):.2f}.")
strata = defaultdict(int)
for r in over:
    strata[r.get("strata", "")] += 1
print(f"  strata of the overridden depths: {dict(strata)}")
bh = {(r['report'], r['borehole']) for r in over}
allbh = {(r['report'], r['borehole']) for r in liq}
print(f"  spanning {len(bh)} of {len(allbh)} boreholes")
print(f"\n  Of those {len(over)} overridden depths, the declared Chinese Criteria is")
print(f"  evaluable at {len(oboth)} of them.")
