from dataclasses import dataclass
from typing import Any, cast, Dict, List, Literal, Tuple, Union

import aiohttp
from asyncache import cached
from cachetools import TTLCache


HALF_DAY_SECS = 60 * 60 * 12


@cached(TTLCache(maxsize=1, ttl=HALF_DAY_SECS))
async def fetch_markets() -> Dict[str, Tuple[str, str]]:
    markets = None
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.upbit.com/v1/market/all") as resp:
            markets = await resp.json()
    name_indexer = {}
    for market in markets:
        name_indexer[market["market"]] = (
            market["korean_name"],
            market["english_name"],
        )
    return name_indexer


async def get_tickers() -> Tuple[str, ...]:
    markets = await fetch_markets()
    return tuple(markets.keys())


async def get_ticker_names(ticker: str) -> Tuple[str, str]:
    ticker = ticker.upper()
    markets = await fetch_markets()
    return markets[ticker]


@dataclass
class CryptoPrice:
    ticker: str
    kr_name: str
    en_name: str
    currency_code: str
    trade_price: Union[int, float]
    signed_change_price: Union[int, float]
    signed_change_rate: Union[int, float]


async def fetch_price(ticker: str) -> CryptoPrice:
    tickers = await get_tickers()
    ticker = ticker.upper()
    if "-" not in ticker:
        ticker = "KRW-" + ticker
        # there is no KRW market
        if ticker not in tickers:
            ticker = "BTC-" + ticker

    currency_code = ticker.split("-")[0]

    price_data: Dict[str, Union[str, int, float]] = {}
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.upbit.com/v1/ticker?markets={ticker}"
        ) as resp:
            price_data = cast(List[Any], await (resp.json()))[0]

    ticker_names = await get_ticker_names(ticker)
    trade_price = cast(Union[int, float], price_data["trade_price"])
    signed_change_price = cast(
        Union[int, float], price_data["signed_change_price"]
    )
    signed_change_rate: float = round(
        cast(float, price_data["signed_change_rate"]) * 100, 2
    )

    return CryptoPrice(
        ticker,
        ticker_names[0],
        ticker_names[1],
        currency_code,
        trade_price,
        signed_change_price,
        signed_change_rate,
    )


async def fetch_candles(
    ticker: str, minutes: Literal[1, 3, 5, 10, 30, 60], count: int
) -> List[Dict[str, Union[str, float, int]]]:
    # TODO: to utility function
    tickers = await get_tickers()
    ticker = ticker.upper()
    if "-" not in ticker:
        ticker = "KRW-" + ticker
        # there is no KRW market
        if ticker not in tickers:
            ticker = "BTC-" + ticker

    if count > 200:
        count = 200

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://api.upbit.com/v1/candles/minutes/{minutes}?market={ticker}&count={count}",  # noqa: E501
            headers={"Accept-Encoding": "gzip"},
        ) as resp:
            return await resp.json()
