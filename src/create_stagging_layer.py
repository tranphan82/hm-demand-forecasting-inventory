import duckdb
from pathlib import Path

RAW_DIR = Path("data/raw")

# Create persistent database
con = duckdb.connect("hm_retail.duckdb")

print("Creating stagging tables...")

# Articles:
con.execute(f"""
CREATE OR REPLACE TABLE stg_articles AS
SELECT *
FROM read_csv_auto('{(RAW_DIR / "articles.csv").as_posix()}') 
""")

# Customers:
con.execute(f"""
CREATE OR REPLACE TABLE stg_customers AS
SELECT *
            FROM read_csv_auto('{(RAW_DIR / "customers.csv").as_posix()}')            
""")

# Transactions:
con.execute(f"""
CREATE OR REPLACE TABLE stg_transactions AS
SELECT *
            FROM read_csv_auto('{(RAW_DIR / "transactions_train.csv").as_posix()}')            
""")

print("Done!")

# Quick validation
for table in [
    "stg_articles",
    "stg_customers",
    "stg_transactions"
]:
    result = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {result:,} rows")