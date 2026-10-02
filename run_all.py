#!/usr/bin/env python3
"""Run every analysis script and compare its printed output with outputs/reference/.

    python run_all.py                     run all scripts and compare with the reference
    python run_all.py --write-reference   (maintainer) store the current outputs as the reference

Each script's printed output is written to outputs/<script>_output.txt and the figures to
outputs/figures/. The exit status is 0 only if every script runs and matches its reference.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "outputs")
REF = os.path.join(OUT, "reference")
SCRIPTS = ["ds06_dataset_checks", "ds06_tables7_8", "ds06_table4", "ds06_coverage", "ds06_f1_audit",
           "ds06_o4_flippoints", "ds06_wn_bounds", "ds06_repeated_values", "ds06_figures_bee"]


def main():
    write_ref = "--write-reference" in sys.argv
    env = dict(os.environ, PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
    os.makedirs(OUT, exist_ok=True)
    failed = 0
    for name in SCRIPTS:
        res = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", name + ".py")], cwd=ROOT, env=env,
                             capture_output=True, text=True, encoding="utf-8")
        out_path = os.path.join(OUT, name + "_output.txt")
        with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(res.stdout)
        if res.returncode != 0:
            print(f"{name:22} FAILED (exit {res.returncode})\n{res.stderr[-2000:]}")
            failed += 1
            continue
        ref_path = os.path.join(REF, name + "_output.txt")
        if write_ref:
            os.makedirs(REF, exist_ok=True)
            shutil.copyfile(out_path, ref_path)
            print(f"{name:22} reference written")
            continue
        if not os.path.exists(ref_path):
            print(f"{name:22} no reference output")
            failed += 1
            continue
        with open(ref_path, encoding="utf-8") as fh:
            same = fh.read().replace("\r\n", "\n") == res.stdout.replace("\r\n", "\n")
        print(f"{name:22} {'matches the reference' if same else 'DIFFERS from the reference'}")
        failed += 0 if same else 1
    if write_ref:
        dst = os.path.join(REF, "figures")
        os.makedirs(dst, exist_ok=True)
        for f in sorted(os.listdir(os.path.join(OUT, "figures"))):
            if f.endswith((".png", ".pdf")):
                shutil.copyfile(os.path.join(OUT, "figures", f), os.path.join(dst, f))
    if write_ref and not failed:
        print("reference outputs written")
    elif failed:
        print(f"{failed} script(s) failed or differ from the reference")
    else:
        print("all outputs match the reference")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
