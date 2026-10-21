from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd

from hm_forecasting.baselines import rolling_window_totals
from hm_forecasting.deepar import build_series
from hm_forecasting.inventory import assumptions_for_class, k_from_cis
from hm_forecasting.policy import normal_stock, period_cost, quantile_stock
from hm_forecasting.segmentation import label_segments, product_segments

ORIGIN = date(2019, 12, 26)
HORIZON = 91
PLANNER_K = 1.645
CAP_MULTIPLE = 3
DEEPAR_SEGMENTS = ["active/intermittent", "active/lumpy"]
POLICIES = ["planner", "cis_normal", "hist_quantile", "deepar_quantile", "segment_choice"]



if __name__ == "__main__":
    saved = np.load(f"data/processed/deepar_totals_{ORIGIN}.npz")
    ids = saved["ids"].tolist()
    totals = saved["totals"]

    con = duckdb.connect("hm_retail.duckdb", read_only=True)
    segments = label_segments(product_segments(con, ORIGIN)).set_index("article_id")
    train = {s["item_id"]: s["target"] for s in build_series(con, ids, ORIGIN)}
    actual = {
        s["item_id"]: s["target"][-HORIZON:].sum()
        for s in build_series(con, ids, ORIGIN + timedelta(days=HORIZON))
    }
    con.close()

    costs = {c: assumptions_for_class(c, horizon_days=HORIZON) for c in "ABC"}

    rows = []
    for i, article_id in enumerate(ids):
        windows = rolling_window_totals(train[article_id], HORIZON)
        mean, std, peak = windows.mean(), windows.std(), windows.max()

        volume_class = segments.loc[article_id, "volume_class"]
        c = costs[volume_class]
        k = k_from_cis(q=HORIZON, ce=c.holding_cost_per_year, d=365, cs=c.shortage_cost)

        stocks = {
            "planner": normal_stock(mean, std, PLANNER_K),
            "cis_normal": normal_stock(mean, std, k),
            "hist_quantile": quantile_stock(windows, c.service_level),
            "deepar_quantile": min(
                quantile_stock(totals[i], c.service_level), CAP_MULTIPLE * peak
            ),
        }

        stocks["segment_choice"] = (
            stocks["deepar_quantile"]
            if segments.loc[article_id, "segment"] in DEEPAR_SEGMENTS
            else stocks["hist_quantile"]
        )

        row = {
            "article_id": article_id,
            "segment": segments.loc[article_id, "segment"],
            "volume_class": volume_class,
            "actual": actual[article_id],
        }
        for name, stock in stocks.items():
            row[f"{name}_stock"] = stock
            row[f"{name}_cost"] = period_cost(
                row["actual"], stock, c.shortage_cost, c.excess_cost_per_period
            )
        rows.append(row)

    results = pd.DataFrame(rows)

    def summarise(group):
        sales = group["actual"].sum()
        out = {"products": len(group)}
        for name in POLICIES:
            out[f"{name}_cost%"] = 100 * group[f"{name}_cost"].sum() / sales
        for name in POLICIES:
            out[f"{name}_stockout"] = (group["actual"] > group[f"{name}_stock"]).mean()
        return pd.Series(out)

    pd.set_option("display.width", 250)
    for column in ["segment", "volume_class"]:
        print(f"\nBy {column}:")
        print(results.groupby(column).apply(summarise, include_groups=False).round(3).to_string())
    print("\nAll products:")
    print(summarise(results).round(3).to_string())

