from pathlib import Path

from . import etl, features

def run_all(con, raw_dir="data/raw"):
    etl.create_staging_tables(con, raw_dir)
    etl.create_dimensions(con)
    etl.create_fact_daily_sales(con)

    features.create_calendar_features(con)
    features.create_forecastable_products(con)
    features.create_product_date_spine(con)
    features.create_forecastbale_base(con)
    features.create_lag_features(con)

