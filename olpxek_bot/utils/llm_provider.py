from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Iterator, Protocol


@dataclass
class Model:
    name: str
    description: str


class SimpleLLMInterface(Protocol):
    def completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream: bool = False,
    ) -> str | Iterator[str]:
        pass

    async def async_completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        pass

    def get_models(self) -> list[Model]:
        pass


class LLMProvider(SimpleLLMInterface):
    def __init__(self):
        self.llms = {}
        self.models = []

    def add_llm(self, llm: SimpleLLMInterface):
        for model in llm.get_models():
            if model.name in self.llms:
                raise ValueError(f"Model {model.name} already exists")
            self.llms[model.name] = llm
            self.models.append(model)

    def get_llm(self, model_name: str) -> SimpleLLMInterface:
        if model_name not in self.llms:
            raise ValueError(f"Model {model_name} not found")
        return self.llms[model_name]

    def get_models(self) -> list[Model]:
        return self.models

    def completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream: bool = False,
    ) -> str | Iterator[str]:
        llm = self.get_llm(model)
        return llm.completion(model, prompt, max_tokens, temperature, top_p, stream)

    async def async_completion(
        self,
        model: str,
        prompt: str,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        llm = self.get_llm(model)
        return await llm.async_completion(model, prompt, max_tokens, temperature, top_p, stream)
