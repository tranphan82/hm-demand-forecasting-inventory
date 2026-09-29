# Velocity Sales
def sales_velocity(con):
    return con.execute("""
SELECT 
    DATE_TRUNC('week', f.sales_date) AS week_start,
    p.product_group_name,
    SUM(f.total_quantity_sold) AS units_sold
FROM fact_daily_sales f
JOIN dim_product p  
    ON f.article_id = p.article_id
GROUP BY week_start, p.product_group_name
ORDER BY week_start, units_sold DESC
""").fetchdf()

# Inventory Turn Risk
def dead_stock(con):
    return con.execute("""
    WITH last_sale AS (
        Select article_id,
        MAx(sales_date) As last_sale_Date
        From fact_daily_sales
        Group By article_id
        ),

    as_of AS (
        Select Max(sales_date) AS as_of_date 
        From fact_daily_sales
        )

    Select
        l.article_id,
        p.product_group_name,
        l.last_sale_date,
        datediff('day', l.last_sale_date, a.as_of_date) AS days_since_last_sale
    From last_sale l
    Join dim_product p
        On l.article_id = p.article_id
    Cross Join as_of a
    Order By days_since_last_sale DESC
    """).fetchdf()

# For Geopastial Demand
def geospatial_demand(con):
    return con.execute("""
        SELECT
            c.postal_code,
            COUNT(*) AS units_sold,
            COUNT(DISTINCT t.customer_id) AS unique_customers
        FROM stg_transactions t
        JOIN dim_customer c ON t.customer_id = c.customer_id
        GROUP BY c.postal_code
        ORDER BY units_sold DESC
    """).fetchdf()

