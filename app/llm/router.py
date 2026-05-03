import random
from typing import AsyncGenerator
from app.config import get_settings
from app.llm.adapters import DeepSeekAdapter, QwenAdapter, GLMAdapter, BaseAdapter

settings = get_settings()


class ModelRouter:
    def __init__(self):
        self.adapters: dict[str, BaseAdapter] = {}
        self._init_adapters()

    def _init_adapters(self):
        if settings.DEEPSEEK_API_KEY:
            self.adapters["deepseek"] = DeepSeekAdapter(
                settings.DEEPSEEK_API_KEY, settings.DEEPSEEK_BASE_URL
            )
        if settings.QWEN_API_KEY:
            self.adapters["qwen"] = QwenAdapter(
                settings.QWEN_API_KEY, settings.QWEN_BASE_URL
            )
        if settings.GLM_API_KEY:
            self.adapters["glm"] = GLMAdapter(
                settings.GLM_API_KEY, settings.GLM_BASE_URL
            )

    def _select_adapter(self, model_name: str | None = None) -> BaseAdapter:
        if model_name and model_name in self.adapters:
            return self.adapters[model_name]

        if not self.adapters:
            raise RuntimeError("没有可用的LLM适配器，请配置至少一个API Key")

        return random.choice(list(self.adapters.values()))

    async def chat(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        adapter = self._select_adapter(model)
        return await adapter.chat(
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )

    async def chat_stream(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        adapter = self._select_adapter(model)
        async for chunk in adapter.chat_stream(
            messages=messages,
            temperature=temperature or settings.LLM_TEMPERATURE,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        ):
            yield chunk
