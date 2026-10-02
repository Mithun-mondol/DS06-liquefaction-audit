#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper; the label map that once translated report file names is therefore empty.
"""
Objective 4 / RQ3 / H1 - the determinacy analysis.

It does not need a numerical sweep. Both criteria are piecewise-linear in wn,
so the point at which each verdict flips is ANALYTIC, and the flip point is
independent of whatever range one chooses to sweep. The chosen range enters only
at the last step, when asking whether the flip point lies inside it.

Chinese Criteria as declared in the reports - liquefiable only if ALL hold:
    clay-size (<5 um) < 15%      [UNTESTABLE - no 5 um data in the package]
    LL < 35
    wn < 0.9 LL
  Note the asymmetry: a NON-liquefiable verdict from LL >= 35 or wn >= 0.9 LL is
  robust to the untestable clay-size condition, because failing any one condition
  is sufficient. Only its "liquefiable" verdicts are uncertain. Every verdict of
  interest here is non-liquefiable, so the missing 5 um data does not weaken the
  analysis.

Bray & Sancio (2006):
    PI > 18                      -> not susceptible, whatever wn is
    PI < 12                      -> susceptible            if wn/LL > 0.85
    12 <= PI <= 18               -> moderately susceptible if wn/LL > 0.80

Onset - CORRECTED 2026-09-27 (project log, correction C7). The audit question is the w_n
above which Bray & Sancio contradicts the report's NON-LIQUEFIABLE verdict:
    PI > 18        -> never (B&S concurs for any w_n)
    otherwise      -> w_n > t*LL, t = 0.85 (PI < 12) or 0.80 (12 <= PI <= 18)
This holds for every depth. The earlier version used 0.90*LL where LL < 35,
which answered "Chinese vs B&S" instead of "report vs B&S". For those LL < 35
depths the declared criterion itself supports NL only above 0.90*LL (or if the
fraction finer than 5 um is >= 15%, never measured), while B&S supports it only
below t*LL - and t < 0.90, so NO w_n satisfies both.
"""
import csv, statistics as st
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


lab = list(csv.DictReader(open(f"{OUT}/ds06_lab.csv", encoding="utf-8")))
att = list(csv.DictReader(open(f"{OUT}/ds06_atterberg.csv", encoding="utf-8")))
moi = list(csv.DictReader(open(f"{OUT}/ds06_moisture.csv", encoding="utf-8")))
liq = list(csv.DictReader(open(f"{OUT}/ds06_liquefaction_rows.csv", encoding="utf-8")))

# ---------------------------------------------------------------- index sources
IDX = {}
for a in att:
    if f(a.get("LL_pct")):
        IDX[ID(a)] = {"LL": f(a["LL_pct"]), "PI": f(a.get("PI_pct")), "src": "sheet"}
for r in lab:                                  # lab summary is more precise
    if f(r.get("LL_pct")):
        IDX[ID(r)] = {"LL": f(r["LL_pct"]), "PI": f(r.get("PI_pct")), "src": "lab"}

WN = {}
for r in moi:
    if f(r.get("wn_pct")):
        WN[ID(r)] = f(r["wn_pct"])
for r in lab:
    if f(r.get("nmc_pct")):
        WN[ID(r)] = f(r["nmc_pct"])

FOS, STRAT, CONCL = {}, {}, {}
for r in liq:
    k = ID(r)
    if f(r.get("FOS")) is not None:
        FOS[k] = f(r["FOS"])
    STRAT[k] = r.get("strata", "")
    CONCL[k] = r.get("conclusion", "")

# ------------------------------------------------- the plausible wn envelope
cl_wn = []
for r in lab:
    w, d = f(r.get("nmc_pct")), f(r.get("depth_m"))
    if w and d and d <= 20 and (r.get("soil_type", "") or "").upper().startswith(("CL", "ML")):
        cl_wn.append(w)
wsat = []
for r in lab:
    e0, gs = f(r.get("e0")), f(r.get("specific_gravity"))
    if e0 and gs:
        wsat.append(100.0 * e0 / gs)

print("=" * 78)
print("THE PLAUSIBLE wn ENVELOPE (item 14) - stated from data, not assumed")
print("=" * 78)
if cl_wn:
    print(f"  measured wn on CL/ML samples above 20 m, n={len(cl_wn)}: "
          f"{min(cl_wn):.1f}-{max(cl_wn):.1f}%, median {st.median(cl_wn):.1f}%")
print(f"  w_sat = e0/Gs, n={len(wsat)}: {min(wsat):.1f}-{max(wsat):.1f}%, "
      f"median {st.median(wsat):.1f}%")
LO = min(min(cl_wn), min(wsat)) if cl_wn else min(wsat)
HI = max(max(cl_wn), max(wsat)) if cl_wn else max(wsat)
print(f"  ENVELOPE ADOPTED: {LO:.1f}% - {HI:.1f}%  (union of the two, widest "
      f"defensible reading)")
print("  Report results against this envelope AND against the flip points "
      "themselves,\n  so a reader who prefers a different envelope can re-read the "
      "table.")


def onset(LL, PI):
    """w_n above which Bray & Sancio contradicts the report's non-liquefiable verdict."""
    if PI is None or LL is None:
        return None, "no PI"
    if PI > 18:
        return None, "PI > 18 - B&S concurs with NL, wn irrelevant"
    t = 0.85 if PI < 12 else 0.80
    if LL >= 35:
        return t * LL, f"LL >= 35: declared criterion NL for any wn; B&S contradicts above {t:.2f} LL"
    return t * LL, (f"LL < 35: B&S contradicts above {t:.2f} LL, and the declared criterion "
                    f"itself supports NL only above 0.90 LL - no wn satisfies both")


# ------------------------------------------ restrict to the overridden depths
over = [k for k in FOS if CONCL.get(k) == "NL" and FOS[k] < 1.0]
targets = sorted([k for k in over if k in IDX], key=lambda k: (k[0], k[1], k[2]))

print()
print("=" * 78)
print(f"FLIP POINTS ON THE {len(targets)} OVERRIDDEN DEPTHS THAT CARRY A LIQUID LIMIT")
print("=" * 78)
print(f"{'report / BH / depth':52} {'FOS':>5} {'LL':>5} {'PI':>5} "
      f"{'onset':>7} {'wn':>7} {'verdict':>12}")

settled, indet, measured_dis, measured_agree = [], [], [], []
for k in targets:
    d = IDX[k]
    on, why = onset(d["LL"], d["PI"])
    wn = WN.get(k)
    tag = f"{label(k[0]):30} {k[1]:7} {k[2]:>5} m"
    if on is None:
        settled.append((k, d, why))
        v = "agree (no wn)"
    elif wn is not None:
        (measured_dis if wn > on else measured_agree).append((k, d, on, wn))
        v = "DISAGREE" if wn > on else "agree"
    else:
        indet.append((k, d, on))
        v = "needs wn"
    print(f"{tag:52} {FOS[k]:5.2f} {d['LL']:5.1f} "
          f"{(d['PI'] if d['PI'] is not None else -1):5.1f} "
          f"{(f'{on:7.1f}' if on else '      -')} "
          f"{(f'{wn:7.2f}' if wn else '      -')} {v:>12}")

print()
print(f"  settled by PI > 18 - both criteria agree, wn irrelevant : {len(settled)}")
print(f"  resolved by a measured wn, criteria DISAGREE            : {len(measured_dis)}")
print(f"  resolved by a measured wn, criteria agree               : {len(measured_agree)}")
print(f"  INDETERMINATE - verdict hinges on the unmeasured wn     : {len(indet)}")

# ----------------------------------------------------- the H1 test
print()
print("=" * 78)
print("H1: is the verdict indeterminate across the plausible envelope?")
print("=" * 78)
print(f"  envelope {LO:.1f}% - {HI:.1f}%\n")
inside = outside_lo = outside_hi = 0
print(f"{'report / BH / depth':52} {'LL':>5} {'PI':>5} {'onset':>7}  position")
for k, d, on in indet:
    tag = f"{label(k[0]):30} {k[1]:7} {k[2]:>5} m"
    if on < LO:
        pos = "BELOW envelope -> DISAGREE for any plausible wn"; outside_lo += 1
    elif on > HI:
        pos = "ABOVE envelope -> agree for any plausible wn"; outside_hi += 1
    else:
        pos = "INSIDE envelope -> genuinely indeterminate"; inside += 1
    print(f"{tag:52} {d['LL']:5.1f} {d['PI']:5.1f} {on:7.1f}  {pos}")

n = len(indet)
print()
print(f"  flip point INSIDE the plausible envelope (indeterminate) : {inside} of {n}")
print(f"  flip point BELOW  (disagree whatever wn turns out to be) : {outside_lo} of {n}")
print(f"  flip point ABOVE  (agree whatever wn turns out to be)    : {outside_hi} of {n}")
print()
if inside + outside_lo > 0:
    print(f"  ==> {inside + outside_lo} of the {n} indeterminate overridden depths would be")
    print(f"      called susceptible by Bray & Sancio somewhere in the plausible wn")
    print(f"      range; {outside_lo} of them for EVERY plausible wn.")
print(f"  ==> H1 verdict: see the counts above. {inside} depths are indeterminate in")
print(f"      the strict sense (the flip point sits inside the envelope).")

# worked example
print()
print("=" * 78)
print("THE WORKED EXAMPLE FOR THE PAPER")
print("=" * 78)
for k, d, on, wn in measured_dis:
    print(f"  {label(k[0])}")
    print(f"  {k[1]} at {k[2]} m, strata {STRAT.get(k,'')}, the report's own FOS = {FOS[k]:.2f}")
    print(f"    measured wn = {wn:.2f}%   LL = {d['LL']:.2f}   PI = {d['PI']:.2f}   "
          f"wn/LL = {wn/d['LL']:.3f}")
    print(f"    Chinese Criteria  -> non-liquefiable   (the verdict the report used)")
    print(f"    Bray & Sancio     -> susceptible       (onset at wn = {on:.1f}%)")
    print(f"    Every quantity here is MEASURED. One depth carrying the whole argument.")
