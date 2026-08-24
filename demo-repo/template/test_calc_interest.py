from calc_interest import calc_interest


def test_one_year():
    assert calc_interest(1000, 12, 12) == 126.83


def test_six_months():
    assert calc_interest(1000, 12, 6) == 61.52


def test_no_time_earns_nothing():
    assert calc_interest(1000, 12, 0) == 0.0
