# Part 2: check the data against rules. Collect every failure, then raise once.
#
# Where the rules come from:
#   DICT  = the data dictionary (DataDocumentation.txt)
#   STUDY = the data covers sales in Ames from 2006 to 2010
#   PHYS  = physical limits (areas, counts and prices can't be negative)
import sys
import pandas as pd


class ValidationError(Exception):
    pass


# ---------- schema: which columns must be text and which must be numbers ----------
# Column names follow the file. Some differ from the dictionary
# (e.g. "Exterior 1" in the dictionary is "Exterior 1st" in the file).
TEXT_COLS = [
    "PID",  # DICT says leading zeros matter, so it is text
    "MS Zoning", "Street", "Alley", "Lot Shape", "Land Contour", "Utilities",
    "Lot Config", "Land Slope", "Neighborhood", "Condition 1", "Condition 2",
    "Bldg Type", "House Style", "Roof Style", "Roof Matl", "Exterior 1st",
    "Exterior 2nd", "Mas Vnr Type", "Exter Qual", "Exter Cond", "Foundation",
    "Bsmt Qual", "Bsmt Cond", "Bsmt Exposure", "BsmtFin Type 1", "BsmtFin Type 2",
    "Heating", "Heating QC", "Central Air", "Electrical", "Kitchen Qual",
    "Functional", "Fireplace Qu", "Garage Type", "Garage Finish", "Garage Qual",
    "Garage Cond", "Paved Drive", "Pool QC", "Fence", "Misc Feature",
    "Sale Type", "Sale Condition",
]
NUMERIC_COLS = [
    "Order", "MS SubClass", "Lot Frontage", "Lot Area", "Overall Qual",
    "Overall Cond", "Year Built", "Year Remod/Add", "Mas Vnr Area", "BsmtFin SF 1",
    "BsmtFin SF 2", "Bsmt Unf SF", "Total Bsmt SF", "1st Flr SF", "2nd Flr SF",
    "Low Qual Fin SF", "Gr Liv Area", "Bsmt Full Bath", "Bsmt Half Bath",
    "Full Bath", "Half Bath", "Bedroom AbvGr", "Kitchen AbvGr", "TotRms AbvGrd",
    "Fireplaces", "Garage Yr Blt", "Garage Cars", "Garage Area", "Wood Deck SF",
    "Open Porch SF", "Enclosed Porch", "3Ssn Porch", "Screen Porch", "Pool Area",
    "Misc Val", "Mo Sold", "Yr Sold", "SalePrice",
]

# ---------- ranges: (lowest allowed, highest allowed) ----------
BIG = float("inf")
RANGES = {
    "Yr Sold": (2006, 2010),         # STUDY
    "Mo Sold": (1, 12),              # months of the year
    "Year Built": (1864, 2010),      # Ames was founded in 1864; nothing built after the last sale
    "Year Remod/Add": (1864, 2010),  # same as Year Built
    "Garage Yr Blt": (1864, 2010),   # same as Year Built
    "Overall Qual": (1, 10),         # DICT: 1 to 10 scale
    "Overall Cond": (1, 10),         # DICT: 1 to 10 scale
    "Lot Frontage": (1, BIG),        # PHYS: if recorded, frontage is more than 0
    "Lot Area": (1, BIG),            # PHYS
    "Gr Liv Area": (1, BIG),         # PHYS
    "SalePrice": (1, BIG),           # PHYS
}
# PHYS: these areas and counts can be 0 but never negative
for col in ["Mas Vnr Area", "BsmtFin SF 1", "BsmtFin SF 2", "Bsmt Unf SF", "Total Bsmt SF",
            "1st Flr SF", "2nd Flr SF", "Low Qual Fin SF", "Bsmt Full Bath", "Bsmt Half Bath",
            "Full Bath", "Half Bath", "Bedroom AbvGr", "Kitchen AbvGr", "TotRms AbvGrd",
            "Fireplaces", "Garage Cars", "Garage Area", "Wood Deck SF", "Open Porch SF",
            "Enclosed Porch", "3Ssn Porch", "Screen Porch", "Pool Area", "Misc Val"]:
    RANGES[col] = (0, BIG)

# ---------- allowed values: every set is copied from the data dictionary ----------
QUAL = {"Ex", "Gd", "TA", "Fa", "Po"}
EXTERIOR = {"AsbShng", "AsphShn", "BrkComm", "BrkFace", "CBlock", "CemntBd", "HdBoard",
            "ImStucc", "MetalSd", "Other", "Plywood", "PreCast", "Stone", "Stucco",
            "VinylSd", "Wd Sdng", "WdShing"}
CONDITION = {"Artery", "Feedr", "Norm", "RRNn", "RRAn", "PosN", "PosA", "RRNe", "RRAe"}
BSMT_FIN = {"GLQ", "ALQ", "BLQ", "Rec", "LwQ", "Unf", "NA"}

# Neighborhood code -> full name (also used for the lookup join in clean.py)
NEIGHBORHOODS = {
    "Blmngtn": "Bloomington Heights", "Blueste": "Bluestem", "BrDale": "Briardale",
    "BrkSide": "Brookside", "ClearCr": "Clear Creek", "CollgCr": "College Creek",
    "Crawfor": "Crawford", "Edwards": "Edwards", "Gilbert": "Gilbert", "Greens": "Greens",
    "GrnHill": "Green Hills", "IDOTRR": "Iowa DOT and Rail Road", "Landmrk": "Landmark",
    "MeadowV": "Meadow Village", "Mitchel": "Mitchell", "Names": "North Ames",
    "NoRidge": "Northridge", "NPkVill": "Northpark Villa", "NridgHt": "Northridge Heights",
    "NWAmes": "Northwest Ames", "OldTown": "Old Town",
    "SWISU": "South & West of Iowa State University", "Sawyer": "Sawyer",
    "SawyerW": "Sawyer West", "Somerst": "Somerset", "StoneBr": "Stone Brook",
    "Timber": "Timberland", "Veenker": "Veenker",
}

ALLOWED = {
    "MS SubClass": {20, 30, 40, 45, 50, 60, 70, 75, 80, 85, 90, 120, 150, 160, 180, 190},
    "MS Zoning": {"A", "C", "FV", "I", "RH", "RL", "RP", "RM"},
    "Street": {"Grvl", "Pave"},
    "Alley": {"Grvl", "Pave", "NA"},
    "Lot Shape": {"Reg", "IR1", "IR2", "IR3"},
    "Land Contour": {"Lvl", "Bnk", "HLS", "Low"},
    "Utilities": {"AllPub", "NoSewr", "NoSeWa", "ELO"},
    "Lot Config": {"Inside", "Corner", "CulDSac", "FR2", "FR3"},
    "Land Slope": {"Gtl", "Mod", "Sev"},
    "Neighborhood": set(NEIGHBORHOODS),
    "Condition 1": CONDITION,
    "Condition 2": CONDITION,
    "Bldg Type": {"1Fam", "2FmCon", "Duplx", "TwnhsE", "TwnhsI"},
    "House Style": {"1Story", "1.5Fin", "1.5Unf", "2Story", "2.5Fin", "2.5Unf", "SFoyer", "SLvl"},
    "Roof Style": {"Flat", "Gable", "Gambrel", "Hip", "Mansard", "Shed"},
    "Roof Matl": {"ClyTile", "CompShg", "Membran", "Metal", "Roll", "Tar&Grv", "WdShake", "WdShngl"},
    "Exterior 1st": EXTERIOR,
    "Exterior 2nd": EXTERIOR,
    "Mas Vnr Type": {"BrkCmn", "BrkFace", "CBlock", "None", "Stone"},
    "Exter Qual": QUAL,
    "Exter Cond": QUAL,
    "Foundation": {"BrkTil", "CBlock", "PConc", "Slab", "Stone", "Wood"},
    "Bsmt Qual": QUAL | {"NA"},
    "Bsmt Cond": QUAL | {"NA"},
    "Bsmt Exposure": {"Gd", "Av", "Mn", "No", "NA"},
    "BsmtFin Type 1": BSMT_FIN,
    "BsmtFin Type 2": BSMT_FIN,
    "Heating": {"Floor", "GasA", "GasW", "Grav", "OthW", "Wall"},
    "Heating QC": QUAL,
    "Central Air": {"N", "Y"},
    "Electrical": {"SBrkr", "FuseA", "FuseF", "FuseP", "Mix"},
    "Kitchen Qual": QUAL,
    "Functional": {"Typ", "Min1", "Min2", "Mod", "Maj1", "Maj2", "Sev", "Sal"},
    "Fireplace Qu": QUAL | {"NA"},
    "Garage Type": {"2Types", "Attchd", "Basment", "BuiltIn", "CarPort", "Detchd", "NA"},
    "Garage Finish": {"Fin", "RFn", "Unf", "NA"},
    "Garage Qual": QUAL | {"NA"},
    "Garage Cond": QUAL | {"NA"},
    "Paved Drive": {"Y", "P", "N"},
    "Pool QC": {"Ex", "Gd", "TA", "Fa", "NA"},
    "Fence": {"GdPrv", "MnPrv", "GdWo", "MnWw", "NA"},
    "Misc Feature": {"Elev", "Gar2", "Othr", "Shed", "TenC", "NA"},
    "Sale Type": {"WD", "CWD", "VWD", "New", "COD", "Con", "ConLw", "ConLI", "ConLD", "Oth"},
    "Sale Condition": {"Normal", "Abnorml", "AdjLand", "Alloca", "Family", "Partial"},
}


def check_schema(df):
    errors = []
    expected = set(TEXT_COLS) | set(NUMERIC_COLS)
    if set(df.columns) != expected:
        errors.append(f"schema: missing {expected - set(df.columns)}, extra {set(df.columns) - expected}")
    for col in NUMERIC_COLS:
        if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"schema: {col} should be numeric but is {df[col].dtype}")
    for col in TEXT_COLS:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            errors.append(f"schema: {col} should be text but is {df[col].dtype}")
    return errors


def check_ranges(df):
    errors = []
    for col, (low, high) in RANGES.items():
        bad = (df[col] < low) | (df[col] > high)     # NaN compares False, so NaN is skipped
        if bad.any():
            errors.append(f"range: {col} outside [{low}, {high}] in {bad.sum()} rows: "
                          f"{df.loc[bad, col].unique()[:5]}")
    return errors


def check_allowed(df):
    errors = []
    for col, allowed in ALLOWED.items():
        bad = df[col].notna() & ~df[col].isin(allowed)
        if bad.any():
            errors.append(f"allowed: {col} has codes not in the dictionary: "
                          f"{df.loc[bad, col].value_counts().to_dict()}")
    return errors


def check_cross_column(df):
    # Each rule is a True/False Series: True means that row breaks the rule.
    # A comparison with NaN is False, so rows with a missing value are not judged.
    partial = df["Sale Condition"] == "Partial"   # DICT: house not finished when assessed

    rules = {
        # DICT: remodel date = construction date if never remodeled, so never earlier
        "Year Remod/Add >= Year Built": df["Year Remod/Add"] < df["Year Built"],
        # Nothing is built after the sale, except pre-construction (Partial) sales
        "Year Built <= Yr Sold unless Partial": (df["Year Built"] > df["Yr Sold"]) & ~partial,
        "Year Remod/Add <= Yr Sold unless Partial": (df["Year Remod/Add"] > df["Yr Sold"]) & ~partial,
        "Garage Yr Blt <= Yr Sold unless Partial": (df["Garage Yr Blt"] > df["Yr Sold"]) & ~partial,
        # DICT: the parts of an area add up to the total
        "Total Bsmt SF = BsmtFin SF 1 + BsmtFin SF 2 + Bsmt Unf SF":
            df["Total Bsmt SF"].notna()
            & (df["BsmtFin SF 1"] + df["BsmtFin SF 2"] + df["Bsmt Unf SF"] != df["Total Bsmt SF"]),
        "Gr Liv Area = 1st Flr SF + 2nd Flr SF + Low Qual Fin SF":
            df["1st Flr SF"] + df["2nd Flr SF"] + df["Low Qual Fin SF"] != df["Gr Liv Area"],
    }

    # DICT: "NA" (or "None") means the thing doesn't exist, so its size must be 0, and the other way round
    none_pairs = [("Pool QC", "NA", "Pool Area"),
                  ("Fireplace Qu", "NA", "Fireplaces"),
                  ("Garage Type", "NA", "Garage Area"),
                  ("Bsmt Qual", "NA", "Total Bsmt SF"),
                  ("Mas Vnr Type", "None", "Mas Vnr Area")]
    for code_col, code, size_col in none_pairs:
        both_known = df[code_col].notna() & df[size_col].notna()
        rules[f"{code_col} == {code} iff {size_col} == 0"] = both_known & (
            (df[code_col] == code) != (df[size_col] == 0))

    # DICT: every garage column says "NA = No Garage", so they must agree with Garage Type
    for col in ["Garage Finish", "Garage Qual", "Garage Cond"]:
        both_known = df[col].notna() & df["Garage Type"].notna()
        rules[f"{col} == NA iff Garage Type == NA"] = both_known & (
            (df[col] == "NA") != (df["Garage Type"] == "NA"))

    errors = []
    for name, bad in rules.items():
        if bad.any():
            errors.append(f"cross: {name} fails in {bad.sum()} rows, "
                          f"Order {df.loc[bad, 'Order'].tolist()[:10]}")
    return errors


def validate(df):
    errors = check_schema(df) + check_ranges(df) + check_allowed(df) + check_cross_column(df)
    if errors:
        raise ValidationError("\n".join(errors))
    return df


if __name__ == "__main__":
    path = sys.argv[1]
    is_raw = "--raw" in sys.argv
    separator = "\t" if is_raw else ","     # the raw file is tab-separated
    df = pd.read_csv(path, sep=separator, keep_default_na=False, na_values=[""],
                     dtype={"PID": str})
    try:
        validate(df)
        print("PASS", path)
    except ValidationError as e:
        print("FAIL", path)
        print(e)
        sys.exit(1)
