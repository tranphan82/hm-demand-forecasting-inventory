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