"""后端配置：从 backend/.env 读取密钥与数据库路径。"""

import math
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# 简单 API Key：桌宠与手机 PWA 通过 X-API-Key 请求头携带，服务端比对
API_TOKEN = os.getenv("API_TOKEN", "").strip()

# 视觉模型（课表图片识别导入）：OpenAI 兼容 vision API（如硅基流动 Qwen2.5-VL）
LLM_API_KEY = os.getenv("LLM_API_KEY", "").strip()
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip()
LLM_VISION_MODEL = os.getenv("LLM_VISION_MODEL", "").strip()

# SQLite 数据库路径（默认 backend/data/pet.db，已被 git 忽略）
DB_PATH = Path(os.getenv("DB_PATH", str(BACKEND_DIR / "data" / "pet.db")))


def positive_seconds(name: str, default: str) -> float:
    """读取正有限秒数，配置错误时明确拒绝启动。"""
    try:
        value = float(os.getenv(name, default))
    except ValueError as exc:
        raise ValueError(f"{name} 必须是正有限秒数") from exc
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} 必须是正有限秒数")
    return value


WS_SEND_TIMEOUT_SECONDS = positive_seconds("WS_SEND_TIMEOUT_SECONDS", "2")
WS_CLOSE_TIMEOUT_SECONDS = positive_seconds("WS_CLOSE_TIMEOUT_SECONDS", "1")
