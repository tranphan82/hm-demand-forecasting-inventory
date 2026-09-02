import duckdb 

con = duckdb.connect("hm_retail.duckdb")

tables = ["stg_articles", "stg_customers", "stg_transactions"]

for table in tables:
    print("="*80)
    print(f"DATA QUALITY CHECK: {table}")
    print("="*80)

    # row count:
    # this is SQL-IN_PYTHON
    row_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] # return a one row tuple with fetchone(), then 1st element with fetchone()[0]
    print(f"Row count: {row_count:,}") # to print "," like 100,234

    # columns and type:
    print("\nColumns and data types:")
    print(con.execute(f"DESCRIBE {table}").fetchdf()) # return a pandas DataFrame with .fetchdf()

    print(f"\nSample rows:")
    print(con.execute(f"SELECT * FROM {table} LIMIT 5").fetchdf())

    print("\n")