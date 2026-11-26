# HW5: Ames Housing quality audit

## How to run

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make all
```

`make all` downloads the raw file (once), checks that validation **fails** on the raw file and
**passes** on the cleaned file, then writes every table to `reports/results/` and the
histograms to `reports/figures/`. `make clean` removes everything generated.

| Step | Script | Output |
| --- | --- | --- |
| Part 1 | `src/download.py` | `data/raw/AmesHousing.txt` (never overwritten) |
| Part 2 | `src/validate.py` | PASS/FAIL with every failure listed |
| Parts 3, 4 | `src/clean.py` | `data/processed/ames_clean.csv`, `na_audit`, `zero_counts`, `fixes`, `true_missing`, `keys` |
| Part 5 | `src/missingness.py` | `missingness_*`, `*_missing_by_*` |
| Part 6 | `src/impute.py` | `imputation_costs`, `figures/lot_frontage_*.png` |
| Part 7 | `src/evaluate.py` | `leakage_rmse`, `leakage_filled_rows` |
| shared | `src/common.py` | loader, `GroupMedianImputer`, `KNNFrontageImputer` |

## Provenance (Part 1)

| Item | Value |
| --- | --- |
| Source URL | https://jse.amstat.org/v19n3/decock/AmesHousing.txt (linked from the JSE article page) |
| Downloaded on | 2026-11-25 |
| SHA-256 of the file used | `6cfe6cb525ba437de428653a1040e2aed7d696640bf75203786a6d7a0e67cfcc` |
| Citation | De Cock, D. (2011). Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project. Journal of Statistics Education, 19(3). |
| Data dictionary | https://jse.amstat.org/v19n3/decock/DataDocumentation.txt |
| Terms of use | JSE data sets may be used freely in teaching without asking permission, with a citation to the data set and author; use in published work needs the author's consent (https://jse.amstat.org/jse_users.htm). |
| Rows, columns on arrival | 2,930 rows, 82 columns (tab-separated); matches the dictionary's "2930 observations, 82 variables" |

`download.py` stops if `data/raw/AmesHousing.txt` already exists, and exits with an error if
the downloaded file is not 2,930 × 82. It prints the SHA-256, so a re-download can be compared
with the value above.

Note: on the day of the audit, jse.amstat.org could not be reached from the build machine, so
the copy used was the mirror in `rasbt/machine-learning-book` (`ch09/AmesHousing.txt`), which
matches the dictionary (2,930 × 82, tab-separated). Byte-identity with the JSE copy could not be
checked from there; `DATA_URL` points at the original JSE source, and the SHA-256 printed by
`download.py` on a fresh download should be compared with the value above.

## Features used in Part 7

14 numeric columns in `NUMERIC_FEATURES`:

`Lot Frontage, Lot Area, Overall Qual, Overall Cond, Year Built, Gr Liv Area, 1st Flr SF,
Full Bath, Half Bath, Bedroom AbvGr, TotRms AbvGrd, Fireplaces, Wood Deck SF, Open Porch SF`

Why: they are the size, quality and age measures a buyer knows before a sale. Apart from
Lot Frontage (required), **none has a missing value**, so the only imputation in Part 7 is
the one being tested. Excluded on purpose: `Garage Yr Blt` (157 structural NaN for houses
with no garage), `Total Bsmt SF` and `Garage Cars` (1 unknown each), `Year Remod/Add`
(1 unknown after cleaning), `Mas Vnr Area` (26 unknown), `PID`/`Order` (identifiers),
`MS SubClass` (nominal code stored as a number), and anything recorded at or after the
sale (`Mo Sold`, `Yr Sold`, `Misc Val`).

`Lot Config` is passed to the Part 7 imputer as a distance key only and dropped before the
model sees the data.

## AI assistance

Claude (Anthropic) was used in a supporting role, as a coding assistant: helping draft and
simplify the scripts in `src/` (validation rules, cleaning, missingness tests, the two
custom imputers, the leakage evaluation), and the results tables and factual summaries in
`reports/report.md`. The arguments in Sections 5 to 8 of the report are my own. I reviewed
the code file by file and can explain every line.
