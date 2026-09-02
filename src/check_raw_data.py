import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")

files = [
    "articles.csv",
    "customers.csv",
    "transactions_train.csv"
]

for file in files:
    print("="*80)
    print(f"FILE: {file}")

    df = pd.read_csv(
        RAW_DIR / file, nrows = 5
    )

    print("\nColumns: ")
    print(df.columns.tolist())

    print("\nSample: ")
    print(df.head())

    print("\nShape: ")
    print(df.shape)

    print("\n")