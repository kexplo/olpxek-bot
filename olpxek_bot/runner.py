import asyncio
from typing import Optional, Tuple

import discord
from discord.ext import commands
from olpxek_bot_private_cogs import list_cogs
import sentry_sdk

from olpxek_bot.cogs import FinanceCog
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

        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        intents.dm_messages = True
        intents.emojis_and_stickers = True
        intents.reactions = True
        intents.guild_messages = True
        intents.guild_reactions = True

        self.discord_bot = commands.Bot(intents=intents, command_prefix=command_prefix, help_command=help_command)
        self.bot_initizalized = False

        self.olpxekbot = OlpxekBot(self.discord_bot)
        # add built-in cogs
        self._cogs = [
            self.olpxekbot,
            FinanceCog(self.config),
        ]

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

    def update_text_reactions(self, comma_separated_keywords: str, reactions: Tuple[str, ...]):
        self.olpxekbot.update_text_reactions(comma_separated_keywords, reactions)

    def register_cog(self, cog: commands.Cog):
        if self.bot_initizalized:
            raise RuntimeError("Cannot register cog after bot is initialized")
        self._cogs.append(cog)

    def register_private_cogs(self):
        for cog_cls in list_cogs():
            self.register_cog(cog_cls(self.discord_bot))

    def run(self, token: str):
        asyncio.run(self._main(token))

    async def _main(self, token: str):
        if not self.bot_initizalized:
            self.bot_initizalized = True
            for cog in self._cogs:
                await self.discord_bot.add_cog(cog)

        async with self.discord_bot:
            await self.discord_bot.start(token)
