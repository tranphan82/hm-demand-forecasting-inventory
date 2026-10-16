import pandas as pd
from datetime import timedelta 
from hm_forecasting.segmentation import label_segments, product_segments

# Function to define a sample of 3000 with timestop
def select_intermittent_articles(
    con,
    as_of_date,
    max_active_ratio=0.15,
    min_sales_days=30,
    min_active_days=90,
    recent_days=56,
    min_recent_sales=1,
    sample_n=3000,
):
    return con.execute("""
        SELECT article_id
        FROM (
            SELECT
                article_id,
                COUNT(*) AS sales_days,
                COUNT(*) FILTER (WHERE sales_date >= $recent_start) AS recent_sales,
                DATE_DIFF('day', MIN(sales_date), $as_of) AS active_days
            FROM fact_daily_sales
            WHERE sales_date < $as_of
            GROUP BY article_id
        )
        WHERE sales_days >= $min_sales_days
          AND recent_sales >= $min_recent_sales
          AND active_days >= $min_active_days
          AND sales_days * 1.0 / active_days < $max_ratio
        ORDER BY hash(article_id)
        LIMIT $sample_n
    """, {
        "as_of": as_of_date,
        "recent_start": as_of_date - timedelta(days=recent_days),
        "min_sales_days": min_sales_days,
        "min_recent_sales": min_recent_sales,
        "min_active_days": min_active_days,
        "max_ratio": max_active_ratio,
        "sample_n": sample_n,
    }).fetchdf()["article_id"].tolist()



# Function to turn products into time series for DeepAR
def build_series(con, article_ids, end_date):
    df = con.execute("""
        SELECT article_id, sales_date, total_quantity_sold
        FROM fact_daily_sales
        WHERE article_id IN (SELECT UNNEST($ids))
          AND sales_date < $end
        ORDER BY article_id, sales_date
    """, {"ids": article_ids, "end": end_date}).fetchdf()

    last_day = pd.Timestamp(end_date) - pd.Timedelta(days=1)

    series = []
    for article_id, group in df.groupby("article_id"):
        full_index = pd.date_range(group["sales_date"].min(), last_day, freq="D")
        target = (
            group.set_index("sales_date")["total_quantity_sold"]
            .reindex(full_index, fill_value=0)
            .to_numpy(dtype="float32")
        )
        series.append({"item_id": article_id, "start": full_index[0], "target": target})

    return series

# Function to select products by segment
def select_articles_by_segment(
    con, as_of_date, segment_labels, min_sales_days=30, sample_n=None
):
    segments = label_segments(product_segments(con, as_of_date))
    chosen = segments[
        segments["segment"].isin(segment_labels) & (segments["sales_days"] >= min_sales_days)
    ]
    if sample_n is not None and sample_n < len(chosen):
        chosen = chosen.sample(n=sample_n, random_state=42)
    return sorted(chosen["article_id"].tolist())

