#!/usr/bin/env python3
"""
Table 4 of the article: the four abutment boreholes of Bridge 33 (Ch. 105+280-105+325),
the softest in the package. For each borehole: analysed depths (a printed conclusion and a
numeric factor of safety), depths declared liquefiable, overridden depths (declared
non-liquefiable with a computed FOS below 1.0) and the FOS range of the overrides.
"""
import csv
import os

DATA = os.environ.get("DS06_DATA", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))


def f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


with open(os.path.join(DATA, "ds06_liquefaction_rows.csv"), encoding="utf-8") as fh:
    liq = list(csv.DictReader(fh))

print("TABLE 4 - the four abutment boreholes of Bridge 33")
print(f"  {'borehole':12} {'analysed':>8} {'declared L':>10} {'overridden':>10}  FOS range of the overrides")
rows = {}
for r in liq:
    if r["report"] != "Bridge 33":
        continue
    fos = f(r["FOS"])
    if fos is None or not r["conclusion"]:
        continue
    d = rows.setdefault(r["borehole"], {"n": 0, "L": 0, "over": []})
    d["n"] += 1
    d["L"] += r["conclusion"] == "L"
    if r["conclusion"] == "NL" and fos < 1.0:
        d["over"].append(fos)
for bh in sorted(rows):
    d = rows[bh]
    rng = f"{min(d['over']):.2f}-{max(d['over']):.2f}" if d["over"] else "-"
    print(f"  {bh:12} {d['n']:8} {d['L']:10} {len(d['over']):10}  {rng}")
