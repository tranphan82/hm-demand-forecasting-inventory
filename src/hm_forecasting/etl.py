from pathlib import Path


def create_staging_tables(con, raw_dir="data/raw"):
    # body of create_stagging_layer.py, using raw_dir instead of hardcoded RAW_DIR
    raw_dir = Path(raw_dir)

    con.execute(f"""
        CREATE OR REPLACE TABLE stg_articles AS
        SELECT * FROM read_csv_auto('{(raw_dir/"articles.csv").as_posix()}')
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE stg_customers AS
        SELECT * FROM read_csv_auto('{(raw_dir/"customers.csv").as_posix()}')
    """)

    con.execute(f"""
        CREATE OR REPLACE TABLE stg_transactions AS
        SELECT * FROM read_csv_auto('{(raw_dir/"transactions_train.csv").as_posix()}')
    """)
    ...

def create_dimensions(con):
    # body of create_dimensions.py (dim_product, dim_customer)
    con.execute("""
        CREATE OR REPLACE TABLE dim_product AS
        SELECT
            article_id,
            product_code,
            COALESCE(prod_name, 'Unknown') AS product_name,
            COALESCE(product_type_name, 'Unknown') AS produc_type_name,
            COALESCE(product_group_name, 'Unknown') AS product_group_name,
            COALESCE(graphical_appearance_name, 'Unknown') AS graphical_appearance_name,
            COALESCE(colour_group_name, 'Unknown') AS color_group_name,
            COALESCE(perceived_colour_value_name, 'Unknown') AS perceived_colour_value_name,
            COALESCE(perceived_colour_master_name, 'Unknown') AS perceived_colour_master_name,
            COALESCE(department_name, 'Unknown') AS department_name,
            COALESCE(index_name, 'Unknown') AS index_name,
            COALESCE(index_group_name, 'Unknown') AS index_group_name,
            COALESCE(section_name, 'Unknown') AS section_name,
            COALESCE(garment_group_name, 'Unknown') AS garment_group_name,
            COALESCE(detail_desc, 'Unknown') AS product_description
        FROM stg_articles
    """)
    
    con.execute("""
        CREATE OR REPLACE TABLE dim_customer AS
        SELECT
            customer_id,
            CASE
                WHEN age BETWEEN 10 and 100 Then age
                ELSE NULL
            END AS age,
        
            CASE
                WHEN age IS NULL THEN 'Unknown'
                WHEN age < 18 THEN 'Under 18'
                WHEN age BETWEEN 18 AND 24 THEN '18-24'
                WHEN age BETWEEN 25 AND 34 THEN '25-34'
                WHEN age BETWEEN 35 AND 44 THEN '35-44'
                WHEN age BETWEEN 45 AND 54 THEN '45-54'
                WHEN age BETWEEN 55 AND 64 THEN '55-64'
                ELSE '65+'
            END AS age_group,
        
            COALESCE(club_member_status, 'Unknown') AS club_member_status,
            COALESCE(fashion_news_frequency, 'Unknown') AS fashion_news_frequency,
            postal_code

        FROM stg_customers
    """)

def create_fact_daily_sales(con):
    # body of create_fact_daily_sales.py
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


def export_to_parquet(con, tables, output_dir = "data/processed"):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok = True)

    for table in tables:
        output_file = output_dir / f"{table}.parquet"
        con.execute(f"""
            COPY (SELECT * FROM {table})
            TO '{output_file.as_posix()}'
            (FORMAT PARQUET)
        """) 