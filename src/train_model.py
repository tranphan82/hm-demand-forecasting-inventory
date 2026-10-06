import duckdb
import pandas as pd

from hm_forecasting.modeling import (
    FEATURE_COLUMNS,
    build_train_test,
    get_split_date,
    mean_absolute_error,
    predict,
    root_mean_squared_error,
    train_lightgbm,
)

if __name__ == "__main__":
    con = duckdb.connect("hm_retail.duckdb", read_only=True)

    split_date = get_split_date(con)
    print(f"Split date: {split_date}")

    train, test = build_train_test(con, split_date)
    print(f"Train rows: {len(train):,}   Test rows: {len(test):,}")

    print("Training LightGBM...")
    model = train_lightgbm(train)
    predictions = predict(model, test)

    actual = test["quantity_sold"]
    forecasts = {
        "Predict zero": pd.Series(0.0, index=actual.index),
        "Seasonal-naive (lag_7)": test["lag_7"],
        "LightGBM (Tweedie)": predictions,
    }

    print()
    for name, forecast in forecasts.items():
        mae = mean_absolute_error(actual, forecast)
        rmse = root_mean_squared_error(actual, forecast)
        print(f"{name:<26} MAE {mae:.4f}   RMSE {rmse:.4f}")

    print("\nFeature importance (total gain):")
    importance = sorted(
        zip(FEATURE_COLUMNS, model.feature_importance(importance_type="gain")),
        key=lambda pair: -pair[1],
    )
    for name, gain in importance:
        print(f"  {name:<16} {gain:,.0f}")

    con.close()