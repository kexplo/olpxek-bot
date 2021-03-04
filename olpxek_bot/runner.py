from typing import Optional, Tuple

from discord.ext import commands

from olpxek_bot.cogs import PyCog
from olpxek_bot.olpxekbot import OlpxekBot


_default_help_cmd = commands.DefaultHelpCommand()


class Runner:
    def __init__(
        self,
        command_prefix: str = "!",
        help_command: Optional[commands.HelpCommand] = _default_help_cmd,
    ):
        self.discord_bot = commands.Bot(
            command_prefix=command_prefix, help_command=help_command
        )
        self.olpxekbot = OlpxekBot(self.discord_bot)
        self.discord_bot.add_cog(self.olpxekbot)
        self._pycog: Optional[PyCog] = None

    def update_text_reactions(
        self, comma_separated_keywords: str, reactions: Tuple[str, ...]
    ):
        self.olpxekbot.update_text_reactions(
            comma_separated_keywords, reactions
        )

    def add_cog(self, cog: commands.Cog):
        self.discord_bot.add_cog(cog)

    def add_pycog(self):
        if self._pycog is None:
            self._pycog = PyCog()
            self.discord_bot.add_cog(self._pycog)

    def run(self, token: str):
        self.discord_bot.run(token)
