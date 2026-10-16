import pandas as pd
from datetime import date

from hm_forecasting.segmentation import product_segments, label_segments

AS_OF = date(2024, 4, 10)

# Test for one window
def test_product_segments_classify_each_rule(segments_con):
    result = product_segments(segments_con, AS_OF).set_index("article_id")

    labels = result[["lifecycle", "demand_pattern", "volume_class"]].to_dict("index")

    assert labels == {
        "SMOOTH": {"lifecycle": "active", "demand_pattern": "smooth", "volume_class": "A"},
        "ERRATIC": {"lifecycle": "active", "demand_pattern": "erratic", "volume_class": "A"},
        "INTERMITTENT": {"lifecycle": "active", "demand_pattern": "intermittent", "volume_class": "B"},
        "LUMPY": {"lifecycle": "active", "demand_pattern": "lumpy", "volume_class": "B"},
        "DORMANT": {"lifecycle": "dormant", "demand_pattern": "intermittent", "volume_class": "C"},
        "NEW": {"lifecycle": "new", "demand_pattern": "intermittent", "volume_class": "C"},
    }

# Test for one window
def test_product_segments_compute_adi_cv2_and_recency(segments_con):
    result = product_segments(segments_con, AS_OF).set_index("article_id")

    assert result.loc["SMOOTH", "adi"] == 1.0
    assert result.loc["INTERMITTENT", "adi"] == 5.0
    assert abs(result.loc["ERRATIC", "cv2"] - 0.81) < 1e-9
    assert result.loc["DORMANT", "days_since_last_sale"] == 91

# Test for 4-window segmentation
def test_label_segments_uses_demand_pattern_only_for_active_products():
    segments = pd.DataFrame({
        "lifecycle": ["active", "dormant", "new"],
        "demand_pattern": ["lumpy", "intermittent", "smooth"],
    })

    labelled = label_segments(segments)

    assert labelled["segment"].tolist() == ["active/lumpy", "dormant", "new"]


