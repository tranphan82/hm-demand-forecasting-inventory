import pandas as pd

from hm_forecasting.dashboard import sales_velocity, dead_stock, geospatial_demand


# For testing Sales Velocity
def test_sales_velocity_aggregates_by_week_and_group(dashboard_con):
    # dashboard_con is the fixture defined in conftest.py
    result = sales_velocity(dashboard_con)

    assert len(result) == 4

    week1 = result[result["week_start"] == pd.Timestamp("2024-01-01")]
    week2 = result[result["week_start"] == pd.Timestamp("2024-01-08")]

    assert week1.iloc[0]["product_group_name"] == "Menswear"
    assert week1.iloc[0]["units_sold"] == 23
    assert week1.iloc[1]["product_group_name"] == "Ladieswear"
    assert week1.iloc[1]["units_sold"] == 20

    assert week2.iloc[0]["product_group_name"] == "Ladieswear"
    assert week2.iloc[0]["units_sold"] == 50
    assert week2.iloc[1]["product_group_name"] == "Menswear"
    assert week2.iloc[1]["units_sold"] == 3


# For tesing Deadlock Inventory
def test_dead_stock_computes_days_since_last_sale(dashboard_con): 
    # dashboard_con is the fixture defined in conftest.py
    result = dead_stock(dashboard_con)

    assert list(result["article_id"]) == ["P2", "P1", "P3"]

    by_article = result.set_index("article_id")
    assert by_article.loc["P2", "days_since_last_sale"] == 8
    assert by_article.loc["P1", "days_since_last_sale"] == 1
    assert by_article.loc["P3", "days_since_last_sale"] == 0


# Testing for Geopastial Demand
def test_geospatial_demand_aggregates_by_postal_code(geospatial_con):
    result = geospatial_demand(geospatial_con)

    assert list(result["postal_code"]) == ["10001", "20002"]

    by_postal = result.set_index("postal_code")
    assert by_postal.loc["10001", "units_sold"] == 5
    assert by_postal.loc["10001", "unique_customers"] == 2
    assert by_postal.loc["20002", "units_sold"] == 1
    assert by_postal.loc["20002", "unique_customers"] == 1