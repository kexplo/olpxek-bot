import asyncio
import io

import discord
from discord.ext import commands
from juga import NaverStockAPI

from olpxek_bot.charts import draw_upbit_chart
from olpxek_bot.config import DefaultConfig
from olpxek_bot.finviz import get_finviz_map_capture
from olpxek_bot.kimp import KimpCalculator
from olpxek_bot.upbit import fetch_candles, fetch_price


class FinanceCog(commands.Cog):
    def __init__(self, config: DefaultConfig):
        self.finviz_cmd_lock = asyncio.Lock()
        self.init_kimp(config)

    def init_kimp(self, config: DefaultConfig):
        self.kimp = None
        if config.kimp is not None:
            self.kimp = KimpCalculator(
                config.kimp.exchange_rate_api_url,
                config.kimp.exchange_rate_result_ref_key,
            )

    @commands.command()
    async def finviz(self, ctx):
        async with self.finviz_cmd_lock:
            await ctx.message.add_reaction("🆗")
            capture = await get_finviz_map_capture()
            await ctx.send(
                file=discord.File(io.BytesIO(capture), filename="finviz.png")
            )

    @commands.command(aliases=("주식", "주가"))
    async def stock(self, ctx, *args):
        if len(args) == 0:
            return

        # parse options
        show_total_infos = False
        graph_option = None
        if len(args) >= 2:
            for option in args[1:]:
                if option.lower() in ["-v", "--verbose", "verbose", "v"]:
                    show_total_infos = True
                    continue
                if option in [
                    "일봉",
                    "주봉",
                    "월봉",
                    "1일",
                    "3개월",
                    "1년",
                    "3년",
                    "10년",
                ]:
                    graph_option = option
                    continue
        query = args[0]

        api = await NaverStockAPI.from_query(query)
        stock_data = await api.fetch_stock_data()

        if stock_data.name_eng is None:
            title = f"{stock_data.name}"
        else:
            title = f"{stock_data.name} ({stock_data.name_eng})"

        market_value_str = ""
        if stock_data.market_value:
            market_value_str = f" / 시총: {stock_data.market_value}"

        embed = discord.Embed(
            title=title,
            url=stock_data.url,
            description=(
                f"{stock_data.symbol_code} "
                f"({stock_data.stock_exchange_name}){market_value_str}\n\n"
                f"**{stock_data.close_price}**\n"
                f"전일비: {stock_data.compare_price}  "
                f"{stock_data.compare_ratio}\n----------"
            ),
            colour=discord.Color.blue(),
        )
        if show_total_infos:
            for k, v in stock_data.total_infos.items():
                embed.add_field(name=k, value=v)
        else:
            embed.add_field(
                name="전체 정보", value="두 번째 인자로 `-v`를 추가하세요"
            )  # fmt: off
        embed.set_footer(text="powered by NAVER stock")

        graph_by_option = {
            "일봉": stock_data.graph_urls.candle_day,
            "주봉": stock_data.graph_urls.candle_week,
            "월봉": stock_data.graph_urls.candle_month,
            "1일": stock_data.graph_urls.day,
            "3개월": stock_data.graph_urls.area_month_three,
            "1년": stock_data.graph_urls.area_year,
            "3년": stock_data.graph_urls.area_year_three,
            "10년": stock_data.graph_urls.area_year_ten,
        }
        if graph_option is not None and graph_by_option.get(graph_option):
            embed.set_image(url=graph_by_option.get(graph_option))
        else:
            embed.set_image(url=stock_data.graph_urls.day)
        await ctx.send(embed=embed)

    @commands.command(aliases=("코인", "cc"))
    async def crypto(self, ctx, ticker):
        price = await fetch_price(ticker)
        embed = discord.Embed(
            title=f"{price.kr_name} {price.ticker}",
            url=f"https://www.upbit.com/exchange?code=CRIX.UPBIT.{price.ticker}",  # noqa: E501
            colour=discord.Color.blue(),
        )

        kimp_str = ""
        if price.ticker == "KRW-BTC" and self.kimp is not None:
            kimp_percent = await self.kimp.calc_percent(price.trade_price)
            kimp_str = f"\n김프: {kimp_percent}%"

        embed.add_field(
            name=f"{price.trade_price:,} {price.currency_code}",
            value=(
                f"{price.signed_change_price:,} ({price.signed_change_rate}%)"
                f"{kimp_str}"
            ),
        )
        embed.set_footer(text="powered by Upbit")

        candles = await fetch_candles(ticker, 60, 100)
        with io.BytesIO() as buf:
            draw_upbit_chart(candles, buf)
            buf.seek(0)
            await ctx.send(
                embed=embed, file=discord.File(buf, filename="chart.png")
            )

    @commands.command(aliases=("김프",))
    async def kimp(self, ctx):
        if self.kimp is None:
            return
        btc_krw_price = await fetch_price("KRW-BTC")
        kimp_percent = await self.kimp.calc_percent(btc_krw_price.trade_price)
        await ctx.send(f"김프: {kimp_percent}% (Upbit <-> Binance)")
