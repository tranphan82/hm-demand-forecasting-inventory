import math

from scipy.stats import norm

from hm_forecasting.inventory import (
    critical_ratio,
    event_cost,
    k_from_cis,
    k_from_csl,
    k_from_csoe,
    k_from_ifr,
    loss_function,
    CostAssumptions,
    assumptions_for_class,
)


def test_critical_ratio():
    assert abs(critical_ratio(0.4, 0.1) - 0.8) < 1e-12


def test_loss_function_at_zero_is_the_normal_density_peak():
    assert abs(loss_function(0.0) - 0.3989422804) < 1e-9


def test_k_from_csl():
    assert k_from_csl(0.5) == 0.0
    assert abs(k_from_csl(0.05) - 1.6448536) < 1e-6


def test_k_from_cis():
    assert abs(k_from_cis(q=10, ce=1, d=100, cs=2) - 1.6448536) < 1e-6


def test_k_from_ifr_solves_the_loss_equation():
    k = k_from_ifr(ifr=0.95, q=10, sigma=20)

    assert abs(loss_function(k) - (10 / 20) * (1 - 0.95)) < 1e-9


def test_k_from_csoe_satisfies_first_order_condition():
    k = k_from_csoe(b1=500, d=1000, ce=2, sigma=10, q=100)

    assert abs(norm.pdf(k) - (2 * 10 * 100) / (500 * 1000)) < 1e-9


def test_k_from_csoe_floors_at_k_min_when_stockouts_are_cheap():
    assert k_from_csoe(b1=1, d=1, ce=10, sigma=10, q=10, k_min=0.0) == 0.0


def test_event_cost():
    assert event_cost(cs=0.4, daily_demand=10, event_days=7, fixed_cost=5) == 33.0

def test_cost_assumptions_derive_costs_per_dollar_of_price():
    costs = CostAssumptions()

    assert abs(costs.unit_cost - 0.50) < 1e-12
    assert abs(costs.shortage_cost - 1.50) < 1e-12
    assert abs(costs.holding_cost_per_year - 0.175) < 1e-12
    assert abs(costs.excess_cost_per_period - (0.10 + 0.175 * 91 / 365)) < 1e-12
    assert abs(costs.service_level - 0.9126) < 1e-4


def test_cost_assumptions_without_goodwill_or_markdown():
    costs = CostAssumptions(goodwill_multiplier=0.0, clearance_markdown=0.0)

    assert costs.shortage_cost == 0.5
    assert abs(costs.excess_cost_per_period - 0.175 * 91 / 365) < 1e-12

def test_service_levels_by_volume_class_at_91_day_horizon():
    levels = {c: assumptions_for_class(c).service_level for c in "ABC"}

    assert abs(levels["A"] - 0.9126) < 1e-4
    assert abs(levels["B"] - 0.8744) < 1e-4
    assert abs(levels["C"] - 0.7768) < 1e-4
