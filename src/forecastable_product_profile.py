import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print(
    con.execute("""
    SELECT
        CASE
            WHEN sales_days < 30 THEN '<30'
            WHEN sales_days < 90 THEN '30-89'
            WHEN sales_days < 180 THEN '90-179'
            WHEN sales_days < 365 THEN '180-365'
            ELSE '365+'
        END AS bucket,
        COUNT(*) AS products
    FROM (
        SELECT
            article_id,
            COUNT(*) AS sales_days
        FROM fact_daily_sales
        GROUP BY article_id            
    )
    GROUP BY bucket
    ORDER BY bucket
    """).fetchdf()
)