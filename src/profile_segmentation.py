from datetime import date

import duckdb

from hm_forecasting.segmentation import product_segments

con = duckdb.connect("hm_retail.duckdb", read_only=True)
segments = product_segments(con, date(2020, 8, 25))
con.close()

print(f"Products: {len(segments):,}")

print("\nLifecycle:")
print(segments["lifecycle"].value_counts())

print("\nDemand pattern among active products:")
print(segments[segments["lifecycle"] == "active"]["demand_pattern"].value_counts())

print("\nProducts by volume class:")
print(segments["volume_class"].value_counts())

print("\nShare of recent units by volume class:")
print((segments.groupby("volume_class")["units"].sum() / segments["units"].sum()).round(3))


