#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper; the label map that once translated report file names is therefore empty.
"""
Task A: can w_n be bounded from e0 and Gs instead of assumed?

For a soil at degree of saturation S:   e = w * Gs / S   ->   w = e * S / Gs
At S = 1 this gives w_sat = e0 / Gs, the maximum water content the measured void
ratio can hold.

Three things are tested, in this order:
  1. VALIDATION - where a sample has NMC *and* e0 *and* Gs, does e0/Gs reproduce
     the measured NMC? That tests the full-saturation assumption against data
     rather than asserting it.
  2. CO-LOCATION - do any e0+Gs samples sit at an Atterberg depth? If so, those
     samples get a data-derived w_n bound instead of a swept range.
  3. PACKAGE RANGE - what envelope does e0/Gs give for the package as a whole?
"""
import csv, os, statistics as st

OUT = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))  # folder holding the CSVs


def f(v):
    try:
        x = float(v)
        return x if x > 0 else None
    except Exception:
        return None


lab = list(csv.DictReader(open(f"{OUT}/ds06_lab.csv", encoding="utf-8")))
att = list(csv.DictReader(open(f"{OUT}/ds06_atterberg.csv", encoding="utf-8")))
moi = list(csv.DictReader(open(f"{OUT}/ds06_moisture.csv", encoding="utf-8")))

print(f"lab rows {len(lab)}   atterberg {len(att)}   moisture {len(moi)}\n")

# ---------------------------------------------------------------- 1. validation
both = []
for r in lab:
    e0, gs, nmc = f(r.get("e0")), f(r.get("specific_gravity")), f(r.get("nmc_pct"))
    if e0 and gs:
        both.append((r, e0, gs, nmc))

print("=" * 78)
print("1. SAMPLES WITH BOTH e0 AND Gs: %d" % len(both))
print("=" * 78)
print(f"{'structure':28} {'BH':8} {'depth':>6} {'e0':>6} {'Gs':>6} "
      f"{'w_sat%':>7} {'NMC%':>7} {'ratio':>6}")
val = []
for r, e0, gs, nmc in sorted(both, key=lambda t: (t[0]['structure'], t[0]['borehole'],
                                                  float(t[0]['depth_m'] or 0))):
    wsat = 100.0 * e0 / gs
    ratio = (nmc / wsat) if nmc else None
    if nmc:
        val.append((nmc, wsat, ratio))
    print(f"{r['structure'][:28]:28} {r['borehole'][:8]:8} {r['depth_m']:>6} "
          f"{e0:6.3f} {gs:6.3f} {wsat:7.2f} "
          f"{(f'{nmc:7.2f}' if nmc else '      -')} "
          f"{(f'{ratio:6.3f}' if ratio else '     -')}")

print()
if val:
    ratios = [v[2] for v in val]
    print(f"VALIDATION on {len(val)} samples that also have NMC:")
    print(f"  NMC / (e0/Gs)  min {min(ratios):.3f}  median {st.median(ratios):.3f}  "
          f"max {max(ratios):.3f}")
    print(f"  implied degree of saturation S = NMC*Gs/e0 : "
          f"{100*min(ratios):.1f}% to {100*max(ratios):.1f}%")
    n_over = sum(1 for x in ratios if x > 1.02)
    print(f"  samples where measured NMC EXCEEDS the saturated value by >2%: {n_over}"
          "   (would indicate e0 and NMC are not from the same specimen)")
else:
    print("VALIDATION IMPOSSIBLE: no sample carries e0, Gs and NMC together.")
    print("  -> the full-saturation assumption cannot be checked against this data,")
    print("     which makes any bound derived from it ASSUMED, not DERIVED.")

# ------------------------------------------------------------- 2. co-location
print()
print("=" * 78)
print("2. CO-LOCATION WITH THE 23 ATTERBERG SAMPLES")
print("=" * 78)


# Joined on report + borehole + depth. Borehole designations repeat across reports, so a join on
# borehole and depth alone conflates structures (the error described in the article, Section 2.3).
def key(rep, bh, d):
    try:
        return (rep, bh.strip().upper(), round(float(d), 2))
    except Exception:
        return None


eg = {}
for r, e0, gs, nmc in both:
    k = key(r["report"], r["borehole"], r["depth_m"])
    if k:
        eg.setdefault(k, (r, e0, gs))

hits = 0
for a in att:
    k = key(a["report"], a["borehole"], a["depth_m"])
    if k and k in eg:
        r, e0, gs = eg[k]
        hits += 1
        print(f"  HIT  {a['structure'][:26]:26} {a['borehole']:8} {a['depth_m']:>6} m  "
              f"LL={a['LL_pct']:>5} PI={a['PI_pct']:>5}  e0={e0:.3f} Gs={gs:.3f}  "
              f"w_sat={100*e0/gs:.2f}%")
print(f"\n  Atterberg samples with a co-located e0+Gs pair: {hits} of {len(att)}")

# also: do Atterberg depths coincide with ANY lab row carrying NMC? (re-confirm F1)
nmc_at = {}
for r in lab:
    if f(r.get("nmc_pct")):
        k = key(r["report"], r["borehole"], r["depth_m"])
        if k:
            nmc_at.setdefault(k, r)
for r in moi:
    k = key(r.get("report", ""), r.get("borehole", ""), r.get("depth_m", ""))
    if k:
        nmc_at.setdefault(k, r)
co_nmc = sum(1 for a in att if key(a["report"], a["borehole"], a["depth_m"]) in nmc_at)
print(f"  Atterberg samples with a co-located moisture value (F1 re-check): {co_nmc}")

# --------------------------------------------------------- 3. package envelope
print()
print("=" * 78)
print("3. PACKAGE ENVELOPE")
print("=" * 78)
wsats = sorted(100.0 * e0 / gs for _, e0, gs, _ in both)
if wsats:
    print(f"  w_sat = e0/Gs over {len(wsats)} samples: "
          f"{min(wsats):.1f}% - {max(wsats):.1f}%, median {st.median(wsats):.1f}%")

nm = sorted(x for x in (f(r.get("nmc_pct")) for r in lab) if x)
print(f"  measured NMC over {len(nm)} lab rows: {min(nm):.1f}% - {max(nm):.1f}%, "
      f"median {st.median(nm):.1f}%")

# shallow (<20 m) fine-grained NMC, which is the population the sweep concerns
sh = []
for r in lab:
    d, n = f(r.get("depth_m")), f(r.get("nmc_pct"))
    if d and n and d <= 20.0:
        sh.append(n)
if sh:
    print(f"  measured NMC, depth <= 20 m, {len(sh)} rows: {min(sh):.1f}% - {max(sh):.1f}%, "
          f"median {st.median(sh):.1f}%")

lls = sorted(x for x in (f(a.get("LL_pct")) for a in att) if x)
print(f"  LL over the 23 Atterberg samples: {min(lls):.0f} - {max(lls):.0f}, "
      f"median {st.median(lls):.0f}")
