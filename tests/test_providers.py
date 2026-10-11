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


class _TCFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments


class _ToolCall:
    def __init__(self, tool_id, name, arguments):
        self.id = tool_id
        self.type = "function"
        self.function = _TCFunction(name, arguments)


class _Msg:
    def __init__(self, content, tool_calls):
        self.content = content
        self.tool_calls = tool_calls


class _ChoiceMsg:
    def __init__(self, msg):
        self.message = msg


class _RespMsg:
    def __init__(self, msg):
        self.choices = [_ChoiceMsg(msg)]


class _CompletionsMsg:
    def __init__(self, resp):
        self._resp = resp

    def create(self, **kwargs):
        return self._resp


class _FakeClientMsg:
    def __init__(self, resp):
        self.chat = type("Chat", (), {"completions": _CompletionsMsg(resp)})()


def test_chat_with_tools_parses_tool_calls(monkeypatch):
    provider = OpenAICompatProvider("sk", "https://x", "m")
    msg = _Msg("", [_ToolCall("t1", "get_weather", '{"city":"北京"}')])
    monkeypatch.setattr(provider, "_client", _FakeClientMsg(_RespMsg(msg)))

    out = provider.chat_with_tools(
        [{"role": "user", "content": "天气"}],
        [{"type": "function", "function": {"name": "get_weather"}}],
    )

    assert out["content"] == ""
    assert out["tool_calls"] == [
        {
            "id": "t1",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"city":"北京"}'},
        }
    ]
