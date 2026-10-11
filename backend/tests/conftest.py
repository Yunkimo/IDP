"""后端测试配置：数据库指向临时目录，注入测试 token。"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(config, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(config, "API_TOKEN", "test-token")
    db.init_db()
    with TestClient(app) as c:
        yield c
