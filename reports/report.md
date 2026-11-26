# HW5 report: Ames Housing quality audit

All numbers below are produced by `make all`; the full tables are in `reports/results/`.

## 1 Provenance

`AmesHousing.txt` (De Cock, 2011) arrived as 2,930 rows × 82 tab-separated columns, matching
the dictionary. The source URL, download date, SHA-256 and terms of use are in `README.md`.
The raw file is never edited: `download.py` refuses to overwrite it, and every fix goes to
`data/processed/ames_clean.csv`.

## 2 Validation: failures on the raw file

`validate.py` checks the column set and dtype family of all 82 columns, 36 range rules,
44 allowed-value sets copied from the dictionary, and 14 cross-column rules. The raw file
fails 10 rules. The cleaned file passes all of them.

| Rule that failed on the raw file | Rows | What I did (`clean.py`) |
| --- | ---: | --- |
| Garage Yr Blt in [1864, 2010] (value 2207) | 1 | NaN. Probably 2007, but that is a guess, not data |
| MS Zoning codes `C (all)`, `I (all)`, `A (agr)` (dict: C, I, A) | 25, 2, 2 | Mapped to the dictionary code, logged |
| Neighborhood `NAmes` (dict: `Names`) | 443 | Mapped, logged |
| Bldg Type `2fmCon`, `Duplex`, `Twnhs` (dict: 2FmCon, Duplx, TwnhsI) | 62, 109, 101 | Mapped, logged. `Twnhs`→`TwnhsI` assumes "inside unit", since `TwnhsE` already exists |
| Exterior 2nd `CmentBd`, `Wd Shng`, `Brk Cmn` (Exterior 1st uses the dictionary spelling) | 126, 81, 22 | Mapped, logged |
| Sale Type `WD ` (trailing space) | 2,536 | Stripped whitespace |
| Year Remod/Add ≥ Year Built | 1 (Order 851) | Year Remod/Add → NaN; can't tell which year is wrong |
| Mas Vnr Type `None` ⇔ Mas Vnr Area = 0 | 10 | 7 rows "None" with area > 0 → type NaN; 3 rows typed with area 0 → area NaN |
| Garage Qual / Garage Cond `NA` ⇔ Garage Type `NA` | 1 each (Order 1357) | A 360 sq ft detached garage cannot be "No Garage" → NaN (unknown) |

Rules that pass on the raw file but are worth noting:
- Year Built, Year Remod/Add and Garage Yr Blt are allowed to exceed Yr Sold only for
  `Partial` sales. The dictionary says Partial means the home was "not completed when last
  assessed", i.e. a pre-construction sale (4 rows).
- The dictionary's column names differ from the file's (`Exterior 1` vs `Exterior 1st`,
  `FireplaceQu` vs `Fireplace Qu`, `Bedroom` vs `Bedroom AbvGr`). The schema follows the file.

## 3 Sentinels and structural absence

**Two loads compared.** Loading with the pandas default (`pd.read_csv(path, sep="\t")`)
turns 15,030 dictionary codes into NaN. Loading with `keep_default_na=False, na_values=[""]`
keeps those codes as strings and makes only empty cells NaN. Full table: `results/na_audit.md`.

| Column(s) | `"NA"` strings | Dictionary meaning | True unknown (empty) |
| --- | ---: | --- | ---: |
| Alley | 2,732 | No alley access | 0 |
| Bsmt Qual, Bsmt Cond, BsmtFin Type 1 | 79 each | No Basement | 1 each (Order 1342, all basement fields empty) |
| Bsmt Exposure / BsmtFin Type 2 | 79 / 79 | No Basement | 4 / 2 (incl. Order 1342) |
| Fireplace Qu | 1,422 | No Fireplace | 0 |
| Garage Type / Finish / Qual / Cond | 157 / 157 / 158 / 158 | No Garage | 0 / 2 / 1 / 1 |
| Pool QC | 2,917 | No Pool | 0 |
| Fence | 2,358 | No Fence | 0 |
| Misc Feature | 2,824 | None | 0 |
| **Mas Vnr Type: `"None"`** | 1,752 | "None" = no masonry veneer | 23 |

- **Not a single `"NA"` string in this file means "unknown".** Every true unknown is an empty
  cell, and 490 of them are in Lot Frontage.
- The default load also eats the string **`"None"`** in Mas Vnr Type. That is a real
  category: 1,752 houses with no veneer would be treated as missing.
- **Decision:** keep `"NA"` and `"None"` as explicit categories. Downstream scripts load with
  `common.load_clean`, which uses `keep_default_na=False`, so the codes survive a CSV round
  trip. One logically implied fill: for Order 1498 (no basement, Total Bsmt SF 0), the
  empty basement bath counts became 0.

**Zeros: sentinel or true zero?** Full counts are in `results/zero_counts.md`.

| Column (zeros) | Verdict | Argument |
| --- | --- | --- |
| Total Bsmt SF (79), Garage Area & Cars (157), Pool Area (2,917), Fireplaces (1,422) | **True zero, structural** | Counts match the `NA` = none codes exactly (cross rules pass) |
| Mas Vnr Area (1,748) | True zero | Pairs with type "None" (after the 10 fixes) |
| 2nd Flr SF (1,678), BsmtFin SF 1/2, Bsmt Unf SF, porches, Wood Deck, Low Qual Fin SF | True zero | One-story houses, unfinished basements, no deck. The component sums add up exactly |
| Full Bath (12) | True zero above grade | 11 of 12 have a basement full bath; the dictionary says "above grade" |
| Bedroom AbvGr (8) | True zero above grade | The dictionary excludes basement bedrooms |
| **Kitchen AbvGr (3)** | **Suspect** | All 3 have a Kitchen Qual rating (TA), so a kitchen exists. Flagged, not changed |
| **Misc Val (3 with a Misc Feature)** | **Possible sentinel** | A shed worth $0 is possible; an unrecorded value is more likely. Flagged |
| Lot Frontage (0 zeros, min 21) | — | A lot with no street frontage *cannot* be recorded as 0, which matters for Part 5 |

## 4 Keys and duplicates

| Check | Result |
| --- | --- |
| `Order` unique | Yes: row number of the file, identifies a *record* |
| `PID` unique | Yes: parcel ID, identifies a *property*. Unique here because no parcel sold twice in 2006–10 |
| Exact duplicate rows / duplicates ignoring Order / duplicate PID | 0 / 0 / 0 |
| PIDs with a leading 0 | 2,929 of 2,930 (read as int → 9 digits, and the assessor lookup breaks) |

**Key for one sale: `PID`, read as text.** In a longer panel, a house could sell twice, so
the sale key would become (PID, Yr Sold, Mo Sold). `Order` is only a position in this file.

**Lookup join.** I built a table of 28 Neighborhood codes and full names from the
dictionary, then joined it with `pd.merge(..., validate="many_to_one")`: **2,930 rows before
and after, 0 unmatched.** Before the `NAmes`→`Names` fix, those 443 rows would have come
back unmatched.

## 5 Missingness mechanism

| | Lot Frontage | Mas Vnr Area |
| --- | --- | --- |
| Share missing | 490 / 2,930 = **16.7%** | 26 / 2,930 = **0.9%** |
| Lot Config | 13% (Inside) → **49% (CulDSac)**, χ² p = 6e-35 | flat, p = 0.98 |
| Neighborhood | 0% (BrDale) → 55% (ClearCr), p = 1e-40 | concentrated in Somerst/Gilbert, p = 6e-8 |
| Lot Area (median, missing vs present) | 10,398 vs 9,248, p = 1e-12 | 9,661 vs 9,432, p = 0.55 |
| SalePrice | $173k vs $158k, p = 5e-6 | $212k vs $160k, p = 1e-5 |
| Year Built | 1976 vs 1972, p = 0.32 | **2006 vs 1973**, p = 3e-10 |

(Mann-Whitney U for numeric, chi-square for categorical; `results/missingness_*.md`.)

- **Lot Frontage: MCAR rejected → MAR on lot geometry.** Missingness tracks observed lot
  shape: cul-de-sac lots are missing almost 4× as often as inside lots, and missing lots are
  larger. The frontage of a pie-shaped cul-de-sac lot or an irregular rural lot is ill-defined,
  so it is the kind of value an assessor skips.
- **Mas Vnr Area: MCAR rejected → MAR on construction status.** 14 of the 26 are `Partial`
  sales (5.7% missing vs 0.5% for Normal), and the median build year is 2006. The house was
  not finished when it was assessed.
- **What the data cannot tell us:** these tests only compare *observed* columns. Whether a
  missing frontage would have been unusually small (MNAR) can't be checked without the
  missing values themselves, so MAR is the best supported reading, not a proven one.

**If Lot Frontage were MNAR:** the assessor records frontage only for lots that touch a
public street. Lots reached by a shared private drive or easement have frontage ≈ 0. Since 0
never appears in this file (minimum 21 ft), those lots would show up as blanks. Missingness
would then depend on the frontage value itself.

## 6 Imputation strategy and defense (at most 150 words)

| Strategy | std (23.37 before) | corr with Lot Area (0.491 before) | Distinct fills |
| --- | ---: | ---: | ---: |
| Median | 21.33 (−8.7%) | 0.363 | 1 |
| Neighborhood median | 21.72 (−7.0%) | 0.389 | 20 |
| **KNN, k=10 on (log Lot Area, Lot Config)** | **22.75 (−2.6%)** | **0.436** | 276 |

Histograms: `figures/lot_frontage_{median,neighborhood_median,KNN}.png`.

**Choice: KNN on log Lot Area and Lot Config.** Part 5 found that Lot Frontage is MAR on
lot geometry: missingness depends on Lot Config (cul-de-sacs 49%) and on Lot Area. Under MAR,
a fill is unbiased only if it conditions on the observed variables that drive the missingness.
KNN conditions on exactly those two, so a missing cul-de-sac lot is filled from similar
cul-de-sac lots rather than from the city median, which is dominated by inside lots. A single
median ignores the mechanism and collapses 490 lots onto one value, which shows as a spike in
its histogram. The neighborhood median conditions on location but not on lot shape. KNN also
costs the least: spread drops 2.6% instead of 8.7%, and correlation with Lot Area drops to
0.436 instead of 0.363. It remains a single fill and still understates uncertainty. If Part 5's
MNAR story holds, no fill from observed columns is correct.

## 7 Leakage-safe evaluation

LinearRegression on log SalePrice, 14 features (README), `KFold(5, shuffle, 5110)`:

| Variant | CV RMSE (log $) |
| --- | ---: |
| A: median Lot Frontage per SalePrice quintile, full table | 0.16243 |
| B: KNN fitted on the full table, then CV | 0.16231 |
| **C: KNN inside a Pipeline** | **0.16231** |
| reference: Lot Frontage dropped | 0.16258 |

| On the 490 filled rows only | A | B | C |
| --- | ---: | ---: | ---: |
| corr(filled Lot Frontage, log SalePrice) | **0.891** | 0.219 | 0.219 |

- **Which variant is correct, and which leak?**
  - **C** is the only honest estimate. The imputer learns its means, SDs and neighbor pool on
    the 4 training folds and only looks them up on the held-out fold.
  - **B** leaks the *features* of the held-out fold into the fill.
  - **A** leaks the *target*: each filled value is a function of SalePrice. That is why the
    filled values correlate 0.89 with log price, against 0.35 for real frontage.
  - A does not score *better* here only because a linear model gives Lot Frontage one slope,
    set mostly by the 2,440 real values. A flexible model (trees) could read the leaked price
    signal off the filled rows.
- **Which can't price an unsold house?** **A.** Its fill needs the house's SalePrice
  quintile, and an unsold house has no SalePrice. The pipeline can't even run on it.
- **Size of B vs C: +0.000001 (0.0006%).** It is tiny for three reasons:
  - the KNN imputer never sees y, so B leaks only feature statistics;
  - each training fold already holds 80% of the rows, so the means, SDs and neighbor pool
    barely change when the other 20% is added;
  - Lot Frontage is a weak feature here: dropping it costs only 0.0003.

## 8 What this data cannot tell you

- **Why a value is missing.** MAR versus MNAR for Lot Frontage cannot be decided from this
  file. The assessor's recording rules, or the parcel maps (PID → city site), would.
- **Which year is right** in the Order 851 remodel conflict, what the 2207 garage year
  should be, and whether the 3 zero-kitchen and 3 $0-misc-value rows are errors.
  They were left as NaN or flagged.
- **Market value for unusual sales.** The dictionary flags 5 houses over 4,000 sq ft
  (3 partial sales that don't reflect market value). They were kept, not deleted, and they
  inflate RMSE.
- **Anything outside Ames 2006–2010**, including the housing crash it spans. One sale per
  parcel means there are no repeat-sale dynamics.
- **Causal effects.** These are assessor attributes at the time of sale, not interventions.
