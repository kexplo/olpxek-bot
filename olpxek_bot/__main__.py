import typer

from olpxek_bot.runner import Runner

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
    runner.add_private_cogs()
    runner.add_pycog()
    runner.add_llmcog()
    runner.add_karlocog("<redacted>")
    runner.run(token)


if __name__ == "__main__":
    app()
