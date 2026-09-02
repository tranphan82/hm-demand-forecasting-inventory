import duckdb
from pathlib import Path

con = duckdb.connect("hm_retail.duckdb")

output_dir = Path("data/processed")
output_dir.mkdir(exist_ok=True)

tables = [
    "dim_product",
    "dim_customer",
    "fact_daily_sales"
]

for table in tables:
    output_file = output_dir / f"{table}.parquet"

    print(f"Exporting {table}...")

    con.execute(f"""
    COPY(
        SELECT *
        FROM {table}
        )   
    TO '{output_file.as_posix()}'
    (FORMAT PARQUET) 
""")
    
    print(f"Saved: {output_file}")

print("\nDone.")