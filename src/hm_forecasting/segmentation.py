import numpy as np
from datetime import timedelta


def product_segments(
    con,
    as_of_date,
    new_days=90,
    dormant_days=56,
    adi_cutoff=1.32,
    cv2_cutoff=0.49,
    volume_days=365,
):
    return con.execute("""
        WITH stats AS (
            SELECT
                article_id,
                COUNT(*) AS sales_days,
                DATE_DIFF('day', MIN(sales_date), $as_of) AS active_days,
                DATE_DIFF('day', MAX(sales_date), $as_of) AS days_since_last_sale,
                DATE_DIFF('day', MIN(sales_date), $as_of) / CAST(COUNT(*) AS DOUBLE) AS adi,
                CASE WHEN AVG(total_quantity_sold) > 0
                     THEN POWER(STDDEV_POP(total_quantity_sold) / AVG(total_quantity_sold), 2)
                     ELSE 0 END AS cv2,
                COALESCE(SUM(total_quantity_sold) FILTER (WHERE sales_date >= $volume_start), 0) AS units
            FROM fact_daily_sales
            WHERE sales_date < $as_of
            GROUP BY article_id
        ),
        ranked AS (
            SELECT
                *,
                SUM(units) OVER (ORDER BY units DESC, article_id)
                    / NULLIF(SUM(units) OVER (), 0) AS cum_share
            FROM stats
        )
        SELECT
            article_id, sales_days, active_days, days_since_last_sale, adi, cv2, units,
            CASE WHEN active_days < $new_days THEN 'new'
                 WHEN days_since_last_sale > $dormant_days THEN 'dormant'
                 ELSE 'active' END AS lifecycle,
            CASE WHEN adi < $adi_cutoff AND cv2 < $cv2_cutoff THEN 'smooth'
                 WHEN adi < $adi_cutoff THEN 'erratic'
                 WHEN cv2 < $cv2_cutoff THEN 'intermittent'
                 ELSE 'lumpy' END AS demand_pattern,
            CASE WHEN cum_share <= 0.80 THEN 'A'
                 WHEN cum_share <= 0.95 THEN 'B'
                 ELSE 'C' END AS volume_class
        FROM ranked
        ORDER BY article_id
    """, {
        "as_of": as_of_date,
        "volume_start": as_of_date - timedelta(days=volume_days),
        "new_days": new_days,
        "dormant_days": dormant_days,
        "adi_cutoff": adi_cutoff,
        "cv2_cutoff": cv2_cutoff,
    }).fetchdf()

# A helper for segment label (four-window segment evaluation)
def label_segments(segments):
    labelled = segments.copy()
    labelled["segment"] = np.where(
        labelled["lifecycle"] == "active",
        "active/" + labelled["demand_pattern"],
        labelled["lifecycle"],
    )
    return labelled
