import pandas as pd

# Function to define a sample of 3000 with timestop
def select_intermittent_articles(
    con,
    as_of_date,
    max_active_ratio=0.15,
    min_sales_days=30,
    min_active_days=90,
    sample_n=3000,
):
    return con.execute("""
        SELECT article_id
        FROM (
            SELECT
                article_id,
                COUNT(*) AS sales_days,
                DATE_DIFF('day', MIN(sales_date), $as_of) AS active_days
            FROM fact_daily_sales
            WHERE sales_date < $as_of
            GROUP BY article_id
        )
        WHERE sales_days >= $min_sales_days
          AND active_days >= $min_active_days
          AND sales_days * 1.0 / active_days < $max_ratio
        ORDER BY hash(article_id)
        LIMIT $sample_n
    """, {
        "as_of": as_of_date,
        "min_sales_days": min_sales_days,
        "min_active_days": min_active_days,
        "max_ratio": max_active_ratio,
        "sample_n": sample_n,
    }).fetchdf()["article_id"].tolist()

# Function to turn products into time series for DeepAR
def build_series(con, article_ids, end_date):
    df = con.execute("""
        Select 
            article_id, 
            sales_date, 
            total_quantity_sold
        From fact_daily_sales
        Where article_id In (Select UNNEST($ids)) 
            And sales_date < $end
        Order by article_id, sales_date
    """, {"ids": article_ids, "end": end_date}
    ).fetchdf()

    last_day = pd.Timestamp(end_date) - pd.Timedelta(days=1)

    series = []

    for article_id, group in df.groupby("article_id"): 
        full_index = pd.date_range(group["sales_date"].min(), last_day, freq="D")
        target = (group.set_index("sales_date")["total_quantity_sold"]
                  .reindex(full_index, fill_value=0)
                  .to_numpy(dtype="float32")
                  )
        series.append({"item_id": article_id,
                       "start": full_index[0],
                       "target": target
                       })
        return series