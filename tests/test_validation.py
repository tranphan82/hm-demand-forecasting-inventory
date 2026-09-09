from hm_forecasting.etl import create_fact_daily_sales
from hm_forecasting.validation import null_rate, zero_sales_pct, fact_date_range


def test_null_rate_on_staging_tables(staged_con):
    assert null_rate(staged_con, "stg_articles", "detail_desc") == 33.3333
    assert null_rate(staged_con, "stg_customers", "age") == 33.3333


def test_fact_date_range(staged_con):
    create_fact_daily_sales(staged_con)

    min_date, max_date = fact_date_range(staged_con)

    assert str(min_date) == "2024-01-01"
    assert str(max_date) == "2024-01-03"


def test_zero_sales_pct(con):
    con.execute("""
        CREATE TABLE forecasting_base AS
        SELECT * FROM (VALUES
            ('2024-01-01'::DATE, 'A0001', 5),
            ('2024-01-02'::DATE, 'A0001', 0),
            ('2024-01-03'::DATE, 'A0001', 0),
            ('2024-01-04'::DATE, 'A0001', 10)
        ) AS t(sales_date, article_id, quantity_sold)
    """)

    assert zero_sales_pct(con) == 50.0