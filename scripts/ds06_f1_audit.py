#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper; the label map that once translated report file names is therefore empty.
"""
Corrected F1 census, and the consequences for the screening comparison.

Verified against the source PDFs:
  Sub-soil investigation report, VUP Ch. 103+017
      "D6   9.0  CL  9.0 36.51 ... 38.13 24.50 13.63 ..."
  Sub-soil investigation report, VUP (DS-06)
      "D10 15.0  CL  8.0 33.60 2.69 39.05 19.72 19.33 ... 0.235 0.019 0.915"
Both are single rows of the Summary of Laboratory Test Results carrying
moisture content AND liquid limit for the same sample.
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


lab = list(csv.DictReader(open(f"{OUT}/ds06_lab.csv", encoding="utf-8")))
att = list(csv.DictReader(open(f"{OUT}/ds06_atterberg.csv", encoding="utf-8")))
moi = list(csv.DictReader(open(f"{OUT}/ds06_moisture.csv", encoding="utf-8")))

ID = lambda r: (r.get("report", ""), r.get("borehole", "").strip().upper(),
                dep(r.get("depth_m")))

# ---- full census of every sample carrying LL, from either source
ll_src = {}
for r in lab:
    if f(r.get("LL_pct")):
        ll_src.setdefault(ID(r), {})["lab"] = (f(r["LL_pct"]), f(r.get("PI_pct")),
                                               f(r.get("nmc_pct")))
for a in att:
    ll_src.setdefault(ID(a), {})["sheet"] = (f(a.get("LL_pct")), f(a.get("PI_pct")), None)

print("=" * 78)
print("CORRECTED CENSUS")
print("=" * 78)
print(f"  distinct samples with a liquid limit, either source : {len(ll_src)}")
print(f"    from an Atterberg sheet                           : "
      f"{sum(1 for v in ll_src.values() if 'sheet' in v)}")
print(f"    from a lab-summary row                            : "
      f"{sum(1 for v in ll_src.values() if 'lab' in v)}")
print(f"    from BOTH (same sample, two documents)            : "
      f"{sum(1 for v in ll_src.values() if len(v) == 2)}")

# ---- moisture at those identities, from every source
moi_at = defaultdict(list)
for r in moi:
    if f(r.get("wn_pct")):
        moi_at[ID(r)].append(("sheet", f(r["wn_pct"])))
for r in lab:
    if f(r.get("nmc_pct")):
        moi_at[ID(r)].append(("lab", f(r["nmc_pct"])))

withw = {k: v for k, v in ll_src.items() if k in moi_at}
print(f"\n  *** samples with LL and moisture at the same identity : {len(withw)} ***")
for k, v in withw.items():
    ll = (v.get("lab") or v.get("sheet"))[0]
    pi = (v.get("lab") or v.get("sheet"))[1]
    print(f"      {label(k[0]):42} {k[1]:7} {k[2]:>6} m  LL={ll:.2f} PI={pi:.2f} "
          f"wn={moi_at[k]}")

print(f"\n  moisture determinations total: {sum(1 for r in moi if f(r.get('wn_pct')))} "
      f"sheets + {sum(1 for r in lab if f(r.get('nmc_pct')))} lab-summary rows")

# ---- verdicts for the measured pairs
print()
print("=" * 78)
print("VERDICTS WHERE THE CRITERION IS ACTUALLY EVALUABLE")
print("=" * 78)


def chinese(ll, wn):
    """Criterion as declared in the reports: liquefiable only if ALL hold."""
    reasons = []
    if not (ll < 35):
        reasons.append(f"LL {ll:.2f} >= 35")
    if not (wn < 0.9 * ll):
        reasons.append(f"wn {wn:.2f} >= 0.9LL {0.9*ll:.2f}")
    return ("non-liquefiable" if reasons else "liquefiable (clay-size unverified)",
            "; ".join(reasons) or "both testable conditions pass")


def bray(pi, wn, ll):
    r = wn / ll
    if pi > 18:
        return "not susceptible", f"PI {pi:.2f} > 18"
    if pi < 12:
        return (("susceptible", f"PI<12 and wn/LL {r:.3f} > 0.85") if r > 0.85
                else ("not susceptible", f"PI<12 but wn/LL {r:.3f} <= 0.85"))
    return (("moderately susceptible", f"12<=PI<=18 and wn/LL {r:.3f} > 0.80") if r > 0.80
            else ("not susceptible", f"12<=PI<=18 but wn/LL {r:.3f} <= 0.80"))


for k, v in withw.items():
    ll, pi, _ = (v.get("lab") or v.get("sheet"))
    wn = moi_at[k][0][1]
    c, cr = chinese(ll, wn)
    b, br = bray(pi, wn, ll)
    agree = "AGREE" if (c == "non-liquefiable") == (b == "not susceptible") else "DISAGREE"
    print(f"\n  {label(k[0])}")
    print(f"    {k[1]} at {k[2]} m   wn={wn:.2f}  LL={ll:.2f}  PI={pi:.2f}  "
          f"wn/LL={wn/ll:.3f}")
    print(f"    Chinese Criteria : {c:36} ({cr})")
    print(f"    Bray & Sancio    : {b:36} ({br})")
    print(f"    --> {agree}  [OBSERVED, not inferred]")

# ---- how many of the 23 still hinge on an unmeasured wn
print()
print("=" * 78)
print("EFFECT ON THE SCREENING COMPARISON")
print("=" * 78)
settled = hinge = measured = 0
for k, v in ll_src.items():
    ll, pi, _ = (v.get("lab") or v.get("sheet"))
    if pi and pi > 18:
        settled += 1
    elif k in moi_at:
        measured += 1
    else:
        hinge += 1
print(f"  settled by PI alone (PI > 18, not susceptible)        : {settled}")
print(f"  resolved by a MEASURED wn                             : {measured}")
print(f"  still hinging on an UNMEASURED wn -> the O4 sweep      : {hinge}")
print(f"  total                                                 : {settled+measured+hinge}")

# ---- saturation validation on the one complete sample
print()
print("=" * 78)
print("SATURATION CHECK ON THE ONE ROW CARRYING wn, Gs AND e0")
print("=" * 78)
for r in lab:
    e0, gs, nmc = f(r.get("e0")), f(r.get("specific_gravity")), f(r.get("nmc_pct"))
    if e0 and gs and nmc and f(r.get("LL_pct")):
        print(f"  {label(r['report'])} {r['borehole']} {r['depth_m']} m")
        print(f"    e0={e0:.3f} Gs={gs:.3f} -> w_sat = e0/Gs = {100*e0/gs:.2f}%")
        print(f"    measured wn = {nmc:.2f}%  ->  S = {100*nmc*gs/e0:.1f}%")
