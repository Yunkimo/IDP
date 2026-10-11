"""Live2D 模型发现测试（纯文件系统逻辑，无需启动 WebEngine）。"""

import pytest

live2d_view = pytest.importorskip("pet.live2d_view")


def test_discover_models_without_bundled_model():
    """基线不内置任何模型，discover_models 应返回空列表（模型由用户自行导入）。"""
    assert live2d_view.discover_models() == []


def test_model_entry_missing_returns_none():
    assert live2d_view.model_entry("不存在的模型目录") is None
