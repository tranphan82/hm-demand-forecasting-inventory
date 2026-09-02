from pathlib import Path

def row_count(con, table):
    return con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

def null_rate(con, table, column):
    return con.execute(f"""
        SELECT ROUND(100.0* SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END)/COUNT(*), 4)
        FROM {table}
    """).fetchone()[0]

def zero_sales_pct(con):
    return con.execute("""
        SELECT ROUND(100.00* SUM(CASE WHEN quantity_sold = 0 THEN 1 ELSE 0 END) / COUNT(*), 2)
        FROM forecasting_base
    """).fetchone()[0]

def fact_date_range(con):
    return con.execute("""
        SELECR MIN(sales_date) AS min_date, MAX(sales_date) AS max_date
        FROM fact_daily_sales
    """).fetchone()