# Things more than one script needs: the loader, a table saver, and two imputers.
import os

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.impute import KNNImputer

RESULTS = "reports/results"
FIGURES = "reports/figures"


def load_clean(path):
    # keep_default_na=False keeps "NA" and "None" as text (they mean "no garage" etc.).
    # Only empty cells become NaN. PID is read as text so the leading 0 is kept.
    return pd.read_csv(path, keep_default_na=False, na_values=[""], dtype={"PID": str})


def save_table(df, name, index=True):
    # Print a table and also save it as markdown in reports/results/
    os.makedirs(RESULTS, exist_ok=True)
    text = df.to_markdown(index=index)
    with open(f"{RESULTS}/{name}.md", "w") as f:
        f.write(text + "\n")
    print(f"\n### {name}\n{text}")


class GroupMedianImputer(BaseEstimator, TransformerMixin):
    # Fill a column with the median of its group (e.g. its neighborhood).
    # The medians are learned in fit() only, so inside a Pipeline the test fold is never used.

    def __init__(self, target="Lot Frontage", group="Neighborhood"):
        self.target = target
        self.group = group

    def fit(self, X, y=None):
        self.medians_ = X.groupby(self.group)[self.target].median()
        self.overall_ = X[self.target].median()   # backup for a group never seen in fit
        return self

    def transform(self, X):
        X = X.copy()
        fill = X[self.group].map(self.medians_).fillna(self.overall_)
        X[self.target] = X[self.target].fillna(fill)
        return X.drop(columns=[self.group])        # the group column was only a key


class KNNFrontageImputer(BaseEstimator, TransformerMixin):
    # Fill Lot Frontage using the 10 most similar lots, where "similar" means
    # similar log(Lot Area) and the same Lot Config. Everything is learned in fit().

    def __init__(self, n_neighbors=10):
        self.n_neighbors = n_neighbors

    def make_table(self, X):
        # Columns used to measure distance between lots
        table = pd.DataFrame({"Lot Frontage": X["Lot Frontage"],
                              "log_area": np.log(X["Lot Area"])})
        dummies = pd.get_dummies(X["Lot Config"], dtype=float)
        dummies = dummies.reindex(columns=self.configs_, fill_value=0.0)
        return pd.concat([table, dummies], axis=1)

    def fit(self, X, y=None):
        self.configs_ = sorted(X["Lot Config"].unique())
        table = self.make_table(X)
        self.mean_ = table.mean()
        self.std_ = table.std()
        self.knn_ = KNNImputer(n_neighbors=self.n_neighbors)
        self.knn_.fit((table - self.mean_) / self.std_)   # standardize so units don't matter
        return self

    def transform(self, X):
        X = X.copy()
        scaled = (self.make_table(X) - self.mean_) / self.std_
        filled = self.knn_.transform(scaled)[:, 0]          # column 0 is Lot Frontage
        X["Lot Frontage"] = filled * self.std_["Lot Frontage"] + self.mean_["Lot Frontage"]
        return X.drop(columns=["Lot Config"])
