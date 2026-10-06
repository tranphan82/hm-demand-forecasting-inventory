import lightgbm as lgb

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

# Function for LightGBM
# LightGBM - Function for train and test set
FEATURE_COLUMNS = [
    "lag_1", "lag_7", "lag_14", "lag_28",
    "rolling_avg_7", "rolling_avg_28",
    "sales_month", "sales_quarter", "sales_week",
    "day_of_week_num", "is_weekend", "is_month_start", "is_month_end",
]
TARGET = "quantity_sold"


def build_train_test(con, split_date, train_sample_pct=10):
    columns = ", ".join(["sales_date", "article_id", TARGET] + FEATURE_COLUMNS)

    train = con.execute(f"""
        SELECT {columns}
        FROM fs_model_features
        WHERE sales_date < ?
          AND lag_7 IS NOT NULL
          AND hash(article_id || CAST(sales_date AS VARCHAR)) % 100 < ?
        ORDER BY sales_date, article_id
    """, [split_date, train_sample_pct]).fetchdf()

    test = con.execute(f"""
        SELECT {columns}
        FROM fs_model_features
        WHERE sales_date >= ?
          AND lag_7 IS NOT NULL
        ORDER BY sales_date, article_id
    """, [split_date]).fetchdf()

    return train, test 

# Building the model LightGBM itself:
DEFAULT_PARAMS = {
    "objective": "tweedie",
    "tweedie_variance_power": 1.2,
    "learning_rate": 0.05,
    "num_leaves": 63,
    "seed": 42,
    "verbosity": -1,
}


def train_lightgbm(train, params=None, num_boost_round=200):
    params = {**DEFAULT_PARAMS, **(params or {})}
    dataset = lgb.Dataset(train[FEATURE_COLUMNS], label=train[TARGET])
    return lgb.train(params, dataset, num_boost_round=num_boost_round)


def predict(model, df):
    return model.predict(df[FEATURE_COLUMNS])


def root_mean_squared_error(actual, predicted):
    return ((actual - predicted) ** 2).mean() ** 0.5