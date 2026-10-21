import numpy as np

from hm_forecasting.policy import (
    normal_stock, 
    period_cost, 
    quantile_stock, 
    evaluate_policies)

from hm_forecasting.inventory import assumptions_for_class



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


# Test for Sensitivity table
def test_evaluate_policies_caps_deepar_and_picks_method_by_segment():
    costs = {c: assumptions_for_class(c) for c in "AB"}
    products = [
        {
            "article_id": "P1", "segment": "active/lumpy", "volume_class": "A",
            "windows": np.array([10.0, 10.0, 10.0]),
            "samples": np.array([10.0] * 5), "actual": 10.0,
        },
        {
            "article_id": "P2", "segment": "active/smooth", "volume_class": "B",
            "windows": np.array([10.0, 10.0]),
            "samples": np.array([100.0] * 5), "actual": 4.0,
        },
    ]

    results = evaluate_policies(products, costs, horizon=91).set_index("article_id")

    assert results.loc["P1", "segment_choice_cost"] == 0.0
    assert results.loc["P2", "deepar_quantile_stock"] == 30.0
    assert results.loc["P2", "segment_choice_stock"] == 10.0
    assert abs(
        results.loc["P2", "segment_choice_cost"] - 6 * costs["B"].excess_cost_per_period
    ) < 1e-12