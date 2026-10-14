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

from hm_forecasting.dashboard import UNKNOWN_POSTAL_CODE # to fix unknown postal code

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

    dim_product = pd.DataFrame({
        "article_id": ["A0001", "B0002"],
        "product_group_name": ["Garment Upper body", "Swimwear"],
        "garment_group_name": ["Jersey Basic", "Swimwear"],
        "index_name": ["Ladieswear", "Ladieswear"],
        "section_name": ["Womens Everyday Basics", "Womens Swimwear"],
        "color_group_name": ["Black", "Blue"], 
    })
    fact_daily_sales_con.register("dim_product_df", dim_product)
    fact_daily_sales_con.execute("CREATE TABLE dim_product AS SELECT * FROM dim_product_df")
        
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


# Add new fixture for Geopastial Demand testing hm_forecasting\dashboard.py
@pytest.fixture
def geospatial_con(con):
    # add one more row to each DataFrame inside geospatial_con:
    stg_transactions = pd.DataFrame({
        "t_dat": ["2024-01-01", "2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", 
                  "2024-01-03", "2024-01-04"], # add "2024-01-04" to fix unknown postal code
        "customer_id": ["c1", "c1", "c1", "c2", "c2", "c3", "c4"], # add "c4" 
        "article_id": ["P1", "P1", "P1", "P1", "P1", "P1", "P1"], # add one more "P1"
        "price": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0], # add 1 more 10.0
    })

    dim_customer = pd.DataFrame({
        "customer_id": ["c1", "c2", "c3", "c4"], # add "c4"
        "postal_code": ["10001", "10001", "20002", UNKNOWN_POSTAL_CODE]}) # add unknown_postal_code

    con.register("stg_transactions_df", stg_transactions)
    con.execute("CREATE TABLE stg_transactions AS SELECT * FROM stg_transactions_df")

    con.register("dim_customer_df", dim_customer)
    con.execute("CREATE TABLE dim_customer AS SELECT * FROM dim_customer_df")

    return con


# Fixture to test the baseline model in hm_forecasting\modeling.py
@pytest.fixture
def modeling_con(con):
    fs_model_features = pd.DataFrame({
        "sales_date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "article_id": "A0001",
        "quantity_sold": [5, 6, 7, 8, 9, 10, 11, 12, 13, 17],
        "lag_7": [None] * 7 + [5, 6, 7],
    })

    con.register("fs_model_features_df", fs_model_features)
    con.execute("""
        Create Table fs_model_features As
        Select Cast(sales_date As Date) As Sales_date, article_id, quantity_sold, lag_7
        From fs_model_features_df    
    """)

    return con


# Fixture to test the LightGBM model
@pytest.fixture
def train_test_con(con):
    n = 20
    quantity = list(range(1, n + 1))

    fs_model_features = pd.DataFrame({
        "sales_date": pd.date_range("2024-01-01", periods=n, freq="D"),
        "article_id": "A0001",
        "quantity_sold": quantity,
        "lag_1": [None] + quantity[:-1],
        "lag_7": [None] * 7 + quantity[:n - 7],
        "lag_14": [None] * 14 + quantity[:n - 14],
        "lag_28": [float("nan")] * n,
        "rolling_avg_7": 0.0,
        "rolling_avg_28": 0.0,
        "sales_month": 1,
        "sales_quarter": 1,
        "sales_week": 1,
        "day_of_week_num": 0,
        "is_weekend": 0,
        "is_month_start": 0,
        "is_month_end": 0,
        "last_price": 10.0,
        "price_ratio_28": 1.0,
         "product_group_name": ["Garment Upper body", "Swimwear"] * 10,
        "garment_group_name": "Jersey Basic",
        "index_name": "Ladieswear",
        "section_name": "Womens Everyday Basics",
        "color_group_name": "Black",

    })

    con.register("fs_model_features_df", fs_model_features)
    con.execute("""
        CREATE TABLE fs_model_features AS
        SELECT CAST(sales_date AS DATE) AS sales_date, * EXCLUDE (sales_date)
        FROM fs_model_features_df
    """)

    return con

# Test fixture for price_feature attribute
@pytest.fixture
def price_con(con):
    forecasting_base = pd.DataFrame({
        "sales_date": pd.date_range("2024-01-01", periods=7, freq="D"),
        "article_id": "A0001",
        "average_unit_price": [10.0, 10.0, 0.0, 8.0, 4.0, 0.0, 0.0],
    })

    con.register("forecasting_base_df", forecasting_base)
    con.execute("""
        CREATE TABLE forecasting_base AS
        SELECT CAST(sales_date AS DATE) AS sales_date, article_id, average_unit_price
        FROM forecasting_base_df
    """)

    return con


@pytest.fixture
def intermittent_con(con):
    def rows(article_id, offsets, start="2024-01-01"):
        dates = pd.Timestamp(start) + pd.to_timedelta(list(offsets), unit="D")
        return pd.DataFrame({
            "sales_date": dates,
            "article_id": article_id,
            "total_quantity_sold": 1,
        })

    fact_daily_sales = pd.concat([
        rows("A_SPARSE", range(0, 96, 8)),
        rows("F_SPARSE2", range(0, 96, 12)),
        rows("B_DENSE", range(0, 50)),
        rows("C_TOO_FEW", range(0, 80, 20)),
        rows("E_SHORT_HISTORY", range(0, 25, 5), start="2024-03-01"),
        rows("H_BECOMES_DENSE", range(0, 36, 6)),
        rows("H_BECOMES_DENSE", range(100, 140)),
    ], ignore_index=True)

    con.register("fact_daily_sales_df", fact_daily_sales)
    con.execute("""
        CREATE TABLE fact_daily_sales AS
        SELECT CAST(sales_date AS DATE) AS sales_date, article_id, total_quantity_sold
        FROM fact_daily_sales_df
    """)

    return con