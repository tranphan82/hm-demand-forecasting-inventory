import duckdb
from pathlib import Path

RAW_DIR = Path("data/raw")

con = duckdb.connect()

files = {
    "articles": RAW_DIR/"articles.csv",
    "customers": RAW_DIR/"customers.csv",
    "transactions": RAW_DIR/"transactions_train.csv",
}

print("="*80)
print("H&M RAW DATA PROFILLING WITH DUCKDB")
print("="*80)

for name, path in files.items():
    print(f"\n{name.upper()} FILE")
    print("="*80)

    sample_query = f"""
        SELECT *
        FROM read_csv_auto('{path.as_posix()}')
        LIMIT 5
    """

    sample = con.execute(sample_query).fetchdf()
    print(sample)

    count_query = f"""
        SELECT COUNT(*) AS row_count
        FROM read_csv_auto('{path.as_posix()}')
    """

    row_count = con.execute(count_query).fetchone()[0]
    print(f"\nRow_count: {row_count:,}")