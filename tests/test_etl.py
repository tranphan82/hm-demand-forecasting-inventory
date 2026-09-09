from hm_forecasting.validation import row_count
from hm_forecasting.etl import create_dimensions, create_fact_daily_sales

def test_staging_creates_expected_row_counts(staged_con):
    assert row_count(staged_con, "stg_articles") == 3
    assert row_count(staged_con, "stg_customers") == 3
    assert row_count(staged_con, "stg_transactions") == 7


def test_dimensions_replaces_missing_detail_desc(staged_con):
    create_dimensions(staged_con)

    result = staged_con.execute("""
        SELECT product_description
        FROM dim_product
        WHERE article_id = '0000000003'
    """).fetchone()[0]

    assert result == "Unknown"

def test_dimension_buckers_missing_age_as_unknown(staged_con):
    create_dimensions(staged_con)

    result = staged_con.execute("""
        SELECT age_group
        FROM dim_customer
        WHERE customer_id = 'c2'
    """).fetchone()[0]

    assert result == "Unknown"


def test_fact_daily_sales_aggregates_correctly(staged_con):
    create_fact_daily_sales(staged_con)

    result = staged_con.execute("""
        SELECT 
            total_quantity_sold,
            total_sales_amount,
            average_unit_price,
            unique_customers
        FROM fact_daily_sales
        WHERE article_id = '0000000001' AND sales_date = '2024-01-01'
        """).fetchone()

    assert result == (3, 30.0, 10.0, 2)
