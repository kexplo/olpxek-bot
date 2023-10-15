import base64
import io

import aiohttp
import discord
from discord.ext import commands


class KarloCog(commands.Cog):
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def request_karlo(self, prompt: str, negative_prompt: str = ""):
        headers = {
            "Authorization": f"KakaoAK {self._api_key}",
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            payload = {
                "prompt": prompt,
                "image_format": "png",
                "return_type": "base64_string",  # url or base64_string
            }
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt

            async with session.post(
                "https://api.kakaobrain.com/v2/inference/karlo/t2i",
                json=payload,
                timeout=60 * 10,
            ) as resp:
                # text_content = await resp.text()
                # print(text_content)  # for debug
                json_content = await resp.json()
                base64_image = json_content["images"][0]["image"]
                yield base64_image

    @commands.command(aliases=("칼로",))
    async def karlo(self, ctx, *, arg):
        print(f"karlo request: {arg}")
        await ctx.message.add_reaction("💬")
        # message = await ctx.reply("💬..")
        try:
            prompt, _, negative_prompt = arg.partition("|")
            async for base64_image in self.request_karlo(prompt.strip(), negative_prompt.strip()):
                # discord message.edit does not support file
                await ctx.reply(
                    file=discord.File(
                        io.BytesIO(base64.b64decode(base64_image)),
                        filename="result.png",
                    ),
                    content=f"{prompt=} {negative_prompt=}",
                )
        except Exception as e:
            await ctx.message.add_reaction("❌")
            print(e)
            new_content = str(e)
            await ctx.reply(content=new_content)
            return
        await ctx.message.add_reaction("✅")
        return
