import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("Creating dim product...")

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

print("Creating dim customer...")

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

print("Dimension table created successfully")

for table in ["dim_product", "dim_customer"]:
    row_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {row_count:,} rows")
