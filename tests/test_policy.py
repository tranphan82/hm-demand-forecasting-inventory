import numpy as np

from hm_forecasting.policy import normal_stock, period_cost, quantile_stock


def test_quantile_stock_takes_a_percentile_per_row():
    one = np.array([0, 10, 20, 30, 40])
    many = np.array([[0, 10, 20], [1, 2, 3]])

    assert quantile_stock(one, 0.5) == 20.0
    assert quantile_stock(many, 1.0).tolist() == [20.0, 3.0]


def test_normal_stock_adds_k_standard_deviations_and_floors_at_zero():
    assert normal_stock(100, 20, 1.0) == 120.0
    assert normal_stock(10, 20, -1.0) == 0.0


def test_period_cost_charges_shortage_and_excess_separately():
    cost = period_cost(np.array([10, 10]), np.array([7, 15]), 1.5, 0.1)

    assert np.allclose(cost, [4.5, 0.5])