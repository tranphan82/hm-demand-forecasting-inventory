import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("Creating product_date_spine...")

con.execute("""
CREATE OR REPLACE TABLE product_date_spine AS
    SELECT 
        c.sales_date,
        p.article_id
    FROM fs_calendar_features c
    CROSS JOIN forecastable_products p
""")

print("Done.")

print(
    con.execute("""
        SELECT COUNT(*) AS rows
        FROM product_date_spine
        """).fetchdf()
)

print("\nSample:")

print(con.execute("""
    SELECT *
    FROM product_date_spine
    ORDER BY article_id, sales_date
    LIMIT 10
""").fetchdf()
)