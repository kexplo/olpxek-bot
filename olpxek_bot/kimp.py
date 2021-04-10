import aiohttp
from asyncache import cached
from cachetools import TTLCache


TWELVE_HOURS = 60 * 60 * 12
BINANCE_BTC_USDT_PRICE_API_URL = (
    "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"  # noqa: E501
)


@cached(TTLCache(maxsize=1, ttl=TWELVE_HOURS))
async def fetch_exchange_rate(api: str, ref_key: str) -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(api) as resp:
            result = await resp.json()

    # "a.b.c" -> result["a"]["b"]["c"]
    ref_keys = ref_key.split(".")
    ref = result
    for key in ref_keys:
        ref = ref[key]

    exchange_rate: float
    if isinstance(ref, str):
        exchange_rate = float(ref.replace(",", ""))
    else:
        exchange_rate = ref
    return exchange_rate


async def fetch_btc_usdt_price_from_binance() -> float:
    async with aiohttp.ClientSession() as session:
        async with session.get(BINANCE_BTC_USDT_PRICE_API_URL) as resp:
            return float((await resp.json())["price"])


class KimpCalculator:
    def __init__(self, exchange_rate_api, exchange_rate_ref_key):
        self.api = exchange_rate_api
        self.ref_key = exchange_rate_ref_key

    async def calc_percent(self, btc_krw_price) -> float:
        exchange_rate = await fetch_exchange_rate(self.api, self.ref_key)
        btc_usdt_price = await fetch_btc_usdt_price_from_binance()
        percent = (btc_krw_price / (btc_usdt_price * exchange_rate) - 1) * 100
        return round(percent, 2)
