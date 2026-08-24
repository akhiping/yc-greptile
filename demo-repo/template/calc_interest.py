def calc_interest(principal, annual_rate, months):
    """Return the total interest earned, compounding monthly.

    The rate is given as an annual percentage, e.g. 12 for 12% a year.
    """
    rate = annual_rate / 100
    total = principal * (1 + rate) ** (months / 12)
    return round(total - principal, 2)
