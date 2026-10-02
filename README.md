# DS-06 liquefaction audit: dataset and analysis scripts

Data and code for the article

> Mondol M. *What the site investigation can and cannot support: an audit of design-stage liquefaction assessment on a Bangladeshi highway project.* Submitted to *Bulletin of Earthquake Engineering*. (Full reference and DOI to be added on publication.)

The article audits the design-stage liquefaction assessment of package DS-06 of the Dhaka–Sylhet National Highway (N2) four-lane improvement, Bangladesh (client: Roads and Highways Department). This repository holds the per-depth dataset extracted from the package's ten sub-soil investigation reports (30 boreholes, 2023–2025), and the Python scripts that recompute the dataset checks and the results reported in the article.

## Contents

```
data/                 seven CSV files; data dictionary in data/README.md
scripts/              analysis scripts (Python 3)
outputs/reference/    the verified output of every script, and Figs. 1–3 of the article
run_all.py            runs every script and compares its output with outputs/reference/
```

## Reproducing the results

```
pip install -r requirements.txt
python run_all.py
```

`run_all.py` runs each script, writes its printed output to `outputs/` and the figures to `outputs/figures/`, and reports whether each output matches the verified copy in `outputs/reference/`. Tested with Python 3.10.12, NumPy 2.2.6 and Matplotlib 3.10.9; only the figure script needs NumPy and Matplotlib. The figures use the Liberation Sans font if it is installed; otherwise Matplotlib substitutes another font with a warning, which changes no number.

| Script | Recomputes (numbering of the article) |
|---|---|
| `ds06_dataset_checks.py` | Table 1, rows 1–5: N = blow₂ + blow₃, laboratory and computation-sheet N against the borelog N, the re-derived equations, and r_d |
| `ds06_tables7_8.py` | Tables 3, 5, 6 and 9–13; the class rule; validation of the reconstructed relations (Table 1, row 5); the K_σ, magnitude-scaling and interaction sensitivities; the accelerations at which larger magnitudes match the reports' demand |
| `ds06_table4.py` | Table 4 (the four abutment boreholes of Bridge 33) |
| `ds06_coverage.py` | Index-test coverage at the overridden depths (Section 3.2) |
| `ds06_f1_audit.py` | The two depths at which the declared criterion is evaluable (Table 7) |
| `ds06_o4_flippoints.py` | The moisture contents at which the Bray–Sancio criterion changes the verdict (Section 3.4) |
| `ds06_wn_bounds.py` | The bound on moisture content from void ratio and specific gravity (Section 3.4) |
| `ds06_repeated_values.py` | Laboratory values printed identically for samples of different boreholes (Section 3.2), and their effect on the supported verdicts and on the worked example of Section 3.3 |
| `ds06_figures_bee.py` | Figs. 1–3, and the moisture-range sensitivity of Table 8 |

The scripts print structure labels only. Their printed table labels follow the article's numbering.

## How the dataset was built and checked

Header fields were read from the PDF text layer, and table bodies from word coordinates with columns detected page by page. One report (Bridge 33) differs: its borehole logs are scans without a text layer, and its computation sheets and laboratory summaries are rotated pages whose text layer reads in mirrored order and was not detected at first. Optical character recognition was tried on these pages and rejected, and the numeric columns of the borehole logs and computation sheets were rendered as separate strips and read visually with the image input of a large language model (Claude, Anthropic). Every recovered row was then checked, and nothing was written unless every check passed. The computation sheets' text layer, decoded later, agrees with every value read visually (504 of 504 values at 52 depths), and the Bridge 33 laboratory summaries were extracted from it; their N values agree with those read from the borehole logs at all 120 samples. The checks are listed in Table 1 of the article; rows 1–5 can be recomputed from this dataset with `ds06_dataset_checks.py` and `ds06_tables7_8.py`. Rows 6 and 7 (the conclusion column re-read from the rendered pages, and the Bridge 33 values compared with the text layer) need the source reports.

## Anonymisation, and what is not included

- As in the article, the geotechnical contractor, the supervising consultant and their staff are not named. The report file names, which carry firm designations, are replaced by the structure labels used in the article (column `report`).
- Borehole coordinates are not included; locations are given by chainage.
- The source reports are the client's documents and are not reproduced. The scripts that extracted the data from them, and the script that compared the report text with the computation sheets (Table 14 of the article), work on those documents and are not included.

## Corrections relative to the extraction

- **Laboratory summaries** (`ds06_lab.csv`, corrected on 2 October 2026, before submission). The first extraction read summary rows only below a fixed position on the page, which dropped the first three to six samples (1.5–9.0 m) of every borehole, and it missed the Bridge 33 summaries entirely. The corrected file has 988 rows instead of 746. All 241 added rows that carry an N agree with the borelog N, and the 34 added moisture contents that also have a standalone sheet agree with it. The correction also captures the direct-shear friction angle on 35 rows where the first pass missed it (a variant of the rotated column label). The article reports the corrected counts.
- **Bridge 33 moisture sheets** (`ds06_moisture.csv`). The sheets print the borehole as AB-01 or AB-02, without the side. Each sheet's value appears, at the same depth, in the laboratory summary of exactly one of the two boreholes of that name, and `borehole` gives the borehole so identified.
- **α and β of the fines correction** (`ds06_liquefaction_rows.csv`). On 312 rows the extraction recorded the printed β in the α column, and the printed α was not captured. The release stores that value as `beta_printed` and leaves `alpha_printed` blank on those rows; both are present on 26 rows. α can be recovered as (N₁)₆₀cs − β (N₁)₆₀; at a fines content of 35 % or more it is 0.50 on every row where this can be done (0.49–0.51 with the printed rounding), the value the article discusses in Section 3.6.
- **`CB`**: 10 rows on which the extraction captured a text label instead of the borehole-diameter correction are blank.
- **`structure`**: 14 rows of `ds06_atterberg.csv` on which the extracted structure field held a document reference instead of a structure name carry the structure label instead.

## Known features of the source data

- Culvert BC-03, BH-02 records a groundwater level of 0 m; whether this is a measured value or a missing entry cannot be told from the report (Section 4.6 of the article).
- The two-span-bridge report logs four boreholes under two structure names; the second record is flagged in `duplicate_of` (boreholes) and `duplicate_record` (SPT depths and layers). Filter on these before counting unique boreholes, depths or layers.
- **Laboratory values repeated across boreholes.** Some values in the laboratory summaries are printed identically, to two decimals, for samples of different boreholes in different reports, almost all between the two-span-bridge report and the two underpass reports; the boreholes concerned were drilled weeks to years apart and record different blow counts. The values are kept as printed. `ds06_repeated_values.py` lists them (Section 3.2 of the article).
- The 52 Bridge 33 computation rows carry only the columns that were read visually (depth, class, N, r_d, C_E, CSR, CRR, FOS, the conclusion and the header values); their intermediate values, (N₁)₆₀ among them, are blank, which is why the substitution analysis of the article excludes them.
- One layer description (Bridge 33, AB-01 (L/S), 30–45 m) comes from optical character recognition and is marked as such; its depths and USCS class are confirmed by the layer-thickness check.
- `CRR_M75`, `CRR` and `FOS` read `NA` where the computation sheet prints NA (16 rows).

## Licence

Code (`scripts/`, `run_all.py`): MIT licence, see `LICENSE`. Data (`data/`): Creative Commons Attribution 4.0 International (CC BY 4.0), see `data/LICENSE.md`.

## Citation

Please cite the article (see `CITATION.cff`; the full reference will be added on publication).

## Contact

Mithun Mondol, Earthquake Disaster Prevention & Mitigation Group, Department of Civil and Environmental Engineering, Saitama University, Saitama, Japan · mithun.mondol@gmail.com · ORCID [0000-0002-7527-0369](https://orcid.org/0000-0002-7527-0369)
