import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("Creating fact_daily_sales...")

con.execute("""
    CREATE OR REPLACE TABLE fact_daily_sales AS
    WITH transaction_items AS(
    SELECT 
        CAST(t_dat AS DATE) AS sales_date,
        article_id,
        customer_id,
        price,
        1 as quantity_sold
    FROM stg_transactions
    )
            
    SELECT
        sales_date,
        article_id,
                
        SUM(quantity_sold) AS total_quantity_sold,
        SUM(price*quantity_sold) AS total_sales_amount,
        SUM(price*quantity_sold)/SUM(quantity_sold) AS average_unit_price,
        COUNT(*) AS number_of_transactions,
        COUNT(DISTINCT customer_id) AS unique_customers,

        EXTRACT(year from sales_date) AS sales_year,
        EXTRACT(month from sales_date) AS sales_month,
        EXTRACT(day from sales_date) AS sales_day
            
    FROM transaction_items
    GROUP BY 
        sales_date,
        article_id         
""")

print("fact_daily_sales created sucessfully!")

row_count = con.execute("""
    SELECT COUNT(*)
    FROM fact_daily_sales
""").fetchone()[0]

print(f"fact_daily_sales: {row_count:,} rows")

print("\nSample:")
print(con.execute("""
    SELECT * 
    FROM fact_daily_sales
    LIMIT 10
""").fetchdf())