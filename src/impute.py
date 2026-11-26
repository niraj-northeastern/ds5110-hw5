# Part 6: three ways to fill Lot Frontage, and what each one costs.
import sys

import matplotlib
matplotlib.use("Agg")   # save figures without opening a window
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES, GroupMedianImputer, KNNFrontageImputer, load_clean, save_table

df = load_clean(sys.argv[1])
before = df["Lot Frontage"]
missing = before.isna()

# Each strategy gives back the full Lot Frontage column with the gaps filled
filled = {
    "median": before.fillna(before.median()),
    "neighborhood median": GroupMedianImputer().fit_transform(
        df[["Lot Frontage", "Neighborhood"]])["Lot Frontage"],
    "KNN": KNNFrontageImputer().fit_transform(
        df[["Lot Frontage", "Lot Area", "Lot Config"]])["Lot Frontage"],
}

rows = {}
for name, after in filled.items():
    # Cost 1: spread (std). Cost 2: link to Lot Area (correlation).
    rows[name] = {
        "std before": before.std(),
        "std after": after.std(),
        "std change %": 100 * (after.std() / before.std() - 1),
        "corr with Lot Area before": before.corr(df["Lot Area"]),
        "corr with Lot Area after": after.corr(df["Lot Area"]),
        "distinct filled values": after[missing].nunique(),
    }

    # One histogram per strategy: real values in blue, filled values in red
    fig, ax = plt.subplots(figsize=(6, 3.6))
    bins = np.arange(0, 205, 5)
    ax.hist(before.dropna(), bins=bins, color="#377eb8", alpha=0.85, label="observed")
    ax.hist(after[missing], bins=bins, color="#e41a1c", alpha=0.85, label=f"filled ({missing.sum()})")
    ax.set_xlabel("Lot Frontage (ft), cut at 200")
    ax.set_ylabel("houses")
    ax.set_title(f"Lot Frontage after {name} fill")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{FIGURES}/lot_frontage_{name.replace(' ', '_')}.png", dpi=150)
    plt.close(fig)

save_table(pd.DataFrame(rows).T.round(3), "imputation_costs")
