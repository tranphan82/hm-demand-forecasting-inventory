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
            "lgbm": predict(model, test),
        }

        row = {"window_start": start, "train_rows": len(train), "test_rows": len(test)}
        for name, forecast in forecasts.items():
            row[f"{name}_mae"] = mean_absolute_error(actual, forecast)
            row[f"{name}_rmse"] = root_mean_squared_error(actual, forecast)
        rows.append(row)

    results = pd.DataFrame(rows)
    results["mae_gain"] = 1 - results["lgbm_mae"] / results["naive_mae"]
    results["rmse_gain"] = 1 - results["lgbm_rmse"] / results["naive_rmse"]

    pd.set_option("display.width", 250)
    print()
    print(results.round(4).to_string(index=False))
    con.close()