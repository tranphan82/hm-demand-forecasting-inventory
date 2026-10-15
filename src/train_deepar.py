from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd

from hm_forecasting.deepar import build_series, select_intermittent_articles
from hm_forecasting.deepar_model import forecast_samples, train_deepar

ORIGIN = date(2020, 8, 25)
HORIZON = 28
SAMPLE_N = 3000

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb", read_only=True)

    article_ids = select_intermittent_articles(con, ORIGIN, sample_n=SAMPLE_N)
    print(f"Selected {len(article_ids):,} intermittent products")

    train_series = build_series(con, article_ids, ORIGIN)
    actual_series = build_series(con, article_ids, ORIGIN + timedelta(days=HORIZON))
    con.close()

    print("Training DeepAR...")
    predictor = train_deepar(train_series, prediction_length=HORIZON)
    samples = forecast_samples(predictor, train_series)

    ids = [s["item_id"] for s in train_series]
    actual_by_id = {s["item_id"]: s["target"] for s in actual_series}

    actual = np.array([actual_by_id[i][-HORIZON:].sum() for i in ids])
    totals = np.stack([samples[i].sum(axis=1) for i in ids])
    p10, p50, p90 = np.percentile(totals, [10, 50, 90], axis=1)

    history_rate = np.array([s["target"].mean() * HORIZON for s in train_series])
    recent_rate = np.array([s["target"][-HORIZON:].mean() * HORIZON for s in train_series])

    print(f"\nMean 28-day demand per product (actual): {actual.mean():.3f}")
    print("\nMAE of 28-day total demand:")
    print(f"  Predict zero            {np.abs(actual).mean():.4f}")
    print(f"  Historical average rate {np.abs(actual - history_rate).mean():.4f}")
    print(f"  Last-28-day rate        {np.abs(actual - recent_rate).mean():.4f}")
    print(f"  DeepAR (mean)           {np.abs(actual - totals.mean(axis=1)).mean():.4f}")

    print("\nQuantile calibration (share of products where actual <= quantile):")
    print(f"  P50 {np.mean(actual <= p50):.3f}   (target about 0.50 or higher)")
    print(f"  P90 {np.mean(actual <= p90):.3f}   (target about 0.90 or higher)")
    print(f"  Inside P10-P90 band {np.mean((actual >= p10) & (actual <= p90)):.3f}")

    print("\nSample of products:")
    print(pd.DataFrame({
        "article_id": ids, "actual": actual, "p10": p10, "p50": p50, "p90": p90,
    }).head(10).round(2).to_string(index=False))

    # Adding new lines to confirm the dormancy theory and add metrics that suit a probabilistic model
    recently_active = np.array([s["target"][-56:].sum() > 0 for s in train_series])
    print(f"\nProducts with a sale in the 56 days before the origin: {recently_active.mean():.3f}")
    print(f"Products with any sale in the 28-day test window:      {np.mean(actual > 0):.3f}")

    def pinball(actual, forecast, tau):
        diff = actual - forecast
        return np.mean(np.maximum(tau * diff, (tau - 1) * diff))

    print("\nRMSE of 28-day total demand:")
    for name, forecast in [
        ("Predict zero", np.zeros_like(actual)),
        ("Last-28-day rate", recent_rate),
        ("DeepAR (mean)", totals.mean(axis=1)),
    ]:
        print(f"  {name:<24}{np.sqrt(np.mean((actual - forecast) ** 2)):.4f}")

    print("\nP90 pinball loss (lower is better):")
    print(f"  Predict zero            {pinball(actual, np.zeros_like(actual), 0.9):.4f}")
    print(f"  DeepAR P90              {pinball(actual, p90, 0.9):.4f}")
    