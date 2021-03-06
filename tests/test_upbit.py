import json
from pathlib import Path

from aioresponses import aioresponses
import pytest

from olpxek_bot.upbit import (
    CryptoPrice, fetch_price, get_ticker_names, get_tickers
)


@pytest.fixture()
def mock_aioresp():
    with aioresponses() as m:
        yield m


@pytest.fixture()
def fixtures_dir(request):
    return Path(request.fspath.dirname, "fixtures")


@pytest.mark.asyncio
async def test_tickers(fixtures_dir, mock_aioresp):
    with open((fixtures_dir / "upbit_market_all.json"), "r") as f:
        expected_payload = json.loads(f.read())
    mock_aioresp.get("https://api.upbit.com/v1/market/all",
                     payload=expected_payload,
                     headers={
                         "Content-Type": "application/json",
                     })

    tickers = await get_tickers()
    assert 294 == len(tickers)
    assert "KRW-BTC" == tickers[0]
    assert "KRW-ETH" == tickers[1]

    kr_name, en_name = await get_ticker_names("KRW-BTC")
    assert "비트코인" == kr_name
    assert "Bitcoin" == en_name

    kr_name, en_name = await get_ticker_names("kRw-Btc")
    assert "비트코인" == kr_name
    assert "Bitcoin" == en_name


@pytest.mark.asyncio
async def test_prices(fixtures_dir, mock_aioresp):
    with open((fixtures_dir / "upbit_price_krw_btc.json"), "r") as f:
        expected_payload = json.loads(f.read())
    mock_aioresp.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC",
                     payload=expected_payload,
                     headers={
                         "Content-Type": "application/json",
                     },
                     repeat=True)

    expected_price = CryptoPrice(
        "KRW-BTC",
        "비트코인",
        "Bitcoin",
        "KRW",
        55072000,
        -1582000,
        -2.79
    )

    # short ticker
    price0 = await fetch_price("BTC")
    assert expected_price == price0

    # full ticker
    price1 = await fetch_price("KRW-BTC")
    assert expected_price == price1
