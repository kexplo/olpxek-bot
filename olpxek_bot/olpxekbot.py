import random
from typing import Dict, Tuple

import discord
from discord.ext import commands
from sentry_sdk import capture_exception


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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        capture_exception(error)

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
