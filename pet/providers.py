"""LLM 提供者抽象：策略模式（Strategy）+ 工厂方法（Factory Method）。

把「调用哪家 LLM」抽象成策略，便于在不改上层代码的前提下切换
DeepSeek / 通义 / 智谱 / Moonshot 等任意 OpenAI 兼容服务。
"""

from abc import ABC, abstractmethod

from openai import OpenAI

from .config import Settings


class ChatProvider(ABC):
    """LLM 对话提供者接口（策略）。"""

    @abstractmethod
    def stream_chat(self, messages: list[dict], on_chunk=None) -> str:
        """流式对话。on_chunk(str) 每收到一个增量被调用；返回完整文本。"""


class OpenAICompatProvider(ChatProvider):
    """OpenAI 兼容协议实现（DeepSeek 等）。客户端惰性创建，避免未配密钥时启动即报错。"""

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    def stream_chat(self, messages: list[dict], on_chunk=None) -> str:
        stream = self._get_client().chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.9,
            max_tokens=1024,
        )
        parts: list[str] = []
        for chunk in stream:
            if not chunk.choices:
                continue
            content = getattr(chunk.choices[0].delta, "content", None)
            if content:
                parts.append(content)
                if on_chunk is not None:
                    on_chunk(content)
        return "".join(parts)


def create_chat_provider(settings: Settings) -> ChatProvider:
    """工厂方法：根据配置创建对话提供者。"""
    return OpenAICompatProvider(
        settings.llm_api_key,
        settings.llm_base_url,
        settings.llm_model,
    )
