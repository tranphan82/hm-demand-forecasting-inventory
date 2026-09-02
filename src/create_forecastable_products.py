import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("Creating forecastable_products...")

con.execute("""
CREATE OR REPLACE TABLE forecastable_products AS
    SELECT 
        article_id,
        COUNT(*) AS sales_days,
        SUM(total_quantity_sold) AS total_units_sold
    FROM fact_daily_sales
    GROUP BY article_id
    HAVING COUNT(*) >=30
""")

print("Done.")

print(
    con.execute("""
    SELECT
        COUNT(*) AS products
    FROM forecastable_products
""").fetchdf()
)

print("\nSample:")

print(
    con.execute("""
    SELECT *
        FROM forecastable_products
        ORDER BY total_units_sold DESC
        LIMIT 10
""").fetchdf()
)