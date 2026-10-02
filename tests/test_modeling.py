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

    