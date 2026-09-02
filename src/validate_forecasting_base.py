import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("="*70)
print("FORECASTING BASE VALIDATION")
print("="*70)

print("\nRows with zero sales:")

print(con.execute("""
SELECT
    COUNT(*) AS zero_sales_rows
    FROM forecasting_base
    WHERE quantity_sold = 0
""").fetchdf()
)

print("\nPercentage of zero-sales rows:")

print(
    con.execute("""
SELECT
    ROUND(100.0*SUM(CASE WHEN quantity_sold = 0 THEN 1 ELSE 0 END)/COUNT(*), 2) AS pct_zero_sales
    FROM forecasting_base
""").fetchdf()
)

print("\nExample product with zero-sales days:")

print(
    con.execute("""
SELECT *
    FROM forecasting_base
    WHERE article_id IN (
        SELECT article_id
        FROM forecasting_base
        GROUP BY article_id
        HAVING SUM(CASE WHEN quantity_sold = 0 THEN 1 ELSE 0 END) > 100
        LIMIT 1
    )
    ORDER BY sales_date
    LIMIT 30
""").fetchdf()
)

con.close()