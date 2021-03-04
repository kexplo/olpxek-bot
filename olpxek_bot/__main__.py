import os
import sys

from discord.ext import commands

from olpxek_bot.olpxekbot import OlpxekBot

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)


def run(token: str):
    bot = commands.Bot(command_prefix="!")
    mybot = OlpxekBot(bot)
    mybot.update_text_reactions(
        "아니야?, 아닌가, 아닐걸, 아닐껄, 아냐?, 아닙니까, 그런가, 아님?, 아닌가요, 아닌가여, 실화냐, 실화입니까, 합니까, 됩니까?, 됩니까",  # noqa: E501
        ("응 아니야", "응 맞아", "아닐걸", "맞을걸"),
    )
    mybot.update_text_reactions("왜죠", ("저야 모르죠",))
    bot.add_cog(mybot)
    bot.run(token)


def run_cli():
    if len(sys.argv) != 2:
        basename = os.path.basename(sys.argv[0])
        print(f"Usage: {basename} <token>")
        sys.exit(1)
    token = sys.argv[1]
    run(token)
