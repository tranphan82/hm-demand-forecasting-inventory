from datetime import date

from hm_forecasting.deepar import select_intermittent_articles

AS_OF = date(2024, 4, 10)
RULES = {"min_sales_days": 5, "min_active_days": 60}


def test_select_intermittent_articles_applies_all_rules(intermittent_con):
    selected = select_intermittent_articles(intermittent_con, AS_OF, sample_n=10, **RULES)

    assert sorted(selected) == ["A_SPARSE", "F_SPARSE2", "H_BECOMES_DENSE"]


def test_select_intermittent_articles_sample_is_exact_and_repeatable(intermittent_con):
    first = select_intermittent_articles(intermittent_con, AS_OF, sample_n=2, **RULES)
    second = select_intermittent_articles(intermittent_con, AS_OF, sample_n=2, **RULES)

    assert len(first) == 2
    assert first == second