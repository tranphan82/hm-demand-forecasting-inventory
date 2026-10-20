import numpy as np

from hm_forecasting.baselines import tsb_rate, rolling_window_totals, empirical_quantile_total


def test_tsb_rate_decays_when_sales_stop():
    target = np.array([4, 0, 0, 0], dtype="float32")

    assert tsb_rate(target, alpha=0.5, beta=0.5) == 0.5


def test_tsb_rate_updates_size_on_a_sale():
    target = np.array([4, 2], dtype="float32")

    assert tsb_rate(target, alpha=0.5, beta=0.5) == 3.0

def test_rolling_window_totals_sums_each_overlapping_window():
    target = np.array([1, 0, 0, 2, 0, 0], dtype="float32")

    assert rolling_window_totals(target, window=3).tolist() == [1.0, 2.0, 2.0, 2.0]


def test_empirical_quantile_total_picks_a_quantile_of_window_totals():
    target = np.array([1, 0, 0, 2, 0, 0], dtype="float32")

    assert empirical_quantile_total(target, window=3, q=0.0) == 1.0
    assert empirical_quantile_total(target, window=3, q=0.5) == 2.0
    