"""后端配置：从 backend/.env 读取密钥与数据库路径。"""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

# 简单 API Key：桌宠与手机 PWA 通过 X-API-Key 请求头携带，服务端比对
API_TOKEN = os.getenv("API_TOKEN", "").strip()

# SQLite 数据库路径（默认 backend/data/pet.db，已被 git 忽略）
DB_PATH = Path(os.getenv("DB_PATH", str(BACKEND_DIR / "data" / "pet.db")))
