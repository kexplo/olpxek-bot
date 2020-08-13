from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, TypedDict

from asyncache import cached
from cachetools import LRUCache
import httpx


class InvalidStockQuery(Exception):
    pass


@dataclass
class NaverStockMetadata:
    symbol_code: str
    display_name: str
    stock_exchange_name: str
    url: str
    reuters_code: str
    is_etf: bool = field(init=False)
    is_global: bool = field(init=False)

    def __post_init__(self):
        self.is_etf = 'etf' in self.url
        self.is_global = self.stock_exchange_name not in ['코스피', '코스닥']


@dataclass
class NaverStockData:
    name: str
    name_eng: str
    symbol_code: str
    close_price: str
    stock_exchange_name: str
    compare_price: str
    compare_ratio: str
    total_infos: Dict[str, str]  # TODO: ETF랑 Stock이랑 별도로 정의하면 좋겠다
    day_graph_url: str = field(init=False)
    candle_graph_url: str = field(init=False)

    def __post_init__(self):
        if self.compare_price[0] != '-':
            self.compare_price = '🔺' + self.compare_price
        if self.compare_ratio[0] != '-':
            self.compare_ratio = '🔺' + self.compare_ratio


class NaverStockAPIResponse(TypedDict):
    stockName: str  # noqa: N815
    stockNameEng: str  # noqa: N815
    symbolCode: str  # noqa: N815
    closePrice: str  # noqa: N815
    stockExchangeType: Dict[str, str]  # noqa: N815
    compareToPreviousClosePrice: str  # noqa: N815
    stockItemTotalInfos: List[Dict[str, str]]  # noqa: N815
    fluctuationsRatio: str  # noqa: N815


class NaverStockAPIParser(metaclass=ABCMeta):
    def __init__(self, stock_metadata: NaverStockMetadata):
        self.metadata = stock_metadata

    def get_day_graph_url(self):
        return (
            f'https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/day/'
            f'{self.metadata.reuters_code}_end.png'
        )

    def get_candle_graph_url(self):
        return(
            f'https://ssl.pstatic.net/imgfinance/chart/mobile/world/item/'
            f'candle/day/{self.metadata.reuters_code}_end.png'
        )

    @abstractmethod
    async def _get_stock_data_impl(self) -> NaverStockData:
        pass

    async def get_stock_data(self) -> NaverStockData:
        stock_data = await self._get_stock_data_impl()
        stock_data.day_graph_url = self.get_day_graph_url()
        stock_data.candle_graph_url = self.get_candle_graph_url()
        return stock_data

    @classmethod
    def api_response_to_stock_data(
        cls,
        response: NaverStockAPIResponse
    ) -> NaverStockData:
        total_infos = {}  # type: Dict[str, str]
        for total_info in response['stockItemTotalInfos']:
            total_infos[total_info['key']] = total_info['value']
            # code, key, value[,
            #   compareToPreviousPrice[code(2,5), text(상승,하락), name]]

        return NaverStockData(
            response['stockName'],
            response['stockNameEng'],
            response['symbolCode'],
            response['closePrice'],
            response['stockExchangeType']['name'],
            response['compareToPreviousClosePrice'],
            response['fluctuationsRatio'],
            total_infos
        )


class NaverStockAPIGlobalETFParser(NaverStockAPIParser):
    async def _get_stock_data_impl(self) -> NaverStockData:
        json_dict = None
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f'https://api.stock.naver.com/etf/'
                f'{self.metadata.reuters_code}/basic')
            json_dict = r.json()
        return self.api_response_to_stock_data(json_dict)


class NaverStockAPIGlobalStockParser(NaverStockAPIParser):
    async def _get_stock_data_impl(self) -> NaverStockData:
        json_dict = None
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f'https://api.stock.naver.com/stock/'
                f'{self.metadata.reuters_code}/basic')
            json_dict = r.json()
        return self.api_response_to_stock_data(json_dict)


class NaverStockAPIKoreaStockParser(NaverStockAPIParser):
    pass


class NaverStockAPIParserFactory(object):
    @classmethod
    def from_metadata(cls, stock_metadata: NaverStockMetadata):
        if stock_metadata.is_global:
            if stock_metadata.is_etf:
                return NaverStockAPIGlobalETFParser(stock_metadata)
            return NaverStockAPIGlobalStockParser(stock_metadata)
        # TODO: kospi, kosdaq
        raise NotImplementedError


class NaverStockAPI(object):
    @classmethod
    async def from_query(cls, query: str):
        metadata = await cls.get_metadata(query)
        return NaverStockAPI(metadata)

    @classmethod
    @cached(LRUCache(maxsize=20))
    async def get_metadata(cls, query: str) -> NaverStockMetadata:
        url_tmpl = 'https://ac.finance.naver.com/ac?q={query}&q_enc=euc-kr&t_koreng=1&st=111&r_lt=111'  # noqa: E501
        async with httpx.AsyncClient() as client:
            r = await client.get(url_tmpl.format(query=query))
            try:
                json_dict = r.json()
                first_item = json_dict['items'][0][0]
            except IndexError:
                raise InvalidStockQuery(json_dict)
            symbol_code, display_name, market, url, reuters_code = first_item
            # NOTE: 모든 값이 list로 감싸져있다
        return NaverStockMetadata(symbol_code[0], display_name[0], market[0],
                                  f'https://m.stock.naver.com{url[0]}',
                                  reuters_code[0])

    def __init__(self, metadata: NaverStockMetadata):
        self.metadata = metadata
        self.parser = NaverStockAPIParserFactory.from_metadata(metadata)

    def get_day_graph_url(self) -> str:
        return self.parser.get_day_graph_url()

    def get_candle_graph_url(self) -> str:
        return self.parser.get_candle_graph_url()

    async def get_stock_data(self) -> NaverStockData:
        return await self.parser.get_stock_data()
