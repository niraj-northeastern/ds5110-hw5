# Part 7: variants A, B, C with the same model and the same folds.
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_val_predict, cross_val_score
from sklearn.pipeline import Pipeline

from common import KNNFrontageImputer, load_clean, save_table

NUMERIC_FEATURES = [
    "Lot Frontage", "Lot Area", "Overall Qual", "Overall Cond", "Year Built",
    "Gr Liv Area", "1st Flr SF", "Full Bath", "Half Bath", "Bedroom AbvGr",
    "TotRms AbvGrd", "Fireplaces", "Wood Deck SF", "Open Porch SF",
]
cv = KFold(n_splits=5, shuffle=True, random_state=5110)

df = load_clean(sys.argv[1])
y = np.log(df["SalePrice"])
missing = df["Lot Frontage"].isna()

# Lot Config is needed by the KNN imputer to measure distance; the imputer drops it after
X_with_key = df[NUMERIC_FEATURES + ["Lot Config"]]

# A: fill with the median Lot Frontage of the house's SalePrice quintile (uses the answer y!)
quintile = pd.qcut(df["SalePrice"], 5, labels=False)
X_A = df[NUMERIC_FEATURES].copy()
X_A["Lot Frontage"] = X_A["Lot Frontage"].fillna(
    X_A.groupby(quintile)["Lot Frontage"].transform("median"))

# B: fit the KNN imputer on all 2,930 rows first, then cross-validate
X_B = KNNFrontageImputer().fit_transform(X_with_key)

# C: put the imputer inside a Pipeline, so it is refit on the training folds each time
pipe_C = Pipeline([("impute", KNNFrontageImputer()), ("model", LinearRegression())])

variants = {
    "A (SalePrice-quintile median, full table)": (LinearRegression(), X_A),
    "B (KNN fit on full table, then CV)": (LinearRegression(), X_B),
    "C (KNN inside Pipeline)": (pipe_C, X_with_key),
    "reference: Lot Frontage dropped": (LinearRegression(), df[NUMERIC_FEATURES[1:]]),
}

rmse = {}
for name, (model, X) in variants.items():
    scores = -cross_val_score(model, X, y, cv=cv, scoring="neg_root_mean_squared_error")
    rmse[name] = {"CV RMSE (log $)": scores.mean(), "fold sd": scores.std()}
save_table(pd.DataFrame(rmse).T.round(5), "leakage_rmse")

a, b, c = [rmse[name]["CV RMSE (log $)"] for name in list(variants)[:3]]
print(f"\nA - C = {a - c:+.5f}    B - C = {b - c:+.6f}")

# Where does A's leak show up? Look only at the 490 houses that got a filled value.
filled_values = {"A": X_A["Lot Frontage"],
                 "B": X_B["Lot Frontage"],
                 "C": X_B["Lot Frontage"]}   # same fill rule as B, just fit per fold in CV
leak = {}
for letter, name in zip("ABC", list(variants)[:3]):
    model, X = variants[name]
    pred = cross_val_predict(model, X, y, cv=cv)
    leak[letter] = {
        "corr(filled Lot Frontage, log SalePrice)": filled_values[letter][missing].corr(y[missing]),
        "RMSE on the 490 filled rows": np.sqrt(((pred - y)[missing] ** 2).mean()),
        "RMSE on the 2,440 observed rows": np.sqrt(((pred - y)[~missing] ** 2).mean()),
    }
save_table(pd.DataFrame(leak).round(4), "leakage_filled_rows")
