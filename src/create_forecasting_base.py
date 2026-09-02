import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("Creating forecasting_base")

con.execute("""
CREATE OR REPLACE TABLE forecasting_base AS
    SELECT
        s.sales_date,
        s.article_id,
        COALESCE(f.total_quantity_sold, 0) AS quantity_sold,
        COALESCE(f.total_sales_amount, 0) AS sales_amount,
        COALESCE(f.average_unit_price, 0) AS average_unit_price,
        COALESCE(f.unique_customers, 0) AS unique_customers
    
    FROM product_date_spine s
    LEFT JOIN fact_daily_sales f
    ON s.sales_date = f.sales_date
    AND s.article_id = f.article_id
""")

print("Done!")

print(con.execute("""
    SELECT COUNT(*)
    FROM forecasting_base
    """).fetchdf()
)

print("\nSample:")

print(con.execute("""
    SELECT *
    FROM forecasting_base
    ORDER BY article_id, sales_date
    LIMIT 20
""").fetchdf()
)

con.close()