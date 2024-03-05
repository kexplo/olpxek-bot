import asyncio

from discord.ext import commands
from openai import AsyncOpenAI
from rich import print


client = AsyncOpenAI(
    api_key="dummy",
    base_url="http://146.56.128.82:9997/v1",
)


async def request_chat_stream(prompt: str):
    # LLaMA Prompt:
    # full_prompt = "Below is an instruction that describes a task. Write a response that appropriately completes the request.\n"  # noqa: E501
    # full_prompt += f"### Instructions: \n{prompt}\n\n### Response: \n"
    # 42dot LLM Prompt:
    # full_prompt = "호기심 많은 인간 (human)과 인공지능 봇 (AI bot)의 대화입니다. 봇은 인간의 질문에 대해 친절하게 유용하고 상세한 답변을 제공합니다. "  # noqa: E501
    # full_prompt += f"<human>: {prompt} <bot>:"

    final_response_text = ""
    stream = await client.chat.completions.create(
        model="gemma-2b-it-gguf",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    async for chunk in stream:
        chunk_text = chunk.choices[0].delta.content or ""
        if chunk_text:
            final_response_text += chunk_text
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
            content = ""

            async def recv_llama_stream(prompt: str):
                nonlocal content
                async for content in request_chat_stream(arg):
                    # request_chat_stream returns accumulated content
                    content = content

            try:
                task = asyncio.create_task(recv_llama_stream(arg))
                prev_content = ""
                while not task.done():
                    if not content.strip():
                        await asyncio.sleep(0.1)
                        continue
                    if prev_content == content:
                        # content not changed
                        await asyncio.sleep(0.1)
                        continue
                    prev_content = content
                    await message.edit(content=content)
                    await asyncio.sleep(1)  # prevent rate limit
                task.result()  # raise exception if any
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
        async for content in request_chat_stream("대한민국의 수도는?"):
            print(content)

    asyncio.run(test_main())
