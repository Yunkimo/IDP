"""Settings 配置加载测试。"""

from pet.config import Settings


def test_defaults_when_env_unset(monkeypatch):
    for key in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    s = Settings()
    assert s.llm_base_url == "https://api.deepseek.com"
    assert s.llm_model == "deepseek-chat"
    assert s.llm_api_key == ""


def test_env_override(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_MODEL", "my-model")
    s = Settings()
    assert s.llm_api_key == "sk-test"
    assert s.llm_base_url == "https://example.com/v1"
    assert s.llm_model == "my-model"


def test_config_json_fields():
    s = Settings()
    assert s.pet_name == "小萌"  # 运行时可通过「切换人设」更改
    assert s.image_engine in ("live2d", "sprite")  # 运行时可通过「切换图片」在两种引擎间切换
    assert s.live2d_model == ""
    assert s.whisper_model == "base"
    assert s.tts_voice == "zh-CN-XiaoyouNeural"
    assert s.max_history > 0
