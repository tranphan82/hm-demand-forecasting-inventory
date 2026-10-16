import duckdb
import pandas as pd

from hm_forecasting.modeling import (
    backtest_windows,
    build_train_test,
    mean_absolute_error,
    predict,
    root_mean_squared_error,
    score_by_segment,
    train_lightgbm,
)
from hm_forecasting.segmentation import label_segments, product_segments

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb", read_only=True)
    rows = []
    segment_tables = []

    for start, end in backtest_windows(con):
        print(f"Window {start} -> {end}")
        train, test = build_train_test(con, start, end_date=end)
        model = train_lightgbm(train)

        actual = test["quantity_sold"]
        forecasts = {
            "zero": pd.Series(0.0, index=actual.index),
            "naive": test["lag_7"],
            "ma7": test["rolling_avg_7"],
            "ma28": test["rolling_avg_28"],
            "lgbm": predict(model, test),
        }

        row = {"window_start": start, "train_rows": len(train), "test_rows": len(test)}
        for name, forecast in forecasts.items():
            row[f"{name}_mae"] = mean_absolute_error(actual, forecast)
            row[f"{name}_rmse"] = root_mean_squared_error(actual, forecast)
        rows.append(row)

        segments = label_segments(product_segments(con, start))
        by_segment = score_by_segment(test, forecasts, segments, "segment")
        by_segment.insert(0, "window_start", start)
        segment_tables.append(by_segment)

    results = pd.DataFrame(rows)
    best_ma_mae = results[["ma7_mae", "ma28_mae"]].min(axis=1)
    best_ma_rmse = results[["ma7_rmse", "ma28_rmse"]].min(axis=1)
    results["mae_gain_vs_best_ma"] = 1 - results["lgbm_mae"] / best_ma_mae
    results["rmse_gain_vs_best_ma"] = 1 - results["lgbm_rmse"] / best_ma_rmse

    pd.set_option("display.width", 250)
    print("\nOverall: LightGBM gain vs the better moving average")
    print(results[["window_start", "mae_gain_vs_best_ma", "rmse_gain_vs_best_ma"]]
          .round(4).to_string(index=False))

    by_segment = pd.concat(segment_tables, ignore_index=True)
    by_segment["mae_gain_vs_ma7"] = 1 - by_segment["lgbm_mae"] / by_segment["ma7_mae"]
    by_segment["rmse_gain_vs_ma7"] = 1 - by_segment["lgbm_rmse"] / by_segment["ma7_rmse"]

    for column in ["rmse_gain_vs_ma7", "mae_gain_vs_ma7"]:
        print(f"\nBy segment: {column} (positive = LightGBM better)")
        print(by_segment.pivot(index="segment", columns="window_start", values=column)
              .round(3).to_string())

    print("\nTest rows per segment:")
    print(by_segment.pivot(index="segment", columns="window_start", values="rows").to_string())

    con.close()

