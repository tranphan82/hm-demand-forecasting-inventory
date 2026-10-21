import numpy as np
import pandas as pd
from hm_forecasting.inventory import k_from_cis


def quantile_stock(samples, tau):
    return np.quantile(samples, tau, axis=-1)


def normal_stock(mean, std, k):
    return np.maximum(mean + k * std, 0.0)


def period_cost(actual, stock, shortage_cost, excess_cost):
    short = np.maximum(actual - stock, 0.0)
    excess = np.maximum(stock - actual, 0.0)
    return shortage_cost * short + excess_cost * excess

# Sensitivity table
POLICIES = ["planner", "cis_normal", "hist_quantile", "deepar_quantile", "segment_choice"]
DEEPAR_SEGMENTS = ["active/intermittent", "active/lumpy"]


def evaluate_policies(products, costs_by_class, horizon, planner_k=1.645, cap_multiple=3):
    rows = []
    for p in products:
        windows = p["windows"]
        mean, std, peak = windows.mean(), windows.std(), windows.max()
        c = costs_by_class[p["volume_class"]]
        k = k_from_cis(q=horizon, ce=c.holding_cost_per_year, d=365, cs=c.shortage_cost)

        stocks = {
            "planner": normal_stock(mean, std, planner_k),
            "cis_normal": normal_stock(mean, std, k),
            "hist_quantile": quantile_stock(windows, c.service_level),
            "deepar_quantile": min(
                quantile_stock(p["samples"], c.service_level), cap_multiple * peak
            ),
        }
        stocks["segment_choice"] = (
            stocks["deepar_quantile"]
            if p["segment"] in DEEPAR_SEGMENTS
            else stocks["hist_quantile"]
        )

        row = {
            "article_id": p["article_id"],
            "segment": p["segment"],
            "volume_class": p["volume_class"],
            "actual": p["actual"],
        }
        for name, stock in stocks.items():
            row[f"{name}_stock"] = stock
            row[f"{name}_cost"] = period_cost(
                p["actual"], stock, c.shortage_cost, c.excess_cost_per_period
            )
        rows.append(row)

    return pd.DataFrame(rows)


def summarise_policies(group):
    sales = group["actual"].sum()
    out = {"products": len(group)}
    for name in POLICIES:
        out[f"{name}_cost%"] = 100 * group[f"{name}_cost"].sum() / sales
    for name in POLICIES:
        out[f"{name}_stockout"] = (group["actual"] > group[f"{name}_stock"]).mean()
    return pd.Series(out)
