from decimal import Decimal

from core.constants import SECONDS_PER_YEAR


def calculate_apy_from_apr(rate):
    return pow(Decimal("1") + rate / SECONDS_PER_YEAR, SECONDS_PER_YEAR) - Decimal("1")
