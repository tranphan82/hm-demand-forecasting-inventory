import duckdb
from hm_forecasting import run_all

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb")
    run_all(con)
    print("Done!")

    con.close()
