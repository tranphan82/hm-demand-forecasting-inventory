import duckdb

con = duckdb.connect("hm_retail.duckdb", read_only=True)

print(
    con.execute("""
        SELECT
            COUNT(*) AS intermittent_products,
            ROUND(AVG(sales_days), 1) AS avg_sales_days,
            ROUND(AVG(active_days), 1) AS avg_active_days
        FROM (
            SELECT
                f.article_id,
                COUNT(*) AS sales_days,
                DATE_DIFF('day', MIN(f.sales_date),
                          (SELECT MAX(sales_date) FROM fact_daily_sales)) + 1 AS active_days
            FROM fact_daily_sales f
            JOIN forecastable_products p ON f.article_id = p.article_id
            GROUP BY f.article_id
        )
        WHERE sales_days * 1.0 / active_days < 0.15
    """).fetchdf()
)

con.close()