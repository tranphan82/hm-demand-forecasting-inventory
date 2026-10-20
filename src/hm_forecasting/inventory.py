import math

from scipy.optimize import brentq
from scipy.stats import norm
from dataclasses import dataclass

@dataclass(frozen=True)
class CostAssumptions:
    gross_margin: float = 0.50
    clearance_markdown: float = 0.60
    holding_rate: float = 0.35
    goodwill_multiplier: float = 2.0
    horizon_days: int = 91 

    @property
    def unit_cost(self):
        return 1 - self.gross_margin

    @property
    def shortage_cost(self):
        return self.gross_margin * (1 + self.goodwill_multiplier)

    @property
    def holding_cost_per_year(self):
        return self.holding_rate * self.unit_cost

    @property
    def excess_cost_per_period(self):
        salvage = 1 - self.clearance_markdown
        markdown_loss = max(self.unit_cost - salvage, 0.0)
        return markdown_loss + self.holding_cost_per_year * self.horizon_days / 365

    @property
    def service_level(self):
        return critical_ratio(self.shortage_cost, self.excess_cost_per_period)


def critical_ratio(cs, ce):
    return cs / (cs + ce)


def loss_function(k):
    return norm.pdf(k) - k * (1 - norm.cdf(k))


def k_from_csl(stockout_probability):
    return norm.ppf(1 - stockout_probability)


def k_from_ifr(ifr, q, sigma):
    target = (q / sigma) * (1 - ifr)
    return brentq(lambda k: loss_function(k) - target, -6, 6)


def k_from_cis(q, ce, d, cs):
    return norm.ppf(1 - q * ce / (d * cs))


def k_from_csoe(b1, d, ce, sigma, q, k_min=0.0):
    ratio = b1 * d / (ce * sigma * q * math.sqrt(2 * math.pi))
    if ratio <= 1:
        return k_min
    return math.sqrt(2 * math.log(ratio))


def event_cost(cs, daily_demand, event_days=7, fixed_cost=0.0):
    return cs * daily_demand * event_days + fixed_cost


GOODWILL_BY_CLASS = {"A": 2.0, "B": 1.0, "C": 0.0}

def assumptions_for_class(volume_class, **overrides):
    return CostAssumptions(goodwill_multiplier=GOODWILL_BY_CLASS[volume_class], **overrides)