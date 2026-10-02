#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper.
"""
Laboratory results printed for more than one borehole (the article, Section 3.2).

Takes the laboratory-summary values as printed and finds identical values attributed to samples of
different boreholes in different reports:
  1. pairs of boreholes with three or more identical values at the same depth;
  2. pairs of samples (any depth) sharing two or more identical results;
  3. what this means at the 216 overridden depths: supported verdicts whose supporting value
     (LL >= 35 % or clay >= 15 %) is printed identically for another borehole's sample, and moisture
     contents that are.
Quantities compared: moisture content, liquid and plastic limits, plasticity index, sand and clay
fractions (non-zero), unit weight, Cc, Cs, e0. Specific gravity, the unconfined-compression and the
direct-shear results take few distinct values and are not used as evidence.
"""
import csv, os, itertools, collections

OUT = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))  # folder holding the CSVs
VS = ["nmc_pct", "LL_pct", "PL_pct", "PI_pct", "sand_pct", "clay_pct", "unit_weight_kNm3", "Cc", "Cs", "e0"]


def f(v):
    try:
        return float(v)
    except Exception:
        return None


def K(r):
    return (r["report"], r["borehole"].strip(), round(float(r["depth_m"]), 2))


lab = list(csv.DictReader(open(f"{OUT}/ds06_lab.csv", encoding="utf-8")))
att = list(csv.DictReader(open(f"{OUT}/ds06_atterberg.csv", encoding="utf-8")))
liq = list(csv.DictReader(open(f"{OUT}/ds06_liquefaction_rows.csv", encoding="utf-8")))
spt = [r for r in csv.DictReader(open(f"{OUT}/ds06_spt.csv", encoding="utf-8")) if not r.get("duplicate_record")]
bhs = [r for r in csv.DictReader(open(f"{OUT}/ds06_boreholes.csv", encoding="utf-8")) if not r.get("duplicate_of")]

rows = {K(r): r for r in lab}
val = {k: {c: r[c].strip() for c in VS if r[c].strip() and f(r[c]) not in (None, 0.0)} for k, r in rows.items()}
over = {K(r) for r in liq if r["conclusion"] == "NL" and f(r["FOS"]) is not None and f(r["FOS"]) < 1}

# 1. same depth, different boreholes in different reports
byb = collections.defaultdict(dict)
for k in rows:
    byb[(k[0], k[1])][k[2]] = k
print("=" * 78)
print("1. BOREHOLE PAIRS WITH >= 3 IDENTICAL VALUES AT THE SAME DEPTH")
print("=" * 78)
meta = {(b["report"], b["borehole"].strip()): b for b in bhs}
npair = 0
for b1, b2 in itertools.combinations(sorted(byb), 2):
    if b1[0] == b2[0]:
        continue
    same = [(d, c, v) for d, k1 in byb[b1].items() if d in byb[b2]
            for c, v in val[k1].items() if val[byb[b2][d]].get(c) == v]
    if len(same) < 3:
        continue
    npair += 1
    n1 = {round(float(s["depth_m"]), 2): s["N"] for s in spt if (s["report"], s["borehole"].strip()) == b1}
    n2 = {round(float(s["depth_m"]), 2): s["N"] for s in spt if (s["report"], s["borehole"].strip()) == b2}
    common = [d for d in n1 if d in n2]
    m1, m2 = meta.get(b1, {}), meta.get(b2, {})
    print(f"  {b1[0]} {b1[1]} (Ch. {m1.get('chainage', '?')}, drilled {m1.get('date_start', '?')})  <->  "
          f"{b2[0]} {b2[1]} (Ch. {m2.get('chainage', '?')}, drilled {m2.get('date_start', '?')})")
    print(f"     identical at the same depth: {len(same)}  " + ", ".join(f"{d} m {c} {v}" for d, c, v in same))
    print(f"     SPT N equal at {sum(1 for d in common if n1[d] == n2[d])} of {len(common)} common depths")
print(f"  -> {npair} borehole pairs\n")

# 2. sample pairs sharing >= 2 identical results, any depth
idx = collections.defaultdict(set)
for k, d in val.items():
    for c, v in d.items():
        idx[(c, v)].add(k)
pairs = collections.defaultdict(set)
for (c, v), ks in idx.items():
    for a, b in itertools.combinations(sorted(ks), 2):
        if (a[0], a[1]) != (b[0], b[1]):
            pairs[(a, b)].add((c, v))
multi = {p: s for p, s in pairs.items() if len(s) >= 2}
print("=" * 78)
print(f"2. SAMPLE PAIRS (DIFFERENT BOREHOLES) SHARING >= 2 IDENTICAL RESULTS: {len(multi)}")
print("=" * 78)
for (a, b), s in sorted(multi.items()):
    print(f"  {a[0]} {a[1]} {a[2]} m  <->  {b[0]} {b[1]} {b[2]} m   " + ", ".join(f"{c} {v}" for c, v in sorted(s))
          + ("   [both overridden]" if a in over and b in over else ""))
print(f"  same depth: {sum(1 for a, b in multi if a[2] == b[2])}; different depths: "
      f"{sum(1 for a, b in multi if a[2] != b[2])} (offsets "
      f"{min(abs(a[2] - b[2]) for a, b in multi if a[2] != b[2]):.1f}-{max(abs(a[2] - b[2]) for a, b in multi):.1f} m)\n")

# 3. the overridden depths
LL, CL, W = {}, {}, {}
for a in att:
    if f(a["LL_pct"]) is not None:
        LL[K(a)] = (f(a["LL_pct"]), None)          # sheet value (whole numbers)
for r in lab:
    k = K(r)
    if f(r["LL_pct"]) is not None:
        LL[k] = (f(r["LL_pct"]), r["LL_pct"].strip())   # the summary is more precise
    if f(r["clay_pct"]) is not None:
        CL[k] = (f(r["clay_pct"]), r["clay_pct"].strip())
    if f(r["nmc_pct"]) is not None:
        W[k] = r["nmc_pct"].strip()


def elsewhere(c, v, k):
    return sorted(x for x in idx.get((c, v), ()) if (x[0], x[1]) != (k[0], k[1]))


sup = [k for k in over if (k in LL and LL[k][0] >= 35) or (k in CL and CL[k][0] >= 15)]
rep, alone = [], 0
for k in sorted(sup):
    hits, other = [], []
    if k in LL and LL[k][0] >= 35:
        (hits if LL[k][1] and elsewhere("LL_pct", LL[k][1], k) else other).append(("LL", LL[k][1] or LL[k][0]))
    if k in CL and CL[k][0] >= 15:
        (hits if elsewhere("clay_pct", CL[k][1], k) else other).append(("clay", CL[k][1]))
    if hits:
        rep.append((k, hits, other))
        alone += not other
print("=" * 78)
print("3. AT THE 216 OVERRIDDEN DEPTHS")
print("=" * 78)
print(f"  supported verdicts: {len(sup)}; supporting value printed identically for another borehole's sample: "
      f"{len(rep)} ({alone} with no other supporting value)")
for k, hits, other in rep:
    for q, v in hits:
        print(f"     {k[0]} {k[1]} {k[2]} m  {q} {v}  also at " +
              "; ".join(f"{x[0]} {x[1]} {x[2]} m" for x in elsewhere('LL_pct' if q == 'LL' else 'clay_pct', v, k)))
wrep = [k for k in over if k in W and elsewhere("nmc_pct", W[k], k)]
print(f"  moisture content at overridden depths: {sum(1 for k in over if k in W)}; "
      f"printed identically for another borehole's sample: {len(wrep)}")
allw = [r["nmc_pct"].strip() for r in lab if f(r["nmc_pct"]) is not None]
print(f"  laboratory-summary moisture contents: {len(allw)} values, {len(set(allw))} distinct")

ex = ("VUP Ch. 103+017", "BH-03", 9.0)
print(f"\n  the worked example, {ex[0]} {ex[1]} {ex[2]} m:")
for c, v in sorted(val.get(ex, {}).items()):
    e = elsewhere(c, v, ex)
    print(f"     {c} {v}: " + ("also at " + "; ".join(f"{x[0]} {x[1]} {x[2]} m" for x in e) if e else "unique"))
