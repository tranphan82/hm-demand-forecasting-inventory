# H&M Retail Demand Forecasting and Inventory Cost Layer

![tests](https://github.com/tranphan82/hm-demand-forecasting-inventory/actions/workflows/ci.yml/badge.svg)

## Summary

Retail stock decisions depend on how much each product will sell over the next quarter, and most products sell rarely and unpredictably. This project builds a forecasting pipeline on H&M's transaction data (31.8M transactions, 105K products, Sept 2018 to Sept 2020), groups products by how they behave, and compares forecasting methods group by group. **Choosing the method per group, instead of applying one rule to everything, cut the cost of over- and under-stocking by about 31% in backtests on two separate quarters.**

## Key results

- **Segment-chosen stock levels cost about 31 to 32% less than a flat 95% planner rule** (cost = shortages plus leftover stock, measured as a share of sales). The result held on two 91-day windows: 32.0% (origin 2020-06-24) and 31.2% on a held-out window (origin 2019-12-26) whose method assignment was fixed before it was scored.
- The saving stayed positive in **all 24 combinations** of cost assumptions tried (goodwill penalty for stockouts of 0 to 2x margin, clearance markdown of 40 to 80%), from about 4% to 64%, with a median near 35%. It is smallest when leftover stock costs almost nothing.
- **One-day-ahead LightGBM forecasts** beat the best 7- or 28-day moving average in all four backtest windows: RMSE (an error measure that penalises big misses) 13 to 22% lower, MAE (average error size) 2 to 21% lower.
- **Accuracy depends strongly on how finely you forecast.** Measured by WAPE (the share of demand missed), LightGBM misses 59% of demand for a single article on a single day, 26% for an article in a week, and **6% for a product group in a week** (a 7-day average misses 10%).

## Approach

1. **Data engineering (DuckDB).** Raw CSVs, staging tables, dimension and daily fact tables, a dense product-by-day grid (43M rows, 84% of them zero-sales days), then lag and rolling-average features that never include the day being predicted. Missing values were small (1.16% of customers lack an age, 0.39% of products lack a description) and were kept and labelled "Unknown", so no transactions were lost.
2. **Segmentation.** Each product is classified as of a cutoff date by lifecycle (new, active or dormant), demand pattern (smooth, erratic, intermittent or lumpy, based on how often it sells and how variable the sale sizes are), and volume class (A, B, C by share of units). On 2020-08-25, 64% of 100,968 products were dormant (no sale in 56 days), and only 504 of 28,628 active products were "smooth".
3. **Forecasting methods compared per segment.** Moving averages; LightGBM with a Tweedie loss (suited to data with many zeros); TSB (a classic intermittent-demand method); and DeepAR (a neural network that forecasts a full probability distribution, run via GluonTS and PyTorch on CPU).
4. **Cost layer.** Newsvendor logic: the best service level is `Cs / (Cs + Ce)`, shortage cost over shortage plus excess cost. Costs per $1 of price: 50% gross margin, a goodwill penalty for stockouts of 2x / 1x / 0 margin for volume classes A / B / C, 60% clearance markdown on leftovers, 35% annual holding cost, and a 91-day (13-week) planning horizon. This gives service levels of about 91% / 87% / 78%. Stock levels are set at that percentile of each product's forecast demand and scored against what actually sold.

## Which method for which segment

| Segment | Best method for stock levels (both backtest origins) |
|---|---|
| Lumpy and intermittent (active) | DeepAR percentiles. Lumpy: about 48 to 50% lower cost than using the product's own history. Intermittent: roughly equal in the held-out window |
| Erratic and smooth (active) | The product's own historical percentile (DeepAR over-insures) |
| Dormant | No forecast; flag for markdown or liquidation |

## Limitations

- Two backtest origins; the held-out one follows the holiday peak and ends as COVID disruption begins.
- Prices are anonymised in this dataset, so costs are expressed per $1 of retail price (as a percentage of sales).
- DeepAR's average forecasts were poor (they over-forecast fading products); only its percentiles are used for stock decisions.
- The cost results depend on assumed margins, markdowns and penalties (see the sensitivity analysis).
- Forecasting brand-new products with no history (cold start) is not solved.
- Observed sales are not the same as demand: stock-outs and restocks create surges that no model here anticipates.

## Running it

```bash
pip install -r requirements.txt          # pipeline, dashboard, tests
pip install -r requirements-deepar.txt   # adds PyTorch and GluonTS for DeepAR
pytest                                    # 63 tests on small synthetic fixtures
```

1. Download the H&M Personalized Fashion Recommendations data from Kaggle into `data/raw/` (not included in this repository).
2. `python src/run_pipeline.py` builds the DuckDB database and Parquet exports.
3. `python src/train_model.py` and `python src/backtest.py` run the LightGBM evaluation and the four-window backtest.
4. `python src/train_deepar.py` then `python src/cost_backtest.py` run DeepAR and the cost backtest (set `ORIGIN` in both scripts).
5. `streamlit run dashboard/app.py` launches the dashboard (sales velocity, dead stock, geospatial demand).

## In production

DeepAR here runs locally on CPU on up to about 25,000 series. In production this would be a scheduled job (for example SageMaker or Vertex AI, or Colab for one-off GPU runs) that reads from a warehouse, writes forecast percentiles back to a table, and monitors for drift. The guardrail used here (capping forecasts at 3x a product's best-ever 91-day total) is a simple example of the checks such a system needs.

## Repository layout

`src/hm_forecasting/` package (pipeline, features, segmentation, modeling, DeepAR, cost policy) · `src/` run scripts · `tests/` pytest suite · `dashboard/` Streamlit app