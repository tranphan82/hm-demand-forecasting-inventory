import duckdb
import numpy as np
import pandas as pd

from hm_forecasting.modeling import (
    FEATURE_COLUMNS,
    build_train_test,
    get_split_date,
    mean_absolute_error,
    predict,
    root_mean_squared_error,
    score_by_segment,
    train_lightgbm,
    wape_by_level,
)
from hm_forecasting.segmentation import product_segments

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
        "zero": pd.Series(0.0, index=actual.index),
        "naive": test["lag_7"],
        "ma7": test["rolling_avg_7"],
        "lgbm": predictions,
    }

    print("\nOverall:")
    for name, forecast in forecasts.items():
        mae = mean_absolute_error(actual, forecast)
        rmse = root_mean_squared_error(actual, forecast)
        print(f"  {name:<8} MAE {mae:.4f}   RMSE {rmse:.4f}")

    print("\nFeature importance (total gain):")
    importance = sorted(
        zip(FEATURE_COLUMNS, model.feature_importance(importance_type="gain")),
        key=lambda pair: -pair[1],
    )
    for name, gain in importance:
        print(f"  {name:<16} {gain:,.0f}")

    segments = product_segments(con, split_date)

    groups = con.execute("SELECT article_id, product_group_name FROM dim_product").fetchdf()

    con.close()

    # For segment evaluation: 
    segments["segment"] = np.where(
        segments["lifecycle"] == "active",
        "active/" + segments["demand_pattern"],
        segments["lifecycle"],
    )

    pd.set_option("display.width", 250)
    for column in ["segment", "volume_class"]:
        print(f"\nBy {column}:")
        print(score_by_segment(test, forecasts, segments, column).round(4).to_string(index=False))

    # For WAPE
    frame = test[["sales_date", "article_id"]].merge(groups, on="article_id", how="left")
    frame["week"] = frame["sales_date"].dt.to_period("W").dt.start_time
    frame["actual"] = actual.to_numpy()
    for name, forecast in forecasts.items():
        frame[name] = np.asarray(forecast)

    levels = {
        "article-day": ["article_id", "sales_date"],
        "article-week": ["article_id", "week"],
        "group-day": ["product_group_name", "sales_date"],
        "group-week": ["product_group_name", "week"],
        "total-week": ["week"],
    }
    print("\nWAPE by aggregation level (lower is better):")
    print(wape_by_level(frame, list(forecasts), levels).round(4).to_string(index=False))