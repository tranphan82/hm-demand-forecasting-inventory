import duckdb 
import pytest
import pandas as pd

from hm_forecasting.etl import create_staging_tables
from hm_forecasting.features import (
    create_calendar_features,
    create_forecastable_products,
    create_product_date_spine,
    create_forecasting_base
)

FIXTURES_DIR = "tests/fixtures/mini_raw"

@pytest.fixture
def con():
    connection = duckdb.connect(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def staged_con(con):
    create_staging_tables(con, raw_dir = FIXTURES_DIR )
    return con


@pytest.fixture
def fact_daily_sales_con(con):
    long_history = pd.DataFrame({
        "sales_date": pd.date_range("2024-01-01", periods=35, freq="D"),
        "article_id": "A0001",
        "total_quantity_sold": range(1, 36),
        "total_sales_amount": [q * 10.0 for q in range(1, 36)],
        "average_unit_price": 10.0,
        "unique_customers": 1,
    })

    short_history = pd.DataFrame({
        "sales_date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "article_id": "B0002",
        "total_quantity_sold": 5,
        "total_sales_amount": 50.0,
        "average_unit_price": 10.0,
        "unique_customers": 1,
    })

    fact_daily_sales = pd.concat([long_history, short_history], ignore_index=True)

    con.register("fact_daily_sales_df", fact_daily_sales)
    con.execute("CREATE TABLE fact_daily_sales AS SELECT * FROM fact_daily_sales_df")

    return con

@pytest.fixture
def forecasting_base_con(fact_daily_sales_con):
    create_calendar_features(fact_daily_sales_con)
    create_forecastable_products(fact_daily_sales_con)
    create_product_date_spine(fact_daily_sales_con)
    create_forecasting_base(fact_daily_sales_con)
    return fact_daily_sales_con


# This is for test the 'Sale_Velocity' built in dashboard.py 
# and will be runned by the code in test_dashboard.py
@pytest.fixture
def dashboard_con(con):
    dim_product = pd.DataFrame({
        'article_id': ['P1', 'P2', 'P3'],
        'product_group_name': ['Menswear', 'Menswear', 'Ladieswear'] 
    })

    fact_daily_sales = pd.DataFrame({
        'sales_date': pd.to_datetime([
            "2024-01-01", "2024-01-03", "2024-01-02",
            "2024-01-01", "2024-01-09", "2024-01-10",
        ]),
        'article_id': ['P1', 'P1', 'P2', 'P3', 'P1', 'P3'],
        'total_quantity_sold': [10, 5, 8, 20, 3, 50],
    })

    con.register('dim_product_df', dim_product)
    con.execute("CREATE TABLE dim_product AS SELECT * FROM dim_product_df")

    con.register('fact_daily_sales_df', fact_daily_sales)
    con.execute("CREATE TABLE fact_daily_sales AS SELECT * FROM fact_daily_sales_df")

    return con  


# Add new fixture for Geopastial Demand testing
@pytest.fixture
def geospatial_con(con):
    stg_transactions = pd.DataFrame({
        "t_dat": ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03"],
        "customer_id": ["c1", "c1", "c1", "c2", "c2", "c3"],
        "article_id": ["P1", "P1", "P1", "P1", "P1", "P1"],
        "price": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
    })

    dim_customer = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3"],
        "postal_code": ["10001", "10001", "20002"],
    })

    con.register("stg_transactions_df", stg_transactions)
    con.execute("CREATE TABLE stg_transactions AS SELECT * FROM stg_transactions_df")

    con.register("dim_customer_df", dim_customer)
    con.execute("CREATE TABLE dim_customer AS SELECT * FROM dim_customer_df")

    return con