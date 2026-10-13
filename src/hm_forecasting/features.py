from pathlib import Path

def create_calendar_features(con):
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



def create_forecastable_products(con):
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

def create_product_date_spine(con):
    con.execute("""
        CREATE OR REPLACE TABLE product_date_spine AS
        SELECT 
            c.sales_date,
            p.article_id
        FROM fs_calendar_features c
        CROSS JOIN forecastable_products p
    """)

def create_forecasting_base(con):
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

def create_lag_features(con):
    con.execute("""
        CREATE OR REPLACE TABLE fs_lag_features AS
        SELECT
            sales_date,
            article_id,
            quantity_sold,

            LAG(quantity_sold, 1) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_1,
            LAG(quantity_sold, 7) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_7,
            LAG(quantity_sold, 14) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_14,
            LAG(quantity_sold, 28) OVER (PARTITION BY article_id ORDER BY sales_date) AS lag_28,

            AVG(quantity_sold) OVER (
                PARTITION BY article_id 
                ORDER BY sales_date 
                ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING) AS rolling_avg_7,

            AVG(quantity_sold) OVER (
                PARTITION BY article_id 
                ORDER BY sales_date 
                ROWS BETWEEN 14 PRECEDING AND 1 PRECEDING) AS rolling_avg_14,    

            AVG(quantity_sold) OVER (
                PARTITION BY article_id 
                ORDER BY sales_date 
                ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING) AS rolling_avg_28

        FROM forecasting_base
    """)


def create_model_features(con):
    con.execute("""
        CREATE OR REPLACE TABLE fs_model_features AS
        SELECT
            p.sales_date,
            p.article_id,
            p.quantity_sold,

            c.sales_year,
            c.sales_month,
            c.sales_quarter,
            c.sales_week,
            c.day_of_month,
            c.day_of_week_num,
            c.is_weekend,
            c.is_month_start,
            c.is_month_end,

            d.product_group_name,
            d.garment_group_name,
            d.index_name,
            d.section_name,
            d.color_group_name,

            p.lag_1,
            p.lag_7,
            p.lag_14,
            p.lag_28,
            p.rolling_avg_7,
            p.rolling_avg_28,

            pr.last_price,
            pr.price_ratio_28,

        FROM fs_lag_features p
        JOIN fs_calendar_features c
            ON p.sales_date = c.sales_date
        JOIn dim_product d
            On p.article_id = d.article_id
        JOIN fs_price_features pr
            ON p.sales_date = pr.sales_date
            AND p.article_id = pr.article_id

    """)

# Create this function for testing the price_feature:
def create_price_features(con):
    con.execute("""
        CREATE OR REPLACE TABLE fs_price_features AS
        SELECT
            sales_date,
            article_id,
            last_price,
            last_price / avg_price_28 AS price_ratio_28
        FROM (
            SELECT
                sales_date,
                article_id,
                LAST_VALUE(NULLIF(average_unit_price, 0) IGNORE NULLS) OVER (
                    PARTITION BY article_id ORDER BY sales_date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                ) AS last_price,
                AVG(NULLIF(average_unit_price, 0)) OVER (
                    PARTITION BY article_id ORDER BY sales_date
                    ROWS BETWEEN 28 PRECEDING AND 1 PRECEDING
                ) AS avg_price_28
            FROM forecasting_base
        )
    """)