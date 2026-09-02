import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print(
    con.execute("""
        SELECT
            COUNT(DISTINCT article_id) AS products,
            AVG(sales_days) AS avg_sales_days
        FROM (
            SELECT
                article_id,
                COUNT(*) AS sales_days
            FROM fact_daily_sales
            GROUP BY article_id
            )
""").fetchdf()
)

print("n\Top distribution:")

print(
    con.execute("""
        SELECT
            sales_days,
            COUNT(*) AS products
        FROM (
            SELECT 
                article_id,
                COUNT(*) AS sales_days
            FROM fact_daily_sales
            GROUP By article_id            
        )
        GROUP BY sales_days
        ORDER BY sales_days DESC
        LIMIT 20
        """).fetchdf()
)

print("n\Bottom distribution:")

print(
    con.execute("""
        SELECT
            sales_days,
            COUNT(*) AS products
        FROM (
            SELECT 
                article_id,
                COUNT(*) AS sales_days
            FROM fact_daily_sales
            GROUP By article_id            
        )
        GROUP BY sales_days
        ORDER BY sales_days ASC
        LIMIT 20
        """).fetchdf()
)