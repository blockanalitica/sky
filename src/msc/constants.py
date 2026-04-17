from decimal import Decimal

from chain_harvester.utils import apy_to_apr

from core.constants import SECONDS_PER_YEAR

PREMIUM_APY = Decimal("0.003")
PREMIUM_APR = apy_to_apr(PREMIUM_APY)
PREMIUM_APR_PER_SECOND = PREMIUM_APR / SECONDS_PER_YEAR
