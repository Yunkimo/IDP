"""视觉识别层测试：纯函数（data URL / 消息构造 / JSON 提取）与解析流程（mock 上游）。"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from app import config, vision


def test_to_data_url_roundtrip():
    data_url = vision.to_data_url(b"fake-image", "image/jpeg")
    assert data_url.startswith("data:image/jpeg;base64,")
    import base64

    assert base64.b64decode(data_url.split(",", 1)[1]) == b"fake-image"


def test_build_messages_structure():
    messages = vision.build_messages(b"fake-image", "image/jpeg")
    assert messages[0] == {"role": "system", "content": vision.VISION_SYSTEM_PROMPT}
    user_content = messages[1]["content"]
    assert user_content[0]["type"] == "image_url"
    assert user_content[0]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert user_content[1]["type"] == "text"


def test_extract_json_array_plain():
    assert vision.extract_json_array('[{"a": 1}]') == [{"a": 1}]


def test_extract_json_array_code_fence():
    text = '```json\n[{"a": 1}]\n```'
    assert vision.extract_json_array(text) == [{"a": 1}]


def test_extract_json_array_prose_around():
    text = '识别结果如下：[{"a": 1}, {"b": 2}] 以上。'
    assert vision.extract_json_array(text) == [{"a": 1}, {"b": 2}]


def test_extract_json_array_invalid_json_raises():
    with pytest.raises(vision.VisionError):
        vision.extract_json_array("[{broken json]")


def test_extract_json_array_empty_raises():
    with pytest.raises(vision.VisionError):
        vision.extract_json_array("")


def test_extract_json_array_object_wrapped():
    # 模型偶尔把数组包在对象里（如 {"courses": [...]}），宽容提取内层数组
    assert vision.extract_json_array('{"courses": [{"a": 1}]}') == [{"a": 1}]


def test_extract_json_array_non_list_raises():
    with pytest.raises(vision.VisionError):
        vision.extract_json_array('{"courses": 3}')


def test_parse_image_unconfigured_raises(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setattr(config, "LLM_VISION_MODEL", "Qwen/Qwen2.5-VL-32B-Instruct")

    async def scenario():
        mocked = AsyncMock()
        monkeypatch.setattr(vision, "_call_vision", mocked)
        with pytest.raises(vision.VisionNotConfigured):
            await vision.parse_schedule_image(b"img", "image/jpeg")
        mocked.assert_not_awaited()

    asyncio.run(scenario())


def test_parse_image_normalizes_and_drops_invalid(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setattr(config, "LLM_VISION_MODEL", "Qwen/Qwen2.5-VL-32B-Instruct")

    async def scenario():
        monkeypatch.setattr(
            vision,
            "_call_vision",
            AsyncMock(
                return_value=(
                    '[{"name":"数学","day_of_week":"3","start_time":"8:00","end_time":"9:40",'
                    '"location":"A101","weeks":"1-16"},{"name":null,"day_of_week":9}]'
                )
            ),
        )
        result = await vision.parse_schedule_image(b"img", "image/jpeg")
        assert result["skipped"] == 1
        assert len(result["courses"]) == 1
        course = result["courses"][0]
        assert course["name"] == "数学"
        assert course["day_of_week"] == 3
        assert course["start_time"] == "08:00"
        assert course["end_time"] == "09:40"
        assert course["location"] == "A101"
        assert course["weeks"] == list(range(1, 17))

    asyncio.run(scenario())


def test_parse_image_mime_fallback(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setattr(config, "LLM_VISION_MODEL", "Qwen/Qwen2.5-VL-32B-Instruct")
    mocked = AsyncMock(
        return_value='[{"name":"课","day_of_week":1,"start_time":"08:00","end_time":"09:00"}]'
    )

    async def scenario():
        monkeypatch.setattr(vision, "_call_vision", mocked)
        await vision.parse_schedule_image(b"img", "")
        assert mocked.await_args.args[1] == "image/jpeg"

    asyncio.run(scenario())


def test_parse_image_timeout_propagates(monkeypatch):
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    monkeypatch.setattr(config, "LLM_VISION_MODEL", "Qwen/Qwen2.5-VL-32B-Instruct")
    mocked = AsyncMock(side_effect=vision.VisionTimeout("视觉模型响应超时"))

    async def scenario():
        monkeypatch.setattr(vision, "_call_vision", mocked)
        with pytest.raises(vision.VisionTimeout):
            await vision.parse_schedule_image(b"img", "image/jpeg")

    asyncio.run(scenario())
