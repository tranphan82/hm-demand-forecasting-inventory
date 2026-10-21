from datetime import date, timedelta

import duckdb
import numpy as np
import pandas as pd

from hm_forecasting.baselines import rolling_window_totals
from hm_forecasting.deepar import build_series
from hm_forecasting.inventory import GOODWILL_BY_CLASS, CostAssumptions, assumptions_for_class
from hm_forecasting.policy import evaluate_policies, summarise_policies
from hm_forecasting.segmentation import label_segments, product_segments

ORIGIN = date(2020, 6, 24)
HORIZON = 91

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

    products = [
        {
            "article_id": article_id,
            "segment": segments.loc[article_id, "segment"],
            "volume_class": segments.loc[article_id, "volume_class"],
            "windows": rolling_window_totals(train[article_id], HORIZON),
            "samples": totals[i],
            "actual": actual[article_id],
        }
        for i, article_id in enumerate(ids)
    ]

    pd.set_option("display.width", 250)

    base_costs = {c: assumptions_for_class(c, horizon_days=HORIZON) for c in "ABC"}
    results = evaluate_policies(products, base_costs, HORIZON)
    for column in ["segment", "volume_class"]:
        print(f"\nBy {column}:")
        print(results.groupby(column).apply(summarise_policies, include_groups=False).round(3).to_string())
    print("\nAll products:")
    print(summarise_policies(results).round(3).to_string())

    scenarios = []
    for scale in [0.0, 0.5, 1.0, 2.0]:
        for markdown in [0.4, 0.6, 0.8]:
            costs = {
                c: CostAssumptions(
                    goodwill_multiplier=GOODWILL_BY_CLASS[c] * scale,
                    clearance_markdown=markdown,
                    horizon_days=HORIZON,
                )
                for c in "ABC"
            }
            summary = summarise_policies(evaluate_policies(products, costs, HORIZON))
            scenarios.append({
                "goodwill_scale": scale,
                "markdown": markdown,
                "service_A": costs["A"].service_level,
                "service_C": costs["C"].service_level,
                "planner_cost%": summary["planner_cost%"],
                "segment_choice_cost%": summary["segment_choice_cost%"],
            })

    sensitivity = pd.DataFrame(scenarios)
    sensitivity["saving%"] = 100 * (1 - sensitivity["segment_choice_cost%"] / sensitivity["planner_cost%"])
    print("\nSensitivity to cost assumptions:")
    print(sensitivity.round(3).to_string(index=False))


