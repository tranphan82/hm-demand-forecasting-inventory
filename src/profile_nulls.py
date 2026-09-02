import duckdb 

con = duckdb.connect("hm_retail.duckdb")

print("="*80)
print("ARTICLE NULL CHECK")
print("="*80)

print(
    con.execute("""
    SELECT 
        COUNT(*) as total_rows,
        SUM(CASE WHEN detail_desc IS NULL THEN 1 ELSE 0 END) AS missing_desc,
        SUM(CASE WHEN prod_name IS NULL THEN 1 ELSE 0 END) AS missing_name
    FROM stg_articles
    """).fetchdf()
)

print("\n")

print("="*80)
print("CUSTOMER NULL CHECK")
print("="*80)

print(
    con.execute("""
    SELECT
        COUNT(*) as total_rows,
        SUM(CASE WHEN age IS NULL THEN 1 ELSE 0 END) AS missing_age,
        SUM(CASE WHEN cluB_member_status IS NULL THEN 1 ELSE 0 END) AS missing_status,
        SUM(CASE WHEN fashion_news_frequency IS NULL THEN 1 ELSE 0 END) AS missing_news
    FROM stg_customers
    """).fetchdf()
)
