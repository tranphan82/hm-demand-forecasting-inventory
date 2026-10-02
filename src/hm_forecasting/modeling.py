# Define the train/test boundary by date, not by ratio 80/20
def get_split_date(con, test_days=28, table="fs_model_features"):
    return con.execute(f"""
        Select Max(sales_date) - {test_days}
        From {table}
""").fetchone()[0]

# Baseline model is the seasonal-naive forecast itself
def baseline_predictions(con, split_date):
    return con.execute("""
        Select 
            sales_date,
            article_id,
            quantity_sold As actual,
            lag_7 As predicted
        From fs_model_features
        Where sales_date >= ?
        And lag_7 is not null
        Order by sales_date, article_id
""", [split_date]).fetchdf()


def mean_absolute_error(actual, predicted):
    return (actual - predicted).abs().mean()