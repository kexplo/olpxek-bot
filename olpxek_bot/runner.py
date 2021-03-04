from typing import Tuple

from discord.ext import commands

from olpxek_bot.olpxekbot import OlpxekBot


class Runner:
    def __init__(self, command_prefix: str = "!"):
        self.discord_bot = commands.Bot(command_prefix=command_prefix)
        self.olpxekbot = OlpxekBot(self.discord_bot)
        self.discord_bot.add_cog(self.olpxekbot)

    def update_text_reactions(
        self, comma_separated_keywords: str, reactions: Tuple[str, ...]
    ):
        self.olpxekbot.update_text_reactions(
            comma_separated_keywords, reactions
        )

    def add_cog(self, cog: commands.Cog):
        self.discord_bot.add_cog(cog)

    def run(self, token: str):
        self.discord_bot.run(token)
