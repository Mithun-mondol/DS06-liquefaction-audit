#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper; the label map that once translated report file names is therefore empty.
"""
VERSION 4, 2026-09-28 (after the round-3 check). Three changes to the substitution chain:
  (1) Under the water-table substitution, a depth ABOVE its borehole's measured level is
      unsaturated, so no triggering calculation applies there. v3 still computed a FOS for
      such depths (sigma' = sigma). v4 excludes them from every water-table case and counts
      them separately (14 of the 190 overridden depths, 54 of the 310).
  (2) K_sigma, which the reports' text requires "when overburden pressure is high (depth >
      15 m)" but the sheets never apply (CRR/CRR_M7.5 = MSF at every depth), is available as
      a sensitivity: K_sigma = min(1, (sigma'/Pa)^(f-1)), Pa = 10 t/m^2 (the sheets' own C_N
      uses 10), f = 0.7 or 0.8 (the text's range for Dr 40-60 %).
  (3) The energy-ratio set is 78 / 70 / 60 / 48 / 30 %: the automatic-trip donut-type range
      (C_E 0.8-1.3, ER 48-78 %) and the donut range (C_E 0.5-1.0, ER 30-60 %) of Youd et al.
      (2001, Table 2). ER 45 % is replaced by 48 %, the automatic-trip lower bound.
  Also added: the supported count under the code's own thresholds (BNBC 2020 Sec 3.9.5: clay
  > 10 %, LL > 36 %), and the accelerations at which M 8.15-8.7 would match the reports' demand.

VERSION 3, 2026-09-28. Table numbers are now those of the assembled manuscript (the file
name keeps the draft numbering: draft Tables 7-8 are manuscript Tables 9-10). Reproduces:
  Section 3.1 census and Table 3 (conclusion against FOS);
  Table 5 (index-test coverage) and Table 6 (index data at the overridden depths, and what
  they support);
  Table 9 (class label against own Atterberg limits; Boulanger & Idriss 2006);
  Table 10 (substitutions through the reconstructed chain);
  Table 11 (the rescue grid, at four accelerations and five energy ratios);
  Table 12 (overridden depths at reduced a_max);
  the interaction check, and every a_max figure quoted in Section 3.7.
v3 runs on the CSV as corrected by ds06_fix_conclusions.py (project log, correction C11): 39 printed
conclusions that the extraction had dropped are restored.
Prints public structure labels only, never report file names.

VERSION 2, 2026-09-27 - supersedes v1 (see project log, correction C9). v1 took alpha from the
CSV column labelled "alpha", which on 308 of 334 rows actually holds beta (an
extraction column offset), and inferred beta from it. That error scales with
(1 - N_new/N_old), so it vanished at baseline and the x0.999 self-check could
not see it. v2 uses no printed alpha or beta at all: both are computed from the
fines content with the relations the sheets themselves use, validated on every
testable row before use.

Relations, each recovered from the reports' own numbers:
  CRR_M7.5   NCEER clean-sand curve (Youd et al. 2001, Eq. 4):
             1/(34-N) + N/135 + 50/(10N+45)^2 - 1/200, N = (N1)60cs < 30;
             reproduces the printed CRR_M7.5 at 321 of 322 depths to the printed
             two decimals (the remaining one lies on a rounding boundary)
  beta       1.0 (FC<=5); 0.99 + FC^1.5/1000 (5<FC<35); 1.2 (FC>=35)
  alpha      0 (FC<=5); exp(1.76 - 190/FC^2) (5<FC<35);
             0.50 for FC>=35 AS PRINTED AND USED ON THE SHEETS - the reports' own
             body text, and Youd et al. 2001 Eq. 6c, give 5.0 (the "alpha slip")
             -> sheet relation reproduces (N1)60cs on 334 of 334 testable rows
  C_N        min(1.7, sqrt(10/sigma'))  sigma' in t/m^2
  sigma'     raised by gamma_w * min(z, d), gamma_w = 1.0 t/m^3, d = measured GWL
  MSF        10^2.24 / Mw^2.56          Idriss (revised); Youd et al. 2001 Table 3
  C_E        ER/60                      Youd et al. 2001 Table 2
All joins keyed on report + borehole + depth.
"""
import csv, math, statistics as st
import os

OUT = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))  # folder holding the CSVs
INF = float("inf")


def f(v):
    try:
        return float(v)
    except Exception:
        return None


def dep(v):
    try:
        return round(float(v), 2)
    except Exception:
        return None


def ID(r):
    return (r.get("report", ""), r.get("borehole", "").strip().upper(), dep(r.get("depth_m")))


liq = list(csv.DictReader(open(f"{OUT}/ds06_liquefaction_rows.csv", encoding="utf-8")))
lab = list(csv.DictReader(open(f"{OUT}/ds06_lab.csv", encoding="utf-8")))
att = list(csv.DictReader(open(f"{OUT}/ds06_atterberg.csv", encoding="utf-8")))
bhs = list(csv.DictReader(open(f"{OUT}/ds06_boreholes.csv", encoding="utf-8")))
mois = list(csv.DictReader(open(f"{OUT}/ds06_moisture.csv", encoding="utf-8")))

# Public labels only: report file names carry firm designations and must never be printed.
SHORT = []  # labels are already in the data


def short(rep):
    for key, name in SHORT:
        if key.lower() in rep.lower():
            return name
    return rep

# ================================================================ SECTION 3.1 / TABLE 3
ALLC = [r for r in liq if r.get("conclusion") and f(r.get("FOS")) is not None]
OVR0 = [r for r in ALLC if r["conclusion"] == "NL" and f(r["FOS"]) < 1]
print(f"SECTION 3.1 CENSUS  computation rows {len(liq)}; with a conclusion "
      f"{sum(1 for r in liq if r.get('conclusion'))}; with a conclusion and a FOS {len(ALLC)}")
for c_ in ("L", "NL"):
    lo = sum(1 for r in ALLC if r["conclusion"] == c_ and f(r["FOS"]) < 1)
    hi = sum(1 for r in ALLC if r["conclusion"] == c_ and f(r["FOS"]) >= 1)
    print(f"  TABLE 3  {c_:2}  FOS<1 {lo:4}   FOS>=1 {hi:3}")
fo = sorted(f(r["FOS"]) for r in OVR0)
nn = sorted(f(r["N_observed"]) for r in OVR0 if f(r.get("N_observed")) is not None)
dd = sorted(f(r["depth_m"]) for r in OVR0)
print(f"  overridden {len(OVR0)} of {len(ALLC)} ({100 * len(OVR0) / len(ALLC):.1f} %); FOS "
      f"{fo[0]:.2f}-{fo[-1]:.2f}, median {st.median(fo):.2f}; depth {dd[0]}-{dd[-1]} m; "
      f"N {nn[0]:.0f}-{nn[-1]:.0f} (median {st.median(nn):.0f})")
bh_all = {(r["report"], r["borehole"]) for r in liq}
bh_ov = {(r["report"], r["borehole"]) for r in OVR0}
print(f"  boreholes with an override: {len(bh_ov)} of {len(bh_all)}")
from collections import Counter as _C
print(f"  classes: overridden {dict(_C(r['strata'] for r in OVR0))}; declared liquefiable "
      f"{dict(_C(r['strata'] or '(none)' for r in ALLC if r['conclusion'] == 'L'))}")
print("  non-liquefiable with FOS >= 1: " + ", ".join(
    f"{short(r['report'])} {r['borehole']} {r['depth_m']} m {r['strata']} FOS {r['FOS']}"
    for r in ALLC if r["conclusion"] == "NL" and f(r["FOS"]) >= 1))
per_rep = _C(short(r["report"]) for r in ALLC if r["conclusion"] == "L")
print(f"  declared liquefiable per report: {dict(sorted(per_rep.items()))}")

# ================================================================ TABLE 9 (draft Table 7)
IDX = {}
for a in att:
    if f(a.get("LL_pct")):
        IDX[ID(a)] = (f(a["LL_pct"]), f(a.get("PI_pct")))
for r in lab:                                    # lab summary is the more precise source
    if f(r.get("LL_pct")):
        IDX[ID(r)] = (f(r["LL_pct"]), f(r.get("PI_pct")))
ROW = {ID(r): r for r in liq}


def uscs(LL, PI):
    A = 0.73 * (LL - 20)
    if LL >= 50:
        return "CH" if PI >= A else "MH"
    if PI > 7 and PI >= A:
        return "CL"
    if 4 <= PI <= 7 and PI >= A:
        return "CL-ML"
    return "ML"


print("\nTABLE 9 - class used vs class from the sample's own limits")
clay_like = sand_like = 0
mismatch = []
for k, (LL, PI) in sorted(IDX.items()):
    if PI is None:
        continue
    clay_like += PI >= 7
    sand_like += PI < 7
    r = ROW.get(k)
    if not r:
        continue
    used, own = r.get("strata", "").strip(), uscs(LL, PI)
    if used and used.upper() != own:
        mismatch.append((k, used, own, LL, PI, 0.73 * (LL - 20), f(r.get("fines_pct")),
                         r.get("FOS"), r.get("conclusion")))
for k, used, own, LL, PI, A, fc, fos, c in mismatch:
    print(f"  {short(k[0]):16} {k[1]} {k[2]:>5} m  used {used:3} own {own:3} "
          f"(LL {LL:.1f}, PI {PI:.1f}, A-line {A:.1f})  fines {fc}%  FOS {fos}  {c}")
print(f"  -> {len(mismatch)} of {len(IDX)} samples contradicted; all fine-grained: "
      f"{all(m[6] and m[6] >= 50 for m in mismatch)}")
print(f"  Boulanger & Idriss (2006): clay-like (PI>=7) {clay_like}, sand-like {sand_like}")

# ================================================================ TABLE 4 (revised, C10)
# A non-liquefiable verdict under the declared criterion needs ONE failing condition:
# LL >= 35, or clay (< 0.005 mm, the laboratory's own boundary) >= 15 %, or the moisture
# condition on a matched sample. Which way the moisture condition points differs between the
# reports' statement (NL if w_n >= 0.9 LL) and the original (NL if w_n <= 0.9 LL), so it is
# reported, not counted as support.
CLAY = {ID(r): f(r["clay_pct"]) for r in lab if f(r.get("clay_pct")) is not None}
WN = {}
for m_ in mois:
    if f(m_.get("wn_pct")) is not None:
        WN[ID(m_)] = f(m_["wn_pct"])
for r in lab:
    if f(r.get("nmc_pct")) is not None:
        WN[ID(r)] = f(r["nmc_pct"])
OVR = [r for r in liq if r.get("conclusion") == "NL" and f(r.get("FOS")) is not None and f(r["FOS"]) < 1]
cnt = {"LL": 0, "LL35": 0, "clay": 0, "clay15": 0, "wn": 0, "pair": 0,
       "supported": 0, "data_unsupported": 0, "nothing": 0, "no_PI": 0}
for r in OVR:
    k = ID(r)
    ll = IDX.get(k, (None, None))[0]
    pi = IDX.get(k, (None, None))[1]
    c = CLAY.get(k)
    s_ll, s_c = ll is not None and ll >= 35, c is not None and c >= 15
    cnt["LL"] += ll is not None
    cnt["LL35"] += s_ll
    cnt["clay"] += c is not None
    cnt["clay15"] += s_c
    cnt["wn"] += k in WN
    cnt["pair"] += ll is not None and k in WN
    cnt["no_PI"] += pi is None
    if s_ll or s_c:
        cnt["supported"] += 1
    elif ll is not None or c is not None:
        cnt["data_unsupported"] += 1
    else:
        cnt["nothing"] += 1
n_ov = len(OVR)
# ---- TABLE 5: coverage across the package, by distinct sample (report, borehole, depth)
wn_sheet = {ID(m_) for m_ in mois if f(m_.get("wn_pct")) is not None}
wn_lab = {ID(r) for r in lab if f(r.get("nmc_pct")) is not None}
ll_sheet = {ID(a) for a in att if f(a.get("LL_pct"))}
ll_lab = {ID(r) for r in lab if f(r.get("LL_pct"))}
print(f"\nTABLE 5 - coverage by distinct sample: moisture {len(wn_sheet | wn_lab)} "
      f"({len(wn_sheet)} sheets + {len(wn_lab)} summary, {len(wn_sheet & wn_lab)} shared); "
      f"liquid limit {len(ll_sheet | ll_lab)} ({len(ll_sheet)} + {len(ll_lab)}, "
      f"{len(ll_sheet & ll_lab)} shared); both on one sample {len((wn_sheet | wn_lab) & (ll_sheet | ll_lab))}; "
      f"moisture sheets sharing a sample with Atterberg sheets {len(wn_sheet & ll_sheet)}")
on_rows = {ID(r): r for r in ALLC}
ll_keys = ll_sheet | ll_lab
print(f"  liquid-limit samples at analysed depths {sum(1 for k in ll_keys if k in on_rows)} of "
      f"{len(ll_keys)}; at overridden depths "
      f"{sum(1 for k in ll_keys if k in on_rows and on_rows[k]['conclusion'] == 'NL' and f(on_rows[k]['FOS']) < 1)}")
bi = [IDX[ID(r)][1] for r in OVR if ID(r) in IDX and IDX[ID(r)][1] is not None]
print(f"  Boulanger & Idriss at the overridden depths with a PI: clay-like {sum(p >= 7 for p in bi)}, "
      f"sand-like {sum(p < 7 for p in bi)}; PI exactly 12 or 18: "
      f"{sorted(p for p in bi if p in (12.0, 18.0))}")
print(f"\nTABLE 6 - index data at the {n_ov} overridden depths, and what they support")
for key, label in (("LL", "liquid limit measured"), ("LL35", "  of which >= 35 %"),
                   ("clay", "clay fraction measured"), ("clay15", "  of which >= 15 %"),
                   ("wn", "moisture content measured"), ("pair", "LL and w_n on the same sample"),
                   ("supported", "verdict supported by a measured failing condition"),
                   ("data_unsupported", "index data measured, none supporting the verdict"),
                   ("nothing", "neither a liquid limit nor a clay fraction"),
                   ("no_PI", "no plasticity index")):
    print(f"  {label:52} {cnt[key]:4}  ({100 * cnt[key] / n_ov:.1f} %)")

# ---- sensitivity of the supported count to the LL threshold (Discussion: Koester 1992)
LLT = [(r, IDX[ID(r)][0], IDX[ID(r)][1]) for r in OVR if ID(r) in IDX and IDX[ID(r)][0] is not None]
clay_ok = {ID(r) for r in OVR if CLAY.get(ID(r)) is not None and CLAY[ID(r)] >= 15}
print(f"\nLL-THRESHOLD SENSITIVITY (supported = LL >= threshold, or clay >= 15 %)")
for thr in (35, 36, 37, 38, 39, 40):
    s = {ID(r) for r, ll, _ in LLT if ll >= thr} | clay_ok
    print(f"  threshold {thr}: supported {len(s):2} of {n_ov};  "
          f"by LL {sum(1 for _, ll, _ in LLT if ll >= thr):2}")
# ---- the class rule: does "CL -> NL; otherwise L if FOS < 1" reproduce every verdict?
ALL = [r for r in liq if r.get("conclusion") and f(r.get("FOS")) is not None]


def class_rule(r):
    if r.get("strata", "").strip().upper() == "CL":
        return "NL"
    return "L" if f(r["FOS"]) < 1 else "NL"


print(f"\nCLASS RULE reproduces {sum(class_rule(r) == r['conclusion'] for r in ALL)} of "
      f"{len(ALL)} verdicts")
cntr = [r for r in ALL if r["conclusion"] == "L" and (
    (ID(r) in IDX and IDX[ID(r)][0] is not None and IDX[ID(r)][0] >= 35) or
    (CLAY.get(ID(r)) is not None and CLAY[ID(r)] >= 15))]
print(f"  declared liquefiable although a measured value fails a condition of the declared "
      f"criterion: {len(cntr)}")
for r in cntr:
    k = ID(r)
    print(f"    {short(k[0]):16} {k[1]} {k[2]:>5} m  {r['strata']:3} LL {IDX.get(k, (None,))[0]}  "
          f"clay {CLAY.get(k)}  FOS {r['FOS']}")

# ---- data a cyclic-softening evaluation would need, at the overridden depths
LABK = {ID(r): r for r in lab}
has = lambda r, col: ID(r) in LABK and f(LABK[ID(r)].get(col)) is not None
u = {ID(r) for r in OVR if has(r, "ucs_qu_kPa")}
c = {ID(r) for r in OVR if has(r, "Cc") or has(r, "e0")}
print(f"\nCYCLIC-SOFTENING DATA at the {n_ov} overridden depths: undrained strength (UCS) at "
      f"{len(u)}, consolidation (Cc or e0) at {len(c)}, both at {len(u & c)}")
near = sum(1 for _, ll, _ in LLT if 35 <= ll < 35.6)
own_cl = sum(1 for _, ll, pi in LLT if pi is not None and uscs(ll, pi) == "CL")
print(f"  of the {len(LLT)} overridden depths with a liquid limit: LL >= 35 at "
      f"{sum(1 for _, ll, _ in LLT if ll >= 35)}, within 0.6 of 35 at {near}, "
      f"CL by own limits at {own_cl}")

# ================================================================ RELATIONS
GWL = {}
for r in bhs:
    g = f(r.get("gwl_m"))
    if g is not None:
        GWL[(r.get("report", ""), r.get("borehole", "").strip().upper())] = g


def gwl_of(r):
    g = f(r.get("gwl_measured_m"))
    return g if g is not None else GWL.get((r.get("report", ""), r.get("borehole", "").strip().upper()))


def beta(fc):
    return 1.0 if fc <= 5 else (0.99 + fc ** 1.5 / 1000 if fc < 35 else 1.2)


def alpha(fc, fixed=False):
    if fc <= 5:
        return 0.0
    if fc < 35:
        return math.exp(1.76 - 190 / fc ** 2)
    return 5.0 if fixed else 0.50           # 0.50 = as printed and used on the sheets


def crr75(n):
    if n is None:
        return None
    if n >= 30:
        return INF                          # NCEER: too dense to liquefy
    return 1 / (34 - n) + n / 135 + 50 / (10 * n + 45) ** 2 - 1 / 200


def MSF(M):
    return 10 ** 2.24 / M ** 2.56


def CN_of(s):
    return min(1.7, math.sqrt(10.0 / s))


# ---- validation of the relations against the reports' own printed numbers
ok_c = tot_c = ok_n = tot_n = 0
for r in liq:
    n, c = f(r.get("N160cs")), f(r.get("CRR_M75"))
    if n is not None and c is not None and n < 30:
        tot_c += 1
        ok_c += abs(round(crr75(n), 2) - c) < 1e-9
    fc, n1 = f(r.get("fines_pct")), f(r.get("N160"))
    if None not in (fc, n1, n):
        tot_n += 1
        ok_n += abs(alpha(fc) + beta(fc) * n1 - n) <= 0.011
print(f"\nVALIDATION  CRR_M7.5 exact at 2 dp: {ok_c} of {tot_c};  (N1)60cs reproduced: {ok_n} of {tot_n}")


def is_dry(r):
    """Above the borehole's measured water level: unsaturated if the water table is moved there."""
    z, d = f(r.get("depth_m")), gwl_of(r)
    return z is not None and d is not None and z < d


def fos(r, WT=False, M=6.5, ER=70, fix=False, csr_only=False, ks=None, fexp=0.7):
    z, se, csr = f(r.get("depth_m")), f(r.get("sigma_eff")), f(r.get("CSR"))
    cn, n160, ce, fc = f(r.get("CN")), f(r.get("N160")), f(r.get("CE")), f(r.get("fines_pct"))
    d = gwl_of(r)
    if None in (z, se, csr, cn, n160, ce, fc, d) or se <= 0 or cn <= 0 or ce == 0:
        return None
    if WT and z < d:
        return None                         # unsaturated under this substitution: no FOS applies
    se_n = se + 1.0 * min(z, d) if WT else se
    csr_n = csr * se / se_n
    cn_n = cn if csr_only else CN_of(se_n)
    n_new = n160 * (cn_n / cn) * ((ER / 60.0) / ce)
    k_sig = 1.0
    if ks == "text" and z > 15:             # the reports' text: required for depth > 15 m
        k_sig = min(1.0, (se_n / 10.0) ** (fexp - 1))
    elif ks == "stress":                    # Youd et al. (2001): wherever sigma' exceeds Pa
        k_sig = min(1.0, (se_n / 10.0) ** (fexp - 1))
    return crr75(alpha(fc, fix) + beta(fc) * n_new) * MSF(M) * k_sig / csr_n


rows = [r for r in liq if f(r.get("FOS")) is not None and r.get("conclusion")]
base = [(r, f(r["FOS"])) for r in rows]


def run(wet=False, **kw):
    """wet=True restricts the population to depths below the measured water level, so that
    cases with and without the water-table substitution can be compared on one population."""
    d = [(r, a, fos(r, **kw)) for r, a in base if not (wet and is_dry(r))]
    d = [x for x in d if x[2] is not None]
    rat = st.median([c / a for _, a, c in d if a > 0 and c != INF])
    ov = [(r, a, c) for r, a, c in d if r["conclusion"] == "NL" and a < 1.0]
    return d, rat, ov


# ================================================================ TABLE 8
CASES = [
    ("None - baseline reproduced", {}),
    ("[arithmetic] alpha, FC>=35: 0.50 -> 5.0", dict(fix=True)),
    ("Water table 0.00 m -> measured", dict(WT=True)),
    ("Design magnitude M 6.5 -> 7.5", dict(M=7.5)),
    ("Design magnitude M 6.5 -> 8.0", dict(M=8.0)),
    ("Design magnitude M 6.5 -> 8.7", dict(M=8.7)),
    ("Energy ratio 70% -> 78% (auto-trip upper bound)", dict(ER=78)),
    ("Energy ratio 70% -> 60% (donut upper bound)", dict(ER=60)),
    ("Energy ratio 70% -> 48% (auto-trip lower bound)", dict(ER=48)),
    ("Energy ratio 70% -> 30% (donut lower bound)", dict(ER=30)),
    ("alpha + water table (both conservative elements)", dict(fix=True, WT=True)),
    ("alpha + water table + M 8.0", dict(fix=True, WT=True, M=8.0)),
    ("alpha + water table + M 8.7", dict(fix=True, WT=True, M=8.7)),
    ("alpha + water table + M 8.0 + ER 48%", dict(fix=True, WT=True, M=8.0, ER=48)),
    ("alpha + water table + M 8.7 + ER 48%", dict(fix=True, WT=True, M=8.7, ER=48)),
    ("Water table + M 8.0 (alpha as printed)", dict(WT=True, M=8.0)),
]
print("\nTABLE 10 - substitutions through the reconstructed chain")
single = {}
for name, kw in CASES:
    d, rat, ov = run(**kw)
    single[name] = rat
    print(f"  {name:50} n={len(d):3}  ratio x{rat:.3f}  overridden "
          f"{st.median(a for _, a, _ in ov):.3f} -> {st.median(c for *_, c in ov):.3f}  "
          f">=1: {sum(1 for *_, c in ov if c >= 1)} of {len(ov)}")

# ---- who is in the substitution population, and the measured water levels it uses
d0, _, ov0 = run()
inpop = {ID(r) for r, *_ in d0}
out = [r for r in ALLC if ID(r) not in inpop]
scan = [r for r in out if "rendered" in r.get("source", "")]
rest = [r for r in out if r not in scan]
print(f"\nPOPULATION  {len(d0)} of {len(ALLC)} depths, {len(ov0)} of {len(OVR0)} overridden. Excluded "
      f"{len(out)}: Bridge 33, read visually without intermediate values, {len(scan)} ({sum(1 for r in scan if r in OVR0)} overridden); "
      f"text-layer lacking C_E or fines content {len(rest)} "
      f"({sum(1 for r in rest if r['conclusion'] == 'L')} declared liquefiable, "
      f"{sum(1 for r in rest if r in OVR0)} overridden)")
g_used = sorted({gwl_of(r) for r, *_ in d0 if gwl_of(r) is not None})
print(f"  measured water levels in the population: {g_used[0]:.2f}-{g_used[-1]:.2f} m; "
      f"lowest non-zero {min(g for g in g_used if g > 0):.2f} m; "
      f"overridden depths at a borehole recording 0.00 m: "
      f"{sum(1 for r, *_ in ov0 if gwl_of(r) == 0)}")
dry_all = [r for r, *_ in d0 if is_dry(r)]
dry_ov = [r for r, *_ in ov0 if is_dry(r)]
print(f"  ABOVE THE MEASURED LEVEL (unsaturated under the water-table substitution): {len(dry_all)} of "
      f"{len(d0)} depths, {len(dry_ov)} of {len(ov0)} overridden (depths "
      f"{min(f(r['depth_m']) for r in dry_ov)}-{max(f(r['depth_m']) for r in dry_ov)} m, levels "
      f"{min(gwl_of(r) for r in dry_ov):.2f}-{max(gwl_of(r) for r in dry_ov):.2f} m). Every water-table "
      f"case below is computed on the {len(d0) - len(dry_all)} depths below the level "
      f"({len(ov0) - len(dry_ov)} overridden).")

# ---- the naive half-correction of the water table (CSR only, C_N penalty forgotten)
_, _, ovn = run(WT=True, csr_only=True)
_, _, ovf = run(WT=True)
print(f"\nWater table, CSR only: {sum(c >= 1 for *_, c in ovn)} of {len(ovn)} reach FOS>=1; "
      f"full treatment: {sum(c >= 1 for *_, c in ovf)} (max {max(c for *_, c in ovf):.3f})")

# ---- TABLE 9: rescue grid. FOS is exactly proportional to 1/a_max (CSR linear in a_max),
#      so the grid at another acceleration is a rescaling of the grid at 0.36 g.
def rescued(amax=0.36, **kw):
    _, _, ov = run(**kw)
    return sum(1 for *_, c in ov if c * 0.36 / amax >= 1)


# 0.324 and 0.276 g: 2/3 * S * Z with S = 1.35 (site class SD) and 1.15 (SC), as Islam et al.
# (2023) describe the code's surface value; 0.24 g is 2/3 * Z, the design-basis value on rock.
for amax in (0.36, 0.324, 0.276, 0.24):
    print(f"\nTABLE 11 - overridden depths reaching FOS>=1, a_max = {amax} g "
          f"(cells: ER 78 / 70 / 60 / 48 / 30 %). Water-table cases count the "
          f"{len(ov0) - len(dry_ov)} overridden depths below the measured level; the other "
          f"{len(dry_ov)} are above it.")
    for label, kw0 in (("alpha + water table", dict(fix=True, WT=True)),
                       ("alpha only", dict(fix=True)), ("water table only", dict(WT=True)),
                       ("neither", {})):
        cells = []
        for M in (6.5, 7.0, 7.5, 8.0, 8.7):
            cells.append(f"M {M}: " + " / ".join(str(rescued(amax, M=M, ER=ER, **kw0))
                                                 for ER in (78, 70, 60, 48, 30)))
        print(f"  {label:20} " + "   ".join(cells))

# ---- sensitivity to the scaling factor itself (MSF multiplies FOS directly)
_, _, ov8 = run(fix=True, WT=True, M=8.0)
m36 = st.median(c for *_, c in ov8)
m24 = m36 * 0.36 / 0.24
print(f"\nMSF SENSITIVITY  M 8.0, both conservative elements corrected: median overridden FOS "
      f"{m36:.3f} at 0.36 g, {m24:.3f} at 0.24 g -> MSF would need x{1 / m36:.2f} / "
      f"x{1 / m24:.2f} for the median depth to reach 1;  MSF(7.5)/MSF(8.0) = "
      f"{MSF(7.5) / MSF(8.0):.3f}")

# ---- TABLE 12 and the design-basis reading, on the reported arithmetic (all overridden depths)
fos183 = [f(r["FOS"]) for r in OVR]
for a_ in (0.20, 0.15, 0.10, 0.05):
    k_ = sum(1 for x in fos183 if x * 0.36 / a_ < 1)
    print(f"TABLE 13  a_max {a_:.2f} g: {k_} of {len(fos183)} still FOS<1 ({100 * k_ / len(fos183):.1f} %)")
print(f"\nReported arithmetic at 0.24 g: {sum(1 for x in fos183 if x * 0.36 / 0.24 < 1)} of "
      f"{len(fos183)} overridden depths still FOS<1; a_max for FOS=1 median "
      f"{st.median(0.36 * x for x in fos183):.3f} g (range {0.36 * min(fos183):.3f}-"
      f"{0.36 * max(fos183):.3f})")

# ---- median a_max at which the 160 recomputable overridden depths reach FOS = 1, by case
print(f"\nMEDIAN a_max (g) FOR FOS = 1: {len(ov0)} recomputable overridden depths; the water-table "
      f"row uses the {len(ov0) - len(dry_ov)} below the measured level")
for label, kw0 in (("reported arithmetic", {}), ("alpha corrected", dict(fix=True)),
                   ("alpha + water table", dict(fix=True, WT=True))):
    cells = []
    for M in (6.5, 8.0, 8.7):
        _, _, ov = run(M=M, **kw0)
        cells.append(f"M {M}: {st.median(0.36 * c for *_, c in ov):.3f}")
    print(f"  {label:22} " + "   ".join(cells))

# ---- interaction: joint (through the chain) vs product of single-factor ratios
print("\nINTERACTION - joint vs product of single-factor median ratios (depths below the measured "
      "level; E = ER 48 %)")
# computed on the depths below the measured level, so that every factor shares one population
S = {"a": run(wet=True, fix=True)[1], "W": run(wet=True, WT=True)[1], "M": run(wet=True, M=8.0)[1],
     "E": run(wet=True, ER=48)[1]}
KW = {"a": dict(fix=True), "W": dict(WT=True), "M": dict(M=8.0), "E": dict(ER=48)}
for combo in ("W+M", "a+M", "a+W", "a+E", "W+E", "a+W+M", "W+M+E", "a+W+M+E"):
    kw, prod = {}, 1.0
    for k in combo.split("+"):
        kw.update(KW[k])
        prod *= S[k]
    j = run(wet=True, **kw)[1]
    print(f"  {combo:8} joint x{j:.3f}  product x{prod:.3f}  interaction {100 * (j / prod - 1):+5.1f}%")

# ---- a_max inversion (FOS proportional to 1/a_max) with the alpha slip corrected
_, _, ova = run(fix=True)
need_fix = sorted(0.36 * c for *_, c in ova)
need_rep = sorted(0.36 * a for _, a, _ in ova)
print(f"\na_max for FOS=1 on these {len(ova)} overridden depths: reported arithmetic median "
      f"{st.median(need_rep):.3f} g; alpha corrected median {st.median(need_fix):.3f} g "
      f"(range {need_fix[0]:.3f}-{need_fix[-1]:.3f})")

# ---- scenario demand (Results 3.6, result 2). FOS is proportional to MSF / a_max, so a scenario's
# demand on a given soil can be compared through a_max / MSF with the reports' own MSF relation.
# The scenario values are LITERATURE: Rahman et al. 2015 (Mw 7.0, 0.15 g), Ansary et al. 2024
# (M 7.5, 0.21 g), Rahman & Siddiqua 2017 (Mw 7.5, 0.15-0.25 g; Dhaka, Chittagong, Sylhet),
# Hossain et al. 2020 (Mw 8.0, 0.36 g); the reports use M 6.5 at 0.36 g.
print("\nTABLE 12 - SCENARIO DEMAND a_max / MSF (MSF = 10^2.24 / M^2.56, the reports' own relation)")
_scen = [("Rahman et al. (2015), Dhaka", 7.0, 0.15), ("Ansary et al. (2024), Dhaka", 7.5, 0.21),
         ("Rahman & Siddiqua (2017), lower end", 7.5, 0.15), ("Rahman & Siddiqua (2017), upper end", 7.5, 0.25),
         ("the reports", 6.5, 0.36), ("Hossain et al. (2020), Moulvibazar", 8.0, 0.36)]
_rep = 0.36 / MSF(6.5)
for _lab, _M, _a in _scen:
    _d = _a / MSF(_M)
    print(f"  {_lab:36} M {_M:3.1f}  a_max {_a:.2f} g  MSF {MSF(_M):.3f}  a_max/MSF {_d:.3f}  "
          f"(x{_d / _rep:.2f} the reports')")

# ---- K_sigma: the reports' text requires it for depth > 15 m; the sheets never apply it
print("\nK_SIGMA (text: required for depth > 15 m; K = min(1, (sigma'/10)^(f-1)); sheets use 1)")
for fexp in (0.7, 0.8):
    deep = [fos(r, ks="text", fexp=fexp) / fos(r) for r, a in base
            if fos(r) is not None and f(r["depth_m"]) > 15 and fos(r) not in (0, INF)]
    print(f"  f = {fexp}: as reported, FOS x{min(deep):.3f}-x{max(deep):.3f} at the {len(deep)} "
          f"depths below 15 m in the population")
    for amax in (0.36, 0.24):
        cells = []
        for M in (6.5, 8.0):
            _, _, ovk = run(fix=True, WT=True, M=M, ks="text", fexp=fexp)
            cells.append(f"M {M}: " + " / ".join(
                str(sum(1 for *_, c in run(fix=True, WT=True, M=M, ER=ER, ks="text", fexp=fexp)[2]
                        if c * 0.36 / amax >= 1)) for ER in (78, 70, 60, 48, 30)))
        print(f"  f = {fexp}, alpha + water table, a_max {amax} g: " + "   ".join(cells))

# ---- the supported count under the code's own thresholds (BNBC 2020 Part 6 Sec 3.9.5)
s_code_ll = {ID(r) for r, ll, _ in LLT if ll > 36}
s_code_cl = {ID(r) for r in OVR if CLAY.get(ID(r)) is not None and CLAY[ID(r)] > 10}
print(f"\nSUPPORT UNDER THE CODE'S THRESHOLDS (LL > 36 %, or clay > 10 %): "
      f"{len(s_code_ll | s_code_cl)} of {n_ov} (LL {len(s_code_ll)}, clay {len(s_code_cl)}, both "
      f"{len(s_code_ll & s_code_cl)}); declared criterion: {cnt['supported']}")

# ---- the acceleration at which a larger magnitude matches the reports' own demand
print("\nMATCHING ACCELERATION  a_max at which M produces the reports' demand (0.36 g at M 6.5)")
for M in (7.0, 7.5, 8.0, 8.15, 8.35, 8.4, 8.7):
    print(f"  M {M:4}: {0.36 * MSF(M) / MSF(6.5):.3f} g")

# ---- K_sigma applied by stress (sigma' > Pa, capped at 1), as Youd et al. (2001) recommend
print("\nK_SIGMA BY STRESS (wherever sigma' > Pa = 10 t/m^2; capped at 1)")
for fexp in (0.7, 0.8):
    for amax in (0.36, 0.24):
        cells = []
        for M in (6.5, 8.0):
            cells.append(f"M {M}: " + " / ".join(
                str(sum(1 for *_, c in run(fix=True, WT=True, M=M, ER=ER, ks="stress", fexp=fexp)[2]
                        if c * 0.36 / amax >= 1)) for ER in (78, 70, 60, 48, 30)))
        print(f"  f = {fexp}, alpha + water table, a_max {amax} g: " + "   ".join(cells))
