import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("="*80)
print("FACT TABLE VALIDATION")
print("="*80)

print("\nDate Range")

print(con.execute("""
SELECT 
    MIN(sales_date) AS min_date, 
    MAX(sales_date) as max_date 
FROM fact_daily_sales
""").fetchdf()
)

print("\nTop Selling Products")

print(con.execute("""
SELECT 
    article_id,
    SUM(total_quantity_sold) AS qty
FROM fact_daily_sales
GROUP BY article_id
ORDER BY qty DESC
LIMIT 10
""").fetchdf()
)

print("\nDaily Sales Summary")

print(con.execute("""
SELECT 
    COUNT(DISTINCT sales_date) AS days,
    SUM(total_quantity_sold) AS total_units
FROM fact_daily_sales
""").fetchdf()
)


