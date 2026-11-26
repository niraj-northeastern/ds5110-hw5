# Parts 3 and 4: fix the problems validate.py found, keep "none" as a category,
# turn only truly unknown values into NaN, and check the keys.
import sys

import numpy as np
import pandas as pd

from common import save_table
from validate import NEIGHBORHOODS, NUMERIC_COLS

# Columns where the dictionary says "NA" means "doesn't have one", not "unknown"
NA_MEANS_NONE = [
    "Alley",                                                       # No alley access
    "Bsmt Qual", "Bsmt Cond", "Bsmt Exposure", "BsmtFin Type 1", "BsmtFin Type 2",  # No Basement
    "Fireplace Qu",                                                # No Fireplace
    "Garage Type", "Garage Finish", "Garage Qual", "Garage Cond",  # No Garage
    "Pool QC",                                                     # No Pool
    "Fence",                                                       # No Fence
    "Misc Feature",                                                # None
]
# (Mas Vnr Type also has "None" = no masonry veneer. Kept as a category too.)

# Codes in the file that don't match the dictionary -> the dictionary's code.
# validate.py reports these on the raw file; here they are fixed on purpose and logged.
CODE_FIXES = {
    "MS Zoning": {"C (all)": "C", "I (all)": "I", "A (agr)": "A"},
    "Neighborhood": {"NAmes": "Names"},
    "Bldg Type": {"2fmCon": "2FmCon", "Duplex": "Duplx", "Twnhs": "TwnhsI"},
    "Exterior 2nd": {"CmentBd": "CemntBd", "Wd Shng": "WdShing", "Brk Cmn": "BrkComm"},
}

fixes = []   # one row per fix, saved to reports/results/fixes.md


def log_fix(problem, mask, df, action):
    orders = df.loc[mask, "Order"].tolist()
    fixes.append({"problem": problem, "rows": len(orders),
                  "Order (first 8)": str(orders[:8]), "action": action})


def load_raw(path):
    # keep_default_na=False so "NA" and "None" stay as text; empty cells become NaN
    return pd.read_csv(path, sep="\t", keep_default_na=False, na_values=[""], dtype={"PID": str})


def na_audit(path):
    # Part 3: load the file twice and compare
    default = pd.read_csv(path, sep="\t")     # pandas default: "NA" and "None" become NaN
    kept = load_raw(path)                      # our way: they stay as text

    rows = []
    for col in kept.columns:
        n_na = (kept[col] == "NA").sum()
        n_none = (kept[col] == "None").sum()
        n_empty = kept[col].isna().sum()
        if n_na + n_none + n_empty == 0:
            continue
        if col in NA_MEANS_NONE:
            meaning = "NA = none"
        elif n_none > 0:
            meaning = "None = no veneer"
        else:
            meaning = "empty = unknown"
        rows.append({"column": col, '"NA"': n_na, '"None"': n_none, "empty": n_empty,
                     "NaN with default load": default[col].isna().sum(), "meaning": meaning})
    save_table(pd.DataFrame(rows), "na_audit", index=False)

    # How many zeros each numeric column has (argued one by one in the report)
    zeros = [{"column": c, "zeros": (kept[c] == 0).sum()} for c in NUMERIC_COLS if (kept[c] == 0).any()]
    save_table(pd.DataFrame(zeros), "zero_counts", index=False)


def decode_missing(df):
    df = df.copy()

    # 1. "WD " has a trailing space in Sale Type
    bad = df["Sale Type"] != df["Sale Type"].str.strip()
    log_fix("Sale Type 'WD ' has a trailing space", bad, df, "strip spaces")
    df["Sale Type"] = df["Sale Type"].str.strip()

    # 2. Codes that are not in the dictionary
    for col, mapping in CODE_FIXES.items():
        for old, new in mapping.items():
            bad = df[col] == old
            log_fix(f"{col}: '{old}' not in dictionary", bad, df, f"change to '{new}'")
            df.loc[bad, col] = new

    # 3. Garage built in 2207. Probably 2007, but that is a guess, so mark it unknown.
    bad = df["Garage Yr Blt"] > 2010
    log_fix("Garage Yr Blt is 2207", bad, df, "set to NaN")
    df.loc[bad, "Garage Yr Blt"] = np.nan

    # 4. Remodeled before it was built. One year is wrong and we can't tell which.
    bad = df["Year Remod/Add"] < df["Year Built"]
    log_fix("Year Remod/Add before Year Built", bad, df, "set Year Remod/Add to NaN")
    df.loc[bad, "Year Remod/Add"] = np.nan

    # 5. Masonry veneer type and area disagree
    bad = (df["Mas Vnr Type"] == "None") & (df["Mas Vnr Area"] > 0)
    log_fix("Mas Vnr Type 'None' but area > 0", bad, df, "set type to NaN")
    df.loc[bad, "Mas Vnr Type"] = np.nan

    bad = df["Mas Vnr Type"].isin(["BrkCmn", "BrkFace", "CBlock", "Stone"]) & (df["Mas Vnr Area"] == 0)
    log_fix("Mas Vnr Type given but area is 0", bad, df, "set area to NaN")
    df.loc[bad, "Mas Vnr Area"] = np.nan

    # 6. Order 1357 has a 360 sq ft detached garage but Garage Qual/Cond say "NA" (no garage).
    #    Here "NA" can't mean "none", so it is unknown.
    has_garage = df["Garage Type"].notna() & (df["Garage Type"] != "NA")
    for col in ["Garage Qual", "Garage Cond"]:
        bad = has_garage & (df[col] == "NA")
        log_fix(f"{col} says no garage but there is one", bad, df, "set to NaN")
        df.loc[bad, col] = np.nan

    # 7. No basement, but the basement bath counts are empty -> no basement means 0 baths
    for col in ["Bsmt Full Bath", "Bsmt Half Bath"]:
        bad = (df["Bsmt Qual"] == "NA") & df[col].isna()
        log_fix(f"{col} empty for a house with no basement", bad, df, "set to 0")
        df.loc[bad, col] = 0

    save_table(pd.DataFrame(fixes), "fixes", index=False)

    missing = df.isna().sum()
    missing = missing[missing > 0].rename("true missing after cleaning").to_frame()
    save_table(missing, "true_missing")
    return df


def check_keys(df):
    # Part 4
    results = pd.DataFrame({
        "check": ["Order is unique", "PID is unique", "exact duplicate rows",
                  "duplicate rows ignoring Order", "duplicate PID",
                  "PIDs starting with 0 (lost if read as a number)"],
        "result": [df["Order"].is_unique,
                   df["PID"].is_unique,
                   df.duplicated().sum(),
                   df.drop(columns="Order").duplicated().sum(),
                   df["PID"].duplicated().sum(),
                   df["PID"].str.startswith("0").sum()],
    })
    save_table(results, "keys", index=False)
    assert df["Order"].is_unique and df["PID"].is_unique

    # Lookup join: neighborhood code -> full name. Must not add or lose rows.
    lookup = pd.DataFrame(list(NEIGHBORHOODS.items()), columns=["Neighborhood", "Neighborhood Name"])
    joined = df.merge(lookup, on="Neighborhood", how="left", validate="many_to_one")
    unmatched = joined["Neighborhood Name"].isna().sum()
    print(f"\nlookup join: {len(df)} rows before, {len(joined)} after, {unmatched} unmatched")
    assert len(joined) == len(df) and unmatched == 0


if __name__ == "__main__":
    raw_path = sys.argv[1]
    out_path = sys.argv[2]
    na_audit(raw_path)
    df = decode_missing(load_raw(raw_path))
    check_keys(df)
    df.to_csv(out_path, index=False)
    print("wrote", out_path, df.shape)
