import duckdb
 
con = duckdb.connect("hm_retail.duckdb")

print("Creating lag features...")

con.execute("""
    CREATE OR REPLACE TABLE fs_lag_features AS
        SELECT
            sales_date,
            article_id,
            quantity_sold,

            LAG(quantity_sold, 1) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_1,
            LAG(quantity_sold, 7) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_7,
            LAG(quantity_sold, 28) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_28,

            AVG(quantity_sold) OVER (
            PARTITION BY article_id 
            ORDER BY sales_date 
            ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS rolling_avg_7,

            AVG(quantity_sold) OVER (
            PARTITION BY article_id 
            ORDER BY sales_date 
            ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS rolling_avg_28,


        FROM forecasting_base""")

print("Done!")

print("\nRow count:")

print(
    con.execute("""
        SELECT COUNT(*)
        FROM fs_lag_features
        """).fetchdf()
)

print("\nSample:")

print(
    con.execute("""
        SELECT *
        from fs_lag_features
        WHERE article_id = '0108775015'
        ORDER BY sales_date
        LIMIT 15
        """).fetchdf()
)

con.close()