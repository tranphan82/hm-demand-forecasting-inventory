import numpy as np


def quantile_stock(samples, tau):
    return np.quantile(samples, tau, axis=-1)


def normal_stock(mean, std, k):
    return np.maximum(mean + k * std, 0.0)


def period_cost(actual, stock, shortage_cost, excess_cost):
    short = np.maximum(actual - stock, 0.0)
    excess = np.maximum(stock - actual, 0.0)
    return shortage_cost * short + excess_cost * excess
