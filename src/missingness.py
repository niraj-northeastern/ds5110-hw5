# Part 5: is the missingness random?
# Split houses into "value missing" and "value present" and compare them on columns we
# do see. If missing were completely random (MCAR), the two groups would look alike.
import sys

import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu

from common import load_clean, save_table

NUMERIC = ["SalePrice", "Lot Area", "Gr Liv Area", "Year Built"]
CATEGORICAL = ["Lot Config", "Neighborhood", "Bldg Type"]


def compare_groups(df, col):
    missing = df[col].isna()
    rows = []

    for obs in NUMERIC:
        a = df.loc[missing, obs]
        b = df.loc[~missing, obs]
        rows.append({"compared on": obs,
                     "missing group": f"median {a.median():,.0f}",
                     "present group": f"median {b.median():,.0f}",
                     "test": "Mann-Whitney U",
                     "p-value": f"{mannwhitneyu(a, b).pvalue:.1e}"})

    for obs in CATEGORICAL:
        share = missing.groupby(df[obs]).mean()       # share missing in each category
        size = df[obs].value_counts()
        share = share[size[share.index] >= 20]        # skip tiny categories
        p = chi2_contingency(pd.crosstab(df[obs], missing))[1]
        rows.append({"compared on": obs,
                     "missing group": f"{share.min():.0%} ({share.idxmin()}) to {share.max():.0%} ({share.idxmax()})",
                     "present group": f"overall {missing.mean():.1%} missing",
                     "test": "chi-square",
                     "p-value": f"{p:.1e}"})
    return pd.DataFrame(rows)


def missing_by(df, col, group):
    table = df.groupby(group)[col].agg(houses="size", missing=lambda s: s.isna().sum())
    table["share missing"] = (table["missing"] / table["houses"]).round(3)
    return table.sort_values("share missing", ascending=False)


if __name__ == "__main__":
    df = load_clean(sys.argv[1])

    for col in ["Lot Frontage", "Mas Vnr Area"]:
        print(f"\n## {col}: {df[col].isna().sum()} missing out of {len(df)}")
        save_table(compare_groups(df, col), "missingness_" + col.replace(" ", "_"), index=False)

    save_table(missing_by(df, "Lot Frontage", "Lot Config"), "lot_frontage_missing_by_lot_config")
    save_table(missing_by(df, "Mas Vnr Area", "Sale Condition"), "mas_vnr_missing_by_sale_condition")
    save_table(missing_by(df, "Mas Vnr Area", "Yr Sold"), "mas_vnr_missing_by_yr_sold")
