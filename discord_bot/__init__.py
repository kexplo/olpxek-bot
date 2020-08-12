import asyncio
import concurrent.futures
import logging
import os
import random
import sys
from typing import Tuple

import discord
from discord import Emoji
from discord.ext import commands

from discord_bot.eval_py import eval_py

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)


class MyBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.text_reactions = {}  # type: Map[Tuple[str], Tuple[str]]
        self.cached_emojis = {}  # type: Map[str, discord.Emoji]

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

    @commands.command(aliases=("골라",))
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
