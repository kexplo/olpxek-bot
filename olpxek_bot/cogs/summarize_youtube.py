from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from olpxek_bot.utils.llm_provider import SimpleLLMInterface
from olpxek_bot.utils.youtube_summarizer import YoutubeSummarizer


class SummarizeYoutubeCog(commands.Cog):
    def __init__(self, llm: SimpleLLMInterface):
        self.llm = llm
        self.youtube_summarizer = YoutubeSummarizer()

    @app_commands.command(name="summarize_youtube", description="summarize a youtube video")
    @app_commands.describe(model="summarization model to use")
    async def summarize_youtube(self, interaction: discord.Interaction, url: str, model: str):
        await interaction.response.defer(thinking=True)
        try:
            summary = await self.youtube_summarizer.async_summarize(url, self.llm, model)
            summary = cast(str, summary)  # to fix type error
        except Exception as e:
            await interaction.followup.send(f"failed with error: {e}")
            return
        await interaction.followup.send(summary)

    @summarize_youtube.autocomplete("model")
    async def models_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=m.description, value=m.name) for m in self.llm.get_models()]
