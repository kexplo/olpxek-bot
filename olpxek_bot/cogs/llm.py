import asyncio
import json

import aiohttp
from discord.ext import commands
from rich import print


async def request_llama_stream(prompt: str):
    # LLaMA Prompt:
    # full_prompt = "Below is an instruction that describes a task. Write a response that appropriately completes the request.\n"  # noqa: E501
    # full_prompt += f"### Instructions: \n{prompt}\n\n### Response: \n"
    # 42dot LLM Prompt:
    full_prompt = "호기심 많은 인간 (human)과 인공지능 봇 (AI bot)의 대화입니다. 봇은 인간의 질문에 대해 친절하게 유용하고 상세한 답변을 제공합니다. "  # noqa: E501
    full_prompt += f"<human>: {prompt} <bot>:"

    final_response_text = ""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://146.56.128.82:8000/v1/completions",
            json={"prompt": full_prompt, "max_tokens": 1024, "stream": True},
            timeout=60 * 10,
        ) as resp:
            async for data, end_of_http_chunk in resp.content.iter_chunks():
                buffer = data.decode().strip()
                # ignore other responses like ping
                if not buffer.startswith("data: "):
                    continue
                data_string = buffer.removeprefix("data: ")
                if data_string == '[DONE]':
                    return
                try:
                    choice = json.loads(data_string)["choices"][0]
                except json.JSONDecodeError as e:
                    print(f"failed to decode json: {data_string}")
                    raise e
                if choice["finish_reason"] == "stop":
                    return
                final_response_text += choice["text"]
                yield final_response_text


class LLMCog(commands.Cog):
    def __init__(self):
        self.llama_cmd_lock = asyncio.Lock()

    @commands.command(aliases=("알파카", "alpaca", "llama"))
    async def llm(self, ctx, *, arg):
        print(f"LLM request: {arg}")
        async with self.llama_cmd_lock:
            await ctx.message.add_reaction("💬")
            message = await ctx.reply("💬..")
            try:
                async for content in request_llama_stream(arg):
                    if len(content.strip()) > 0:
                        await message.edit(content=content)
            except Exception as e:
                await ctx.message.add_reaction("❌")
                print(e)
                prev_content = message.content
                if prev_content:
                    new_content = prev_content + "\n---\n" + str(e)
                else:
                    new_content = str(e)
                await message.edit(content=new_content)
                return
            await ctx.message.add_reaction("✅")
            return


if __name__ == "__main__":
    async def test_main():
        async for content in request_llama_stream("대한민국의 수도는?"):
            print(content)
    asyncio.run(test_main())
