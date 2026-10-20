import numpy as np 

# a classic baseline (TSB)
def tsb_rate(target, alpha=0.1, beta=0.1):
    probability = 1.0
    size = float(target[0])

    for value in target[1:]:
        occurred = value > 0
        probability += beta * (float(occurred) - probability)
        if occurred:
            size += alpha * (value - size)

    return probability * size

# These two below function are for add the comparision (quantiles) for cost layer
def rolling_window_totals(target, window=28):
    cumulative = np.concatenate([[0.0], np.cumsum(target, dtype="float64")])
    if len(target) < window:
        return np.array([cumulative[-1]])
    return cumulative[window:] - cumulative[:-window]


def empirical_quantile_total(target, window=28, q=0.9):
    return float(np.quantile(rolling_window_totals(target, window), q))