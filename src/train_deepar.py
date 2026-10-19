from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd

from hm_forecasting.deepar import build_series, select_articles_by_segment
from hm_forecasting.deepar_model import forecast_totals, train_deepar
from hm_forecasting.modeling import pinball_loss, root_mean_squared_error
from hm_forecasting.segmentation import label_segments, product_segments

ORIGIN = date(2020, 8, 25)
HORIZON = 28
SEGMENTS = ["active/intermittent", "active/lumpy"]

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb", read_only=True)

    segments = label_segments(product_segments(con, ORIGIN))
    article_ids = select_articles_by_segment(con, ORIGIN, SEGMENTS)
    print(f"Selected {len(article_ids):,} products")

    train_series = build_series(con, article_ids, ORIGIN)
    actual_series = build_series(con, article_ids, ORIGIN + timedelta(days=HORIZON))
    con.close()

    print("Training DeepAR...")
    predictor = train_deepar(
        train_series, prediction_length=HORIZON, max_epochs=10, num_batches_per_epoch=100
    )
    totals_by_id = forecast_totals(predictor, train_series)

    ids = [s["item_id"] for s in train_series]
    actual_by_id = {s["item_id"]: s["target"] for s in actual_series}

    totals = np.stack([totals_by_id[i] for i in ids])
    results = pd.DataFrame({
        "article_id": ids,
        "actual": [actual_by_id[i][-HORIZON:].sum() for i in ids],
        "recent_rate": [s["target"][-HORIZON:].mean() * HORIZON for s in train_series],
        "deepar_mean": totals.mean(axis=1),
        "p90": np.percentile(totals, 90, axis=1),
    })
    results = results.merge(segments[["article_id", "segment"]], on="article_id", how="left")

    def summarise(group):
        actual = group["actual"]
        return pd.Series({
            "products": len(group),
            "mean_actual": actual.mean(),
            "rmse_zero": root_mean_squared_error(actual, 0.0),
            "rmse_recent": root_mean_squared_error(actual, group["recent_rate"]),
            "rmse_deepar": root_mean_squared_error(actual, group["deepar_mean"]),
            "pinball_zero": pinball_loss(actual, 0.0, 0.9),
            "pinball_deepar": pinball_loss(actual, group["p90"], 0.9),
            "p90_coverage": (actual <= group["p90"]).mean(),
        })

    pd.set_option("display.width", 250)
    print("\nBy segment:")
    print(results.groupby("segment").apply(summarise, include_groups=False).round(4).to_string())
    print("\nAll selected products:")
    print(summarise(results).round(4).to_string())

    # Add this to check the assumptions: is that for lumpy prodicts we plan from the quantiles, not the mean
    # It shows the ten products with the largest errors: their actual 28-day demand, what the recent rate would have predicted, DeepAR’s median, mean and P90.
    results["p50"] = np.percentile(totals, 50, axis=1)
    results["error"] = (results["deepar_mean"] - results["actual"]).abs()
    print("\nWorst 10 mean forecasts:")
    print(
        results.nlargest(10, "error")[
            ["article_id", "segment", "actual", "recent_rate", "p50", "deepar_mean", "p90"]
        ].round(1).to_string(index=False)
    )

    def max_window_total(target, window=HORIZON):
        cumulative = np.concatenate([[0.0], np.cumsum(target)])
        if len(target) < window:
            return cumulative[-1]
        return (cumulative[window:] - cumulative[:-window]).max()

    results["hist_max"] = [max_window_total(s["target"]) for s in train_series]
    runaway = results["p50"] > 3 * results["hist_max"]
    print(f"\nRunaway forecasts (P50 above 3x best-ever 28-day total): {runaway.mean():.2%} of products")

    capped = results.assign(
        deepar_mean=np.minimum(results["deepar_mean"], 3 * results["hist_max"]),
        p90=np.minimum(results["p90"], 3 * results["hist_max"]),
    )
    print("\nWith forecasts capped at 3x best-ever 28-day total:")
    print(capped.groupby("segment").apply(summarise, include_groups=False).round(4).to_string())


    