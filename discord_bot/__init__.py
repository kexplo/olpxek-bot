import asyncio
import concurrent.futures
import io
import logging
import os
import random
import sys
from typing import Dict, Tuple

import discord
from discord.ext import commands

from discord_bot.eval_py import eval_py
from discord_bot.stock import get_finviz_map_capture

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)


class MyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.text_reactions = {}  # type: Map[Tuple[str], Tuple[str]]
        self.cached_emojis = {}  # type: Map[str, discord.Emoji]
        self.finviz_cmd_lock = asyncio.Lock()

    def _bot_init(self):
        self._cache_emojis(self.bot)

    def _cache_emojis(self, bot):
        def find_emoji(name):
            return discord.utils.find(lambda x: x.name == name, bot.emojis)

        cache_emoji_names = ["_x", "_v"]
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

        rolled_numbers = [random.randint(1, faces) for x in range(roll_count)]
        result_str = ", ".join(map(str, rolled_numbers))
        await ctx.send(f"{arg} 결과: {result_str}")

    @commands.command()
    async def py(self, ctx, *, arg):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
            future = pool.submit(eval_py, arg)
            try:
                result = future.result(timeout=1.0)
            except concurrent.futures.TimeoutError:
                print("py TimeoutError")
                for pid, process in pool._processes.items():
                    print(f"kill pid: {pid}")
                    process.kill()
                print("pool.shutdown")
                pool.shutdown(wait=True)
                return await ctx.send("TimeoutError")
            return await ctx.send(result)

    @commands.command(aliases=("골라", "뽑아", "뽑기"))
    async def choice(self, ctx, *args):
        if len(args) == 0:
            return
        # await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))
        await ctx.send(random.choice(args))

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
            # await ctx.message.add_reaction('...')
            capture = await get_finviz_map_capture()
            await ctx.send(file=discord.File(io.BytesIO(capture),
                                             filename='finviz.png'))

    @commands.command()
    async def stock_day(self, ctx, arg):
        from discord_bot.stock import get_stock_day_graph_png
        graph_png = await get_stock_day_graph_png(arg)
        await ctx.send(file=discord.File(io.BytesIO(graph_png),
                                         filename='graph.png'))

    @commands.command()
    async def stock_candle(self, ctx, arg):
        from discord_bot.stock import get_stock_candle_graph_png
        graph_png = await get_stock_candle_graph_png(arg)
        await ctx.send(file=discord.File(io.BytesIO(graph_png),
                                         filename='graph.png'))

    @commands.command()
    async def stock(self, ctx, *args):
        if len(args) == 0:
            return
        from discord_bot.stock import get_stock_data

        show_total_infos = False
        if len(args) == 2:
            if args[1] .lower() in ['-f', '--full', 'full', 'f']:
                show_total_infos = True
        query = args[0]

        try:
            stock_data = await get_stock_data(query)
        except NotImplementedError:
            return await ctx.send('준비중')

        embed = discord.Embed(
            title=f'{stock_data.name} ({stock_data.name_eng})',
            description=(
                f'{stock_data.symbol_code} '
                f'({stock_data.stock_exchange_name})\n\n'
                f'**{stock_data.close_price}**\n'
                f'{stock_data.compare_price}  '
                f'{stock_data.compare_ratio}\n----------'),
            colour=discord.Color.blue())
        if show_total_infos:
            for k, v in stock_data.total_infos.items():
                embed.add_field(name=k, value=v)
        else:
            embed.add_field(name='종합 정보',
                            value='두 번째 인자로 `-f`를 추가하세요')
        embed.set_footer(text='powered by NAVER stock')
        embed.set_image(url=stock_data.day_graph_url)
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
                    return await message.channel.send(random.choice(reactions))

    def add_text_reaction(self,
                          comma_separated_keywords: str,
                          reactions: Tuple):
        keywords = tuple(map(str.strip, comma_separated_keywords.split(",")))
        self.text_reactions[keywords] = reactions


def run(token: str):
    bot = commands.Bot(command_prefix="!")
    mybot = MyBot(bot)
    mybot.add_text_reaction(
        "아니야?, 아닌가, 아닐걸, 아닐껄, 아냐?, 아닙니까, 그런가, 아님?, 아닌가요, 아닌가여, 실화냐, 실화입니까, 합니까, 됩니까?, 됩니까",
        ("응 아니야", "응 맞아", "아닐걸", "맞을걸"),
    )
    mybot.add_text_reaction("왜죠", ("저야 모르죠",))
    bot.add_cog(mybot)
    bot.run(token)


def run_cli():
    if len(sys.argv) != 2:
        basename = os.path.basename(sys.argv[0])
        print(f'Usage: {basename} <token>')
        sys.exit(1)
    token = sys.argv[1]
    run(token)
