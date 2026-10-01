import duckdb 
import pandas as pd

from hm_forecasting.features import (
    create_calendar_features,
    create_forecastable_products,
    create_product_date_spine,
    create_forecasting_base,
    create_lag_features,
    create_model_features
)



def test_forecastable_products_filters_by_sales_days(fact_daily_sales_con):
    create_forecastable_products(fact_daily_sales_con)

    result = fact_daily_sales_con.execute("""
        SELECT article_id
        FROM forecastable_products
        ORDER BY article_id    
    """).fetchall()

    assert result == [("A0001",)]

# Correctness test:
def test_lag_28_is_null_before_28_days_of_history(forecasting_base_con):
    create_lag_features(forecasting_base_con)

    lag_28_day_28 = forecasting_base_con.execute("""
        Select lag_28 From fs_lag_features Where sales_date = '2024-01-28'
""").fetchone()[0]

    lag_28_day_29 = forecasting_base_con.execute("""
        Select lag_28 From fs_lag_features Where sales_date = '2024-01-29'
""").fetchone()[0]

    assert lag_28_day_28 is None
    assert lag_28_day_29 == 1


def test_lag_and_rolling_values_are_correct(forecasting_base_con):
    create_lag_features(forecasting_base_con)

    result = forecasting_base_con.execute("""
        Select lag_1, lag_7, lag_14, rolling_avg_7, rolling_avg_28
        From fs_lag_features
        Where sales_date = '2024-01-29'
""").fetchone()  

    assert result == (28, 22, 15, 25.0, 14.5)


# Leakage test:
def _build_pipeline(day29_quantity):
    con = duckdb.connect(":memory:")

    quantities = list(range(1,36))
    quantities[28] = day29_quantity #index 28 = the 29th day

    fact_daily_sales = pd.DataFrame({
        "sales_date": pd.date_range("2024-01-01", periods=35, freq="D"),
        "article_id": "A0001",
        "total_quantity_sold": quantities,
        "total_sales_amount": [q*10.0 for q in quantities],
        "average_unit_price": 10.0,
        "unique_customers": 1
    })

    con.register("fact_daily_sales_df", fact_daily_sales)
    con.execute("Create Table fact_daily_sales As Select * From fact_daily_sales_df")

    create_calendar_features(con)
    create_forecastable_products(con)
    create_product_date_spine(con)
    create_forecasting_base(con)
    create_lag_features(con)

    return con

def test_rolling_averages_exclude_current_day():
    con_normal = _build_pipeline(day29_quantity=29)
    con_mutated = _build_pipeline(day29_quantity=99999)

    rolling_normal = con_normal.execute("""
        Select rolling_avg_7, rolling_avg_28
        From fs_lag_features Where sales_date = '2024-01-29'
""").fetchone()

    rolling_mutated = con_mutated.execute("""
        Select rolling_avg_7, rolling_avg_28
        From fs_lag_features Where sales_date = '2024-01-29'
""").fetchone()

    assert rolling_normal == rolling_mutated

    lag_1_normal = con_normal.execute("""
        Select lag_1 From fs_lag_features Where sales_date = '2024-01-30'
""").fetchone()[0]

    lag_1_mutated = con_mutated.execute("""
        Select lag_1 From fs_lag_features Where sales_date = '2024-01-30'
""").fetchone()[0]

    assert lag_1_mutated == 99999
    assert lag_1_normal != lag_1_mutated

    con_normal.close()
    con_mutated.close()

# Test fs_model_features: verifying the join actually lines up the right calendar row with the right lag row, not just that it runs without erroring

def test_model_features_joins_calendar_and_lag_data(forecasting_base_con):
    create_lag_features(forecasting_base_con)
    create_model_features(forecasting_base_con)

    result = forecasting_base_con.execute("""
        SELECT sales_month, day_of_week_num, is_weekend, lag_1, lag_14, rolling_avg_7
        FROM fs_model_features
        WHERE sales_date = '2024-01-29'
    """).fetchone()

    assert result == (1, 1, 0, 28, 15, 25.0)


# Last test: a grain/integrity check: no duplicate (article_id, sales_date) rows, 
# and no missing calendar days for the one product that made it through the filter.

def test_forecasting_base_has_no_duplicate_or_missing_dates(forecasting_base_con):
    total_rows = forecasting_base_con.execute("""
        SELECT COUNT(*) FROM forecasting_base
    """).fetchone()[0]

    distinct_rows = forecasting_base_con.execute("""
        SELECT COUNT(*) FROM (
            SELECT DISTINCT article_id, sales_date FROM forecasting_base
        )
    """).fetchone()[0]

    min_date, max_date = forecasting_base_con.execute("""
        SELECT MIN(sales_date), MAX(sales_date) FROM forecasting_base
    """).fetchone()

    assert total_rows == distinct_rows
    assert total_rows == (max_date - min_date).days + 1