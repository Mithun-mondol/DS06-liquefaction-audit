#!/usr/bin/env python3
# Public release (2026-10-02): reads the anonymised CSVs in ../data, whose "report" column already holds
# the structure labels used in the paper; the label map that once translated report file names is therefore empty.
"""
BEE submission version of ds06_figures.py (2026-10-01). Same data, same plotted values.
Changes for Springer artwork rules only: lettering 8.5-9 pt, no transparency (EPS),
file names Fig1-Fig3, widths kept within 174 mm / 84 mm. Original script unchanged.
"""
"""
Figures 1-3 for the DS-06 audit paper. Every plotted value is derived here from
the extracted CSVs - nothing is hard-coded - and the script prints the numbers
it plots so they can be checked against the article before use.

Fig 1  Reported conclusion against computed FOS, every depth carrying both (366 after the
       conclusion fix of 2026-09-28, project log, correction C11), CL emphasised.
Fig 2  Disagreement onsets for the indeterminate overridden depths, on a
       moisture-content axis, with the plausible ranges as bands; plus the one
       depth where w_n was measured.
Fig 3  Share of overridden depths still computing FOS < 1 as a_max is reduced.

Onset definition (CORRECTED 2026-09-27, project log, correction C7). The audit question is
when the alternative criterion contradicts the report's NON-LIQUEFIABLE verdict.
Bray & Sancio (2006) call a soil susceptible when w_n/LL > 0.85 (PI < 12) or
> 0.80 (12 <= PI <= 18), and not susceptible for PI > 18. So the onset is
t*LL for every depth. The earlier version used 0.90*LL where LL < 35, which
conflated "Chinese vs Bray & Sancio" with "report vs Bray & Sancio".

Palette: reference instance, validated on white (slot 1 blue, slot 2 orange:
CVD dE 24.7, normal-vision dE 33.6, both >= 3:1). CL/other is distinguished by
FILL as well as hue, because blue and the muted grey sit at similar greyscale
luminance (0.188 vs 0.242) and journals still print in greyscale.
"""
import csv, math, statistics as st
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))  # folder holding the CSVs
FIG = os.environ.get("DS06_FIGS", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs", "figures"))
os.makedirs(FIG, exist_ok=True)
A_REPORT = 0.36
W1, W2, W3 = (float(v) for v in os.environ.get("DS06_W", "6.6,6.75,3.2").split(","))

# ---- palette (reference instance) and chrome
BLUE, ORANGE = "#2a78d6", "#eb6834"
MUTED, INK, INK2 = "#898781", "#0b0b0b", "#52514e"
GRID, AXIS = "#e1e0d9", "#c3c2b7"
BAR = "#d4e4f7"  # BLUE at 20 % over white, opaque (EPS has no transparency)
BAND_WIDE, BAND_NARROW = "#f3f2ee", "#e4e2da"

plt.rcParams.update({
    "font.family": "Liberation Sans", "font.size": 8.5,
    "mathtext.fontset": "custom", "mathtext.rm": "Liberation Sans",
    "mathtext.it": "Liberation Sans:italic", "mathtext.bf": "Liberation Sans:bold",
    "mathtext.cal": "Liberation Sans", "mathtext.sf": "Liberation Sans",
    "axes.labelsize": 9, "xtick.labelsize": 8.5, "ytick.labelsize": 8.5,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.6,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "savefig.dpi": 600, "figure.dpi": 150,
})


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
moi = list(csv.DictReader(open(f"{OUT}/ds06_moisture.csv", encoding="utf-8")))
bhs = list(csv.DictReader(open(f"{OUT}/ds06_boreholes.csv", encoding="utf-8")))

# public short names - structure and chainage only; no firm is identifiable
SHORT = []  # labels are already in the data


def short(rep):
    for key, name in SHORT:
        if key in rep:
            return name
    return rep


rows = [r for r in liq if f(r.get("FOS")) is not None and r.get("conclusion")]
over = [r for r in rows if r["conclusion"] == "NL" and f(r["FOS"]) < 1.0]
print(f"Fig 1 population: {len(rows)} depths; overridden {len(over)}")

# ============================================================== FIGURE 1
fig, ax = plt.subplots(figsize=(W1, 2.6))
rng = np.random.default_rng(7)                       # seeded: reproducible jitter
ypos = {"NL": 1.0, "L": 0.0}
counts = defaultdict(int)
yjit = {}                                              # jittered y of each plotted depth
for cl in (False, True):                              # draw CL on top
    xs, ys = [], []
    for r in rows:
        is_cl = r.get("strata", "").strip().upper() == "CL"
        if is_cl != cl:
            continue
        xs.append(f(r["FOS"]))
        ys.append(ypos[r["conclusion"]] + rng.uniform(-0.27, 0.27))
        yjit[id(r)] = ys[-1]
        counts[(r["conclusion"], is_cl)] += 1
    if cl:
        ax.scatter(xs, ys, s=15, facecolor=BLUE, edgecolor="white", linewidth=0.4,
                   zorder=3, label="CL (low-plasticity clay)")
    else:
        ax.scatter(xs, ys, s=15, facecolor="none", edgecolor=MUTED, linewidth=0.8,
                   zorder=2, label="All other classes")
ax.axvline(1.0, color=INK2, lw=0.8, zorder=1)
ax.text(1.0, 1.52, "  FOS = 1.0", color=INK2, fontsize=8.5, va="center", ha="left")
nl_hi = sorted((r for r in rows if r["conclusion"] == "NL" and f(r["FOS"]) >= 1.0),
               key=lambda r: f(r["FOS"]))
for r in nl_hi:                                        # label each point where it is drawn
    x_, y_ = f(r["FOS"]), yjit[id(r)]
    ax.annotate(f"{r['strata']}, {x_:.2f}", xy=(x_, y_), xytext=(x_ + 0.035, y_ - 0.2),
                fontsize=8.5, color=INK2, ha="left", va="center",
                arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.6, shrinkA=0, shrinkB=2))
n_nl = counts[("NL", True)] + counts[("NL", False)]
n_l = counts[("L", True)] + counts[("L", False)]
ax.set_yticks([0, 1])
ax.set_yticklabels([f"Declared liquefiable\n(n = {n_l})", f"Declared non-liquefiable\n(n = {n_nl})"])
ax.set_ylim(-0.55, 1.62)
ax.set_xlim(0, 1.35)
ax.set_xticks(np.arange(0, 1.31, 0.2))
ax.set_xlabel("Factor of safety computed by the report's own triggering procedure")
ax.xaxis.grid(True, color=GRID, lw=0.5)
ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
h, l = ax.get_legend_handles_labels()
ax.legend(h[::-1], l[::-1], loc="lower center", bbox_to_anchor=(0.42, 1.0), ncol=2,
          frameon=False, fontsize=8.5, handletextpad=0.3, columnspacing=1.6)
fig.tight_layout()
for ext in ("pdf", "png", "eps"):
    fig.savefig(f"{FIG}/Fig1.{ext}", bbox_inches="tight")
plt.close(fig)
print(f"  NL: CL {counts[('NL', True)]}, other {counts[('NL', False)]}   "
      f"L: CL {counts[('L', True)]}, other {counts[('L', False)]}   "
      f"NL with FOS>=1: {[(r['strata'], r['FOS']) for r in nl_hi]}")

# ============================================================== FIGURE 2 data
IDX = {}
for a in att:
    if f(a.get("LL_pct")):
        IDX[ID(a)] = (f(a["LL_pct"]), f(a.get("PI_pct")))
for r in lab:
    if f(r.get("LL_pct")):
        IDX[ID(r)] = (f(r["LL_pct"]), f(r.get("PI_pct")))
WN = {}
for r in moi:
    if f(r.get("wn_pct")):
        WN[ID(r)] = f(r["wn_pct"])
for r in lab:
    if f(r.get("nmc_pct")):
        WN[ID(r)] = f(r["nmc_pct"])


def t_of(PI):
    if PI is None or PI > 18:
        return None
    return 0.85 if PI < 12 else 0.80


cl_wn = [f(r["nmc_pct"]) for r in lab if f(r.get("nmc_pct")) and f(r.get("depth_m"))
         and f(r["depth_m"]) <= 20 and (r.get("soil_type", "") or "").upper().startswith(("CL", "ML"))]
wsat = [100 * f(r["e0"]) / f(r["specific_gravity"]) for r in lab
        if f(r.get("e0")) and f(r.get("specific_gravity"))]
WIDE = (min(min(cl_wn), min(wsat)), max(max(cl_wn), max(wsat)))
NARROW = (min(wsat), max(wsat))
MED = st.median(cl_wn)

indet, measured = [], []
for r in over:
    k = ID(r)
    if k not in IDX:
        continue
    LL, PI = IDX[k]
    t = t_of(PI)
    if t is None:
        continue
    onset = t * LL
    rec = dict(k=k, LL=LL, PI=PI, t=t, onset=onset, old=(0.90 * LL if LL < 35 else onset),
               fos=f(r["FOS"]), wn=WN.get(k), lt35=LL < 35)
    (measured if k in WN else indet).append(rec)

print(f"\nFig 2 / Objective 4, CORRECTED onset t*LL:")
print(f"  plausible range {WIDE[0]:.1f}-{WIDE[1]:.1f}%, e0/Gs range {NARROW[0]:.1f}-{NARROW[1]:.1f}%, "
      f"median measured w_n {MED:.1f}%")
for d in sorted(indet, key=lambda d: d["onset"]):
    chg = "" if abs(d["old"] - d["onset"]) < 1e-9 else f"   (was {d['old']:.1f} - CHANGED)"
    print(f"  {short(d['k'][0]):17} {d['k'][1]} {d['k'][2]:>5} m  LL {d['LL']:5.1f} PI {d['PI']:5.1f} "
          f"t {d['t']:.2f}  onset {d['onset']:5.2f}%{chg}")
for d in measured:
    print(f"  MEASURED: {short(d['k'][0])} {d['k'][1]} {d['k'][2]} m onset {d['onset']:.2f}%, "
          f"w_n {d['wn']:.2f}% -> {'DISAGREE' if d['wn'] > d['onset'] else 'agree'}")

print("\n  envelope sensitivity (corrected):")
for name, (lo, hi) in [("plausible", WIDE), ("e0/Gs range", NARROW),
                       ("25-35%", (25.0, 35.0)), ("30-35%", (30.0, 35.0))]:
    ins = sum(1 for d in indet if lo <= d["onset"] <= hi)
    below = sum(1 for d in indet if d["onset"] < lo)
    above = sum(1 for d in indet if d["onset"] > hi)
    print(f"    {name:16} {lo:5.1f}-{hi:5.1f}%: indeterminate {ins}, "
          f"always contradicted {below}, always supported {above}")

# ============================================================== FIGURE 2
order = sorted(indet, key=lambda d: d["onset"])
fig, ax = plt.subplots(figsize=(W2, 4.1))
X0, X1 = 15, 50                                  # the plausible range reaches 47.8 %
ax.axvspan(*WIDE, color=BAND_WIDE, zorder=0, lw=0)
ax.axvspan(*NARROW, color=BAND_NARROW, zorder=0, lw=0)
ax.axvline(MED, color=INK2, lw=0.7, zorder=3)
labels, ys = [], []
y = 0
for d in order:
    ys.append(y)
    ax.barh(y, X1 - d["onset"], left=d["onset"], height=0.46, color=BAR,
            lw=0, zorder=2)
    ax.scatter([d["onset"]], [y], marker="D", s=20, facecolor=BLUE, edgecolor="white",
               linewidth=0.5, zorder=4)
    dag = " †" if d["lt35"] else ""
    labels.append(f"{short(d['k'][0])} · {d['k'][1]} · {d['k'][2]:.1f} m"
                  f"   LL {d['LL']:.0f}, PI {d['PI']:.0f}{dag}")
    y += 1
y += 0.6                                           # gap before the measured row
for d in measured:
    ys.append(y)
    ax.barh(y, X1 - d["onset"], left=d["onset"], height=0.46, color=BAR,
            lw=0, zorder=2)
    ax.scatter([d["onset"]], [y], marker="D", s=20, facecolor=BLUE, edgecolor="white",
               linewidth=0.5, zorder=4)
    ax.scatter([d["wn"]], [y], marker="o", s=30, facecolor=ORANGE, edgecolor="white",
               linewidth=0.6, zorder=5)
    ax.text(d["wn"], y - 0.34, f"measured w$_n$ {d['wn']:.1f} %", va="bottom", ha="center",
            fontsize=8.5, color=INK2)
    labels.append(f"{short(d['k'][0])} · {d['k'][1]} · {d['k'][2]:.1f} m"
                  f"   LL {d['LL']:.0f}, PI {d['PI']:.0f}  (measured)")
    y += 1
ax.set_yticks(ys)
ax.set_yticklabels(labels)
ax.invert_yaxis()
ax.set_xlim(X0, X1)
ax.set_ylim(y - 0.4, -0.75)
ax.set_xlabel("Natural moisture content, w$_n$ (%)")
ax.xaxis.grid(True, color=GRID, lw=0.5)
ax.set_axisbelow(True)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
# BEE version: band and median-line labels moved from in-plot text into the legend
# (at 8.5 pt the three stacked labels overlapped); wording and values unchanged.
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker="D", ls="", markerfacecolor=BLUE, markeredgecolor="white",
                  markersize=5, label="onset: Bray & Sancio contradicts the report's verdict"),
           Patch(facecolor=BAR, label="w$_n$ at which the verdict is contradicted"),
           Line2D([], [], marker="o", ls="", markerfacecolor=ORANGE, markeredgecolor="white",
                  markersize=5.5, label="measured w$_n$"),
           Patch(facecolor=BAND_WIDE, edgecolor=AXIS, lw=0.4,
                 label=f"plausible range {WIDE[0]:.1f}–{WIDE[1]:.1f} %"),
           Patch(facecolor=BAND_NARROW, edgecolor=AXIS, lw=0.4,
                 label=f"range of e$_0$/G$_s$ {NARROW[0]:.1f}–{NARROW[1]:.1f} %"),
           Line2D([], [], color=INK2, lw=0.9, label=f"median measured {MED:.1f} %")]
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=2,
           frameon=False, fontsize=8.5, handletextpad=0.5, columnspacing=2.0, labelspacing=0.45)
fig.tight_layout(rect=(0, 0.165, 1, 1))
for ext in ("pdf", "png", "eps"):
    fig.savefig(f"{FIG}/Fig2.{ext}", bbox_inches="tight")
plt.close(fig)

# ============================================================== FIGURE 3
need = sorted(A_REPORT * f(r["FOS"]) for r in over)
n = len(need)
xs = np.linspace(0, 0.40, 801)
share = [100.0 * sum(1 for a in need if a < x) / n for x in xs]
fig, ax = plt.subplots(figsize=(W3, 2.7))
ax.plot(xs, share, color=BLUE, lw=1.3, solid_joinstyle="round", solid_capstyle="round", zorder=3)
ax.axvline(A_REPORT, color=INK2, lw=0.8, zorder=2)
ax.text(A_REPORT - 0.006, 8, "design value\n0.36 g", ha="right", va="bottom", fontsize=8.5, color=INK2)
med = st.median(need)
ax.scatter([med], [50], s=22, facecolor=BLUE, edgecolor="white", linewidth=0.6, zorder=4)
ax.annotate(f"half still below 1\nat {med:.3f} g", xy=(med, 50), xytext=(med + 0.035, 38),
            fontsize=8.5, color=INK2, ha="left", va="center",
            arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.6))
ax.set_xlim(0, 0.40)
ax.set_ylim(0, 104)
ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4])
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_xlabel("Peak ground acceleration assumed, a$_{max}$ (g)")
ax.set_ylabel("Overridden depths still\ncomputing FOS < 1 (%)")
ax.grid(True, color=GRID, lw=0.5)
ax.set_axisbelow(True)
fig.tight_layout()
for ext in ("pdf", "png", "eps"):
    fig.savefig(f"{FIG}/Fig3.{ext}", bbox_inches="tight")
plt.close(fig)
print(f"\nFig 3: {n} overridden depths; a_max for FOS=1 min {need[0]:.3f} median {med:.3f} "
      f"max {need[-1]:.3f} g")
for x in (0.05, 0.10, 0.15, 0.20):
    k = sum(1 for a in need if a < x)
    print(f"  at {x:.2f} g: {k} of {n} ({100.0*k/n:.1f}%) still FOS < 1")
print("\nwrote Fig1, Fig2, Fig3 (.pdf + .png + .eps)")
