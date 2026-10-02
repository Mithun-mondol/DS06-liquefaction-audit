# Data dictionary

Seven UTF-8 CSV files, one row per record, extracted from the ten sub-soil investigation reports of package DS-06 (Dhaka–Sylhet National Highway, N2, Bangladesh). Values are as printed in the reports unless stated otherwise; an empty cell means the value is not printed or was not extracted. Licence: CC BY 4.0 (`LICENSE.md`).

**Keys.** Every join is keyed on `report` + `borehole` + `depth_m`. Borehole designations repeat across reports, so a join on borehole and depth alone conflates structures.

**`report`** holds the structure label used in the article: Bridge 32, Bridge 33, Bridge 34, Bridge 35, Bridge 36, Bridge 37, Two-span bridge, VUP Ch. 103+017, VUP (DS-06), Culvert BC-03. **`structure`** is the structure name as written on the sheets. **`chainage`** is km+m along the highway.

## ds06_boreholes.csv — 34 records (30 unique boreholes)

| Column | Meaning |
|---|---|
| report, structure, borehole, chainage | as above |
| bh_depth_m | declared depth of the borehole (m) |
| rl_m | reduced level of the ground at the borehole (m) |
| gwl_m | groundwater level recorded on the borelog, measured 24 h after completion of the borehole (m below ground) |
| dia_mm | borehole diameter (mm) |
| boring_method, boring_ground | as printed |
| date_start, date_end | drilling dates (dd/mm/yyyy) |
| duplicate_of | for the four boreholes the two-span-bridge report logs under a second structure name: the first record (structure\|borehole) |

## ds06_spt.csv — 1014 rows (952 unique test depths)

| Column | Meaning |
|---|---|
| report, structure, borehole, chainage | as above |
| depth_m | test depth (m) |
| rl_m | reduced level at the test depth (m) |
| sample | sample designation |
| blow1, blow2, blow3 | blow counts for the three 6-inch (150 mm) increments |
| N | SPT N value (ASTM D-1586: blow2 + blow3) |
| refusal | refusal note, where printed instead of a plain N |
| uscs | USCS class |
| description | stratum description |
| duplicate_record | `yes` for the second record of a duplicated borehole |

## ds06_layers.csv — 255 rows (243 unique layers)

| Column | Meaning |
|---|---|
| report, structure, borehole, chainage | as above |
| top_m, bottom_m, thickness_m | layer boundaries and thickness (m) |
| uscs | USCS class |
| description | stratum description (one entry, Bridge 33 AB-01 (L/S) 30–45 m, is from optical character recognition and marked as such) |
| duplicate_record | `yes` for the second record of a duplicated borehole |

## ds06_lab.csv — 988 rows (Summary of Laboratory Test Results; all ten reports)

Values as printed. Some are printed identically for samples of different boreholes in different reports; see the main README and `scripts/ds06_repeated_values.py`.

| Column | Meaning |
|---|---|
| report, structure, borehole, chainage, sample | as above |
| depth_m | sample depth (m) |
| soil_type | USCS class |
| N | SPT N at the sample depth |
| nmc_pct | natural moisture content (%) |
| specific_gravity | specific gravity of soil solids |
| LL_pct, PL_pct, PI_pct | liquid limit, plastic limit, plasticity index (%) |
| sand_pct, silt_pct, clay_pct | grain-size fractions (%); clay is the fraction finer than 0.005 mm |
| unit_weight_kNm3 | unit weight (kN/m³) |
| ucs_strain_pct, ucs_qu_kPa | unconfined compression: strain at failure (%), strength q_u (kPa) |
| Cc, Cs, e0 | compression index, swelling index, initial void ratio |
| ds_c_kPa, ds_phi_deg | direct shear: cohesion (kPa), friction angle (degrees) |

## ds06_atterberg.csv — 23 rows (every Atterberg-limit test sheet)

| Column | Meaning |
|---|---|
| report, structure, borehole, sample | as above |
| depth_m | sample depth (m) |
| visual_class | visual classification on the sheet |
| LL_pct, PL_pct, PI_pct | liquid limit, plastic limit, plasticity index (%) |
| uscs | USCS class on the sheet |

## ds06_moisture.csv — 120 rows (every moisture-content test sheet)

Every sheet's value also appears in the laboratory summary. The Bridge 33 sheets print the borehole without its side (AB-01, AB-02); `borehole` gives the side, identified from the laboratory summary, where each sheet's value appears at exactly one of the two boreholes of that name.

| Column | Meaning |
|---|---|
| report, structure, borehole, sample | as above |
| depth_m | sample depth (m) |
| wn_pct | natural moisture content (%) |

## ds06_liquefaction_rows.csv — 390 rows (13 depths per borehole, 1.5–19.5 m)

One row per depth of the *Typical Computation of Liquefaction Potential by Simplified Method* sheets. Stresses are in t/m² and densities in t/m³ (γ_w = 1.0 t/m³), as in the reports.

| Column | Meaning |
|---|---|
| report, borehole, structure, chainage | as above |
| gwl_measured_m | groundwater level measured in the borehole (m below ground) |
| depth_m | depth (m) |
| strata | USCS class used on the sheet |
| N_observed | field SPT N on the sheet |
| fines_pct | fines content used (%) |
| saturated_density, submerged_density | densities used (t/m³) |
| sigma_total, sigma_eff | total and effective vertical stress (t/m²); total stress is printed on 158 rows |
| rd | stress reduction coefficient |
| zone_factor | zone coefficient applied as a_max (g) |
| water_table_assumed_m | water table used in the computation (m) |
| design_magnitude | design magnitude |
| energy_pct | assumed rod energy ratio (%), where printed |
| CN, CE, CB, CR, CS | overburden, energy, borehole-diameter, rod-length and sampler corrections |
| N160 | (N₁)₆₀ |
| alpha_printed, beta_printed | fines-correction coefficients as printed (see the main README: α is blank where it was not captured) |
| N160cs | (N₁)₆₀cs = α + β (N₁)₆₀ |
| CRR_M75, CRR | cyclic resistance ratio for M 7.5, and after magnitude scaling (`NA` where printed NA) |
| CSR | cyclic stress ratio |
| FOS | factor of safety CRR/CSR (`NA` where printed NA) |
| conclusion | the printed conclusion: `L` liquefiable, `NL` non-liquefiable |
| check_CSR, check_FOS, check_N160cs | `ok` where the value re-derived during extraction matched the printed one (Table 1, row 4) |
| source | how the row was read: `text layer, equations re-derived` (338 rows), or, for the 52 Bridge 33 rows, `read from rendered scan, checked against borelog N`: read visually from the rendered page, and later also checked against the page's rotated text layer (504 of 504 values agree). The Bridge 33 rows carry only the columns read visually |
