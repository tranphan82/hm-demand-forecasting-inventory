import pandas as pd
from datetime import date

from hm_forecasting.deepar import (select_intermittent_articles, build_series)

AS_OF = date(2024, 4, 10)
RULES = {"min_sales_days": 5, "min_active_days": 60, "min_recent_sales": 0}


def test_select_intermittent_articles_applies_all_rules(intermittent_con):
    selected = select_intermittent_articles(intermittent_con, AS_OF, sample_n=10, **RULES)

    assert sorted(selected) == ["A_SPARSE", "F_SPARSE2", "H_BECOMES_DENSE"]


def test_select_intermittent_articles_sample_is_exact_and_repeatable(intermittent_con):
    first = select_intermittent_articles(intermittent_con, AS_OF, sample_n=2, **RULES)
    second = select_intermittent_articles(intermittent_con, AS_OF, sample_n=2, **RULES)

    assert len(first) == 2
    assert first == second

# Test the build_series in deepar.py(turn product into time series)
def test_build_series_zero_fills_missing_days(intermittent_con):
    series = build_series(intermittent_con, ["A_SPARSE", "E_SHORT_HISTORY"], date(2024, 1, 11))
    by_id = {s["item_id"]: s for s in series}

    assert list(by_id) == ["A_SPARSE"]
    assert by_id["A_SPARSE"]["start"] == pd.Timestamp("2024-01-01")
    assert by_id["A_SPARSE"]["target"].tolist() == [1, 0, 0, 0, 0, 0, 0, 0, 1, 0]


def test_build_series_starts_at_each_products_first_sale(intermittent_con):
    series = build_series(intermittent_con, ["E_SHORT_HISTORY"], date(2024, 3, 10))

    assert series[0]["start"] == pd.Timestamp("2024-03-01")
    assert series[0]["target"].tolist() == [1, 0, 0, 0, 0, 1, 0, 0, 0]


def test_select_intermittent_articles_requires_recent_sales(intermittent_con):
    selected = select_intermittent_articles(
        intermittent_con, AS_OF, sample_n=10,
        min_sales_days=5, min_active_days=60, recent_days=56, min_recent_sales=1,
    )

    assert sorted(selected) == ["A_SPARSE", "F_SPARSE2"]

def test_build_series_returns_one_series_per_product(intermittent_con):
    series = build_series(intermittent_con, ["A_SPARSE", "F_SPARSE2"], date(2024, 1, 11))

    assert [s["item_id"] for s in series] == ["A_SPARSE", "F_SPARSE2"]
    assert series[1]["target"].tolist() == [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]