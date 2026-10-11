"""提供者（策略）与 LLM 客户端（门面）测试，使用 mock 隔离网络。"""

import pytest

from pet.llm import LLMClient, LLMError
from pet.providers import OpenAICompatProvider, create_chat_provider


class _Delta:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.delta = _Delta(content)


class _Chunk:
    def __init__(self, content):
        self.choices = [_Choice(content)] if content is not None else []


class _Completions:
    def __init__(self, chunks):
        self._chunks = chunks

    def create(self, **kwargs):
        return iter(self._chunks)


class _FakeClient:
    def __init__(self, chunks):
        self.chat = type("Chat", (), {"completions": _Completions(chunks)})()


def test_stream_chat_concatenates_and_callbacks(monkeypatch):
    provider = OpenAICompatProvider("sk", "https://x", "m")
    chunks = [_Chunk("你"), _Chunk(None), _Chunk("好")]
    monkeypatch.setattr(provider, "_client", _FakeClient(chunks))

    collected = []
    result = provider.stream_chat([{"role": "user", "content": "hi"}], on_chunk=collected.append)

    assert result == "你好"
    assert collected == ["你", "好"]


def test_llm_client_wraps_error():
    class _Boom:
        def stream_chat(self, messages, on_chunk=None):
            raise RuntimeError("boom")

    client = LLMClient(_Boom())
    with pytest.raises(LLMError):
        client.chat([{"role": "user", "content": "hi"}])


def test_factory_returns_openai_compat_provider():
    from pet.config import Settings

    provider = create_chat_provider(Settings())
    assert isinstance(provider, OpenAICompatProvider)
