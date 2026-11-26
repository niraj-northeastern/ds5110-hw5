# Part 1: download the raw file once and never overwrite it.
import hashlib
import os
import sys
from urllib.request import urlretrieve

import pandas as pd

DATA_URL = "https://jse.amstat.org/v19n3/decock/AmesHousing.txt"

path = sys.argv[1]

if os.path.exists(path):
    print(path, "already exists, not downloading again.")
    sys.exit(0)

os.makedirs(os.path.dirname(path), exist_ok=True)
urlretrieve(DATA_URL, path)

df = pd.read_csv(path, sep="\t")
sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
print("Downloaded", path, "shape:", df.shape, "sha256:", sha)

# The data dictionary says 2930 observations and 82 variables
if df.shape != (2930, 82):
    sys.exit("Wrong shape, expected (2930, 82)")
