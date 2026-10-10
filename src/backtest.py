import duckdb
import pandas as pd

from hm_forecasting.modeling import (
    backtest_windows,
    build_train_test,
    mean_absolute_error,
    predict,
    root_mean_squared_error,
    train_lightgbm,
)

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb", read_only=True)
    rows = []

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

    results = pd.DataFrame(rows)
    best_ma_mae = results[["ma7_mae", "ma28_mae"]].min(axis=1)
    best_ma_rmse = results[["ma7_rmse", "ma28_rmse"]].min(axis=1)
    results["mae_gain_vs_best_ma"] = 1 - results["lgbm_mae"] / best_ma_mae
    results["rmse_gain_vs_best_ma"] = 1 - results["lgbm_rmse"] / best_ma_rmse

    pd.set_option("display.width", 250)
    print("\nMAE")
    print(results[["window_start", "zero_mae", "naive_mae", "ma7_mae", "ma28_mae", "lgbm_mae"]]
          .round(4).to_string(index=False))
    print("\nRMSE")
    print(results[["window_start", "zero_rmse", "naive_rmse", "ma7_rmse", "ma28_rmse", "lgbm_rmse"]]
          .round(4).to_string(index=False))
    print("\nLightGBM gain vs the better moving average")
    print(results[["window_start", "mae_gain_vs_best_ma", "rmse_gain_vs_best_ma"]]
          .round(4).to_string(index=False))

    con.close()
    