import asyncio
import io
import random
from typing import Dict, Tuple

import discord
from discord.ext import commands
from juga import NaverStockAPI

from olpxek_bot.stock import get_finviz_map_capture


# a check that disables private messages except the owners
async def owner_or_guild_only(ctx):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if not is_owner and ctx.guild is None:
        raise commands.NoPrivateMessage()
    return True


class OlpxekBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.text_reactions = (
            {}
        )  # type: Dict[Tuple[str, ...], Tuple[str, ...]]  # noqa: E501
        self.cached_emojis = {}  # type: Dict[str, discord.Emoji]
        self.finviz_cmd_lock = asyncio.Lock()
        # disable pm
        bot.add_check(owner_or_guild_only)

    def _bot_init(self):
        self._cache_emojis(self.bot)

    def _cache_emojis(self, bot):
        def find_emoji(name):
            return discord.utils.find(lambda x: x.name == name, bot.emojis)

        cache_emoji_names = ["_x", "_v", "small_blue_triangle_down"]
        for emoji_name in cache_emoji_names:
            emoji = find_emoji(emoji_name)
            if emoji is not None:
                self.cached_emojis[emoji_name] = emoji

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong")

    @commands.command(aliases=("주사위",))
    async def dice(self, ctx, arg):
        """
        1d100. https://en.wikipedia.org/wiki/Dice_notation#Standard_notation
        """
        if "d" not in arg:
            return
        try:
            roll_count, faces = map(int, arg.split("d", 1))
        except ValueError:
            return await ctx.message.add_reaction(self.cached_emojis["_x"])
        if roll_count > 50:
            return await ctx.send("굴릴 주사위가 너무 많아요 :(")
        if roll_count <= 0 or faces <= 0:
            return await ctx.message.add_reaction(self.cached_emojis["_x"])

        rolled_numbers = [
            random.randint(1, faces) for x in range(roll_count)  # noqa: S311
        ]
        result_str = ", ".join(map(str, rolled_numbers))
        await ctx.send(f"{arg} 결과: {result_str}")

    @commands.command(aliases=("골라", "뽑아", "뽑기"))
    async def choice(self, ctx, *args):
        if len(args) == 0:
            return
        await ctx.send(random.choice(args))  # noqa: S311

    @commands.command(aliases=("섞어",))
    async def shuffle(self, ctx, *args):
        if len(args) == 0:
            return
        items = list(args)
        random.shuffle(items)
        await ctx.send(" ".join(items))

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

    @commands.Cog.listener()
    async def on_ready(self):
        self._bot_init()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        for keywords, reactions in self.text_reactions.items():
            for keyword in keywords:
                if keyword in message.content:
                    return await message.channel.send(
                        random.choice(reactions)  # noqa: S311
                    )

    def update_text_reactions(
        self, comma_separated_keywords: str, reactions: Tuple[str, ...]
    ):
        keywords = tuple(map(str.strip, comma_separated_keywords.split(",")))
        self.text_reactions[keywords] = reactions
