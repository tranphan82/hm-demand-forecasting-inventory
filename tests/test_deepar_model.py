import numpy as np
import pandas as pd
import pytest

pytest.importorskip("gluonts")

from hm_forecasting.deepar_model import forecast_samples, train_deepar


def test_deepar_trains_and_returns_non_negative_sample_paths():
    rng = np.random.default_rng(0)
    series = [
        {
            "item_id": f"S{i}",
            "start": pd.Timestamp("2024-01-01"),
            "target": rng.poisson(0.3, size=120).astype("float32"),
        }
        for i in range(6)
    ]

    predictor = train_deepar(
        series,
        prediction_length=7,
        context_length=14,
        max_epochs=1,
        num_batches_per_epoch=5,
        num_parallel_samples=20,
    )
    samples = forecast_samples(predictor, series)

    assert set(samples) == {f"S{i}" for i in range(6)}
    assert samples["S0"].shape == (20, 7)
    assert (samples["S0"] >= 0).all()