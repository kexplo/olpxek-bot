from typing import Optional, Tuple

from discord.ext import commands
import sentry_sdk

from olpxek_bot.cogs import FinanceCog, PyCog
from olpxek_bot.config import ConfigLoader, DefaultConfig
from olpxek_bot.olpxekbot import OlpxekBot


_default_help_cmd = commands.DefaultHelpCommand()
_default_config_loader = ConfigLoader()


class Runner:
    def __init__(
        self,
        command_prefix: str = "!",
        help_command: Optional[commands.HelpCommand] = _default_help_cmd,
        config_loader: ConfigLoader = _default_config_loader,
    ):
        self.try_load_config(config_loader)
        self.setup_sentry()
        self.discord_bot = commands.Bot(
            command_prefix=command_prefix, help_command=help_command
        )
        self.olpxekbot = OlpxekBot(self.discord_bot)
        # add built-in cogs
        self.discord_bot.add_cog(self.olpxekbot)
        self.discord_bot.add_cog(FinanceCog(self.config))
        self._pycog: Optional[PyCog] = None

    def try_load_config(self, config_loader: ConfigLoader):
        try:
            config = config_loader.load_config()
        except FileNotFoundError:
            config = config_loader.default_config()
        self.config: DefaultConfig = config

    def setup_sentry(self, dsn: Optional[str] = None):
        _dsn = None
        if dsn is not None:
            _dsn = dsn
        elif self.config.sentry is not None:
            _dsn = self.config.sentry.dsn
        if _dsn is not None:
            sentry_sdk.init(_dsn, traces_sample_rate=1.0)

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
