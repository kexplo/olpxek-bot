import logging

try:
    from olpxek_bot_private_cogs import list_cogs, list_llms
except ImportError:
    def list_cogs():
        return []

    def list_llms():
        return []

import typer

from olpxek_bot.cogs import KarloCog, LLMCog, PyCog, SummarizeYoutubeCog
from olpxek_bot.runner import Runner
from olpxek_bot.utils.llm_provider import LLMProvider

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)


app = typer.Typer()


@app.command()
def run(token: str):
    runner = Runner(command_prefix="!")
    runner.update_text_reactions(
        "아니야?, 아닌가, 아닐걸, 아닐껄, 아냐?, 아닙니까, 그런가, 아님?, 아닌가요, 아닌가여, 실화냐, 실화입니까, 합니까, 됩니까?, 됩니까",  # noqa: E501
        ("응 아니야", "응 맞아", "아닐걸", "맞을걸"),
    )
    runner.update_text_reactions("왜죠", ("저야 모르죠",))

    # register private cog classes
    for cog_cls in list_cogs():
        runner.register_cog_cls(cog_cls)

    llm_provider = LLMProvider()
    # add private llms
    for private_llm in list_llms():
        llm_provider.add_llm(private_llm)

    runner.register_cog(PyCog())
    runner.register_cog(LLMCog())
    runner.register_cog(KarloCog("<redacted>"))
    runner.register_cog(SummarizeYoutubeCog(llm_provider))

    runner.run(token)


if __name__ == "__main__":
    app()
