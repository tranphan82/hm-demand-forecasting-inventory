import numpy as np

from hm_forecasting.baselines import tsb_rate


def test_tsb_rate_decays_when_sales_stop():
    target = np.array([4, 0, 0, 0], dtype="float32")

    assert tsb_rate(target, alpha=0.5, beta=0.5) == 0.5


def test_tsb_rate_updates_size_on_a_sale():
    target = np.array([4, 2], dtype="float32")

    assert tsb_rate(target, alpha=0.5, beta=0.5) == 3.0

