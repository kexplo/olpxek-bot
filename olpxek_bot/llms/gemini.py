from __future__ import annotations

from typing import AsyncIterator, Iterator

import google.generativeai as genai

from olpxek_bot.utils.llm_provider import Model, SimpleLLMInterface


# gemini 1.0 pro free quotas: 60 QPM(queries per minute)
MODEL_NAME = "models/gemini-1.0-pro-latest"
API_KEY = "<redacted>"


class GeminiLLM(SimpleLLMInterface):
    def __init__(self, api_key: str | None = None):
        if api_key is not None:
            genai.configure(api_key=api_key)
        else:
            genai.configure(api_key=API_KEY)
        self.model = genai.GenerativeModel(MODEL_NAME)

    def completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream: bool = False,
    ) -> str | Iterator[str]:
        gen_config = None
        if max_tokens is not None or temperature is not None or top_p is not None:
            gen_config = genai.GenerationConfig(max_output_tokens=max_tokens, temperature=temperature, top_p=top_p)
        if not stream:
            response = self.model.generate_content(prompt, generation_config=gen_config)
            return response.text
        stream_response = self.model.generate_content(prompt, generation_config=gen_config, stream=True)
        for chunk in stream_response:
            yield chunk.text

    async def async_completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        gen_config = None
        if max_tokens is not None or temperature is not None or top_p is not None:
            gen_config = genai.GenerationConfig(max_output_tokens=max_tokens, temperature=temperature, top_p=top_p)
        if not stream:
            response = await self.model.generate_content_async(prompt, generation_config=gen_config)
            return response.text
        stream_response = await self.model.generate_content_async(prompt, generation_config=gen_config, stream=True)

        async def asynciter_wrapper(resp):
            async for chunk in resp:
                try:
                    yield chunk.text
                except ValueError:
                    # finished
                    if chunk._done:
                        break

        return asynciter_wrapper(stream_response)

    def get_models(self) -> list[Model]:
        return [
            Model(name="gemini-1.0-pro-latest", description="Gemini 1.0 Pro"),
        ]


if __name__ == "__main__":
    async def run():
        llm = GeminiLLM()
        resp = await llm.async_completion("gemini-1.0-pro-latest", "hello world")
        print(resp)

        stream_resp = await llm.async_completion("gemini-1.0-pro-latest", "What is the meaning of life?", stream=True)
        async for chunk in stream_resp:
            print(chunk)
    import asyncio
    asyncio.run(run())
