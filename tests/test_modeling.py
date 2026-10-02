import pandas as pd

from hm_forecasting.modeling import get_split_date, baseline_predictions, mean_absolute_error


# Test for baseline model
def test_get_split_date_holds_out_last_n_days(modeling_con):
    split_date = get_split_date(modeling_con, test_days=2)

    assert str(split_date) == "2024-01-08"


def test_baseline_predictions_use_lag_7_on_test_period_only(modeling_con):
    split_date = get_split_date(modeling_con, test_days=2)
    result = baseline_predictions(modeling_con, split_date)

    assert list(result["actual"]) == [12, 13, 17]
    assert list(result["predicted"]) == [5, 6, 7]
    assert mean_absolute_error(result["actual"], result["predicted"]) == 8.0


def test_mean_absolute_error():
    actual = pd.Series([10, 20, 30])
    predicted = pd.Series([12, 18, 25])

    assert mean_absolute_error(actual, predicted) == 3.0


# This test is for testing LightGBM
from hm_forecasting.modeling import (
    FEATURE_COLUMNS,
    baseline_predictions,
    build_train_test,
    get_split_date,
    mean_absolute_error,
)


def test_build_train_test_splits_by_date(train_test_con):
    split_date = get_split_date(train_test_con, test_days=3)
    train, test = build_train_test(train_test_con, split_date, train_sample_pct=100)

    assert len(train) == 9
    assert len(test) == 4
    assert train["sales_date"].max() < test["sales_date"].min()
    assert str(train["sales_date"].min().date()) == "2024-01-08"


def test_build_train_test_returns_expected_columns(train_test_con):
    split_date = get_split_date(train_test_con, test_days=3)
    train, test = build_train_test(train_test_con, split_date, train_sample_pct=100)

    expected = ["sales_date", "article_id", "quantity_sold"] + FEATURE_COLUMNS
    assert list(train.columns) == expected
    assert list(test.columns) == expected


def test_build_train_test_sampling_applies_only_to_training(train_test_con):
    split_date = get_split_date(train_test_con, test_days=3)
    train, test = build_train_test(train_test_con, split_date, train_sample_pct=0)

    assert len(train) == 0
    assert len(test) == 4


def test_build_train_test_sample_is_repeatable(train_test_con):
    split_date = get_split_date(train_test_con, test_days=3)

    first, _ = build_train_test(train_test_con, split_date, train_sample_pct=50)
    second, _ = build_train_test(train_test_con, split_date, train_sample_pct=50)

    assert first.equals(second)