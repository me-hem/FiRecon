from decimal import Decimal, ROUND_HALF_UP

ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def money(value) -> Decimal:
    """Normalize a financial value to two decimal places."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
