import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("Creating fs_calendar_features...")

con.execute("""
CREATE OR REPLACE TABLE fs_calendar_features AS
        SELECT
            sales_date,
            EXTRACT(year from sales_date) AS sales_year,
            EXTRACT(month from sales_date) AS sales_month,
            EXTRACT(quarter from sales_date) AS sales_quarter,
            EXTRACT(week from sales_date) AS sales_week,
            EXTRACT(day from sales_date) AS day_of_month,
            EXTRACT(dayofweek from sales_date) AS day_of_week_num,

            CASE
                WHEN EXTRACT(dayofweek FROM sales_date) in (0,6) THEN 1
                ELSE 0
            END AS is_weekend,

            CASE
                WHEN EXTRACT(day FROM sales_date) = 1 THEN 1
                ELSE 0
            END AS is_month_start,

            CASE
                WHEN sales_date = LAST_DAY(sales_date) THEN 1
                ELSE 0
            END AS is_month_end
        FROM (
            SELECT DISTINCT sales_date
            FROM fact_daily_sales
            )
        ORDER BY sales_date
""")

print("fs_calendar_features created successfully")

print(con.execute("""
SELECT *
FROM fs_calendar_features
LIMIT 10
""").fetchdf())

row_count = con.execute("""
SELECT COUNT(*)
FROM fs_calendar_features
""").fetchone()[0]

print(f"Rows: {row_count:,}")