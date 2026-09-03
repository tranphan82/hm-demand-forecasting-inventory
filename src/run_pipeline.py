import duckdb
from hm_forecasting import run_all
from hm_forecasting.etl import export_to_parquet

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb")

    print("Running pipeline...")
    run_all(con)
    print("Done.")

    print("Exporting to parquet...")
    export_to_parquet(con, ["dim_product", "dim_customer", "fact_daily_sales"])
    print("Done.")

    con.close()
