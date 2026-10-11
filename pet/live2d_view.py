"""Live2D 形象视图：透明 QWebEngineView，通用渲染任意 Cubism 4 模型。

模型以「目录」为单位放在 assets/live2d/ 下，每个目录含一个入口 json
（*.model3.json 或旧版 *.model.json）。入口路径、动作组、表情名都从模型
自身动态发现，不再硬编码具体模型，从而支持导入与切换任意 Live2D 模型。
"""

import json
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, QUrlQuery
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QWidget

from .paths import app_dir
from .webenv import enable_local_file_access  # noqa: F401  # 导出供外部复用

__all__ = ["Live2DView", "discover_models", "find_model_entry", "enable_local_file_access"]

LIVE2D_DIR = app_dir() / "assets" / "live2d"


def find_model_entry(folder: Path) -> Path | None:
    """在模型目录里找 Cubism 入口 json（*.model3.json 或 *.model.json），找不到返回 None。"""
    for pattern in ("*.model3.json", "*.model.json"):
        hits = sorted(folder.glob(pattern))
        if hits:
            return hits[0]
    return None


def _read_expressions(entry: Path) -> list[str]:
    """从模型入口 json 里读取表情名列表。"""
    try:
        data = json.loads(entry.read_text(encoding="utf-8"))
    except Exception:
        return []
    exprs = data.get("FileReferences", {}).get("Expressions", [])
    return [e.get("Name", "") for e in exprs if isinstance(e, dict) and e.get("Name")]


def discover_models() -> list[dict]:
    """扫描 assets/live2d/，返回可用模型列表，每项 {name, entry, expressions}。"""
    models = []
    if not LIVE2D_DIR.is_dir():
        return models
    for child in sorted(LIVE2D_DIR.iterdir()):
        if not child.is_dir():
            continue
        entry = find_model_entry(child)
        if entry is not None:
            models.append(
                {
                    "name": child.name,
                    "entry": f"{child.name}/{entry.name}",
                    "expressions": _read_expressions(entry),
                }
            )
    return models


def model_entry(name: str) -> str | None:
    """返回模型入口的相对路径（目录/入口.json），不存在则返回 None。"""
    entry = find_model_entry(LIVE2D_DIR / name)
    if entry is None:
        return None
    return f"{name}/{entry.name}"


class Live2DView(QWebEngineView):
    """加载并渲染 assets/live2d/index.html 的透明 WebView，模型由 model_name 指定。"""

    def __init__(
        self, width: int = 360, height: int = 480, parent=None, *, model_name: str = ""
    ) -> None:
        super().__init__(parent)
        self.model_name = model_name
        self.expressions: list[str] = self._load_expressions()

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        self.resize(width, height)
        self.setMinimumSize(width, height)

        page = self.page()
        page.setBackgroundColor(Qt.GlobalColor.transparent)
        page.settings().setAttribute(page.settings().WebAttribute.ShowScrollBars, False)

        # 桌面宠物需由父窗口接管鼠标（拖拽/点击），故让 WebView 对鼠标事件穿透
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.loadFinished.connect(self._make_click_through)

        entry = model_entry(model_name) or ""
        url = QUrl.fromLocalFile(str(LIVE2D_DIR / "index.html"))
        query = QUrlQuery()
        query.addQueryItem("entry", entry)
        url.setQuery(query)
        self.load(url)

    def _load_expressions(self) -> list[str]:
        entry = find_model_entry(LIVE2D_DIR / self.model_name)
        if entry is None:
            return []
        return _read_expressions(entry)

    def _make_click_through(self, _ok: bool) -> None:
        """页面加载后，对内部 Chromium 子控件同样设置穿透（子控件是延迟创建的）。"""
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        for child in self.findChildren(QWidget):
            child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

    # —— 供上层控制的桥接 ——
    def play_motion(self, group: str | None = None) -> None:
        """播放指定动作组内的随机动作；group 为空时播放一个随机动作。"""
        g = json.dumps(group) if group else "null"
        self.page().runJavaScript(f"window.live2d && window.live2d.motion({g})")

    def set_expression(self, name: str) -> None:
        self.page().runJavaScript(f"window.live2d && window.live2d.expression({name!r})")

    def reset_expression(self) -> None:
        """复位表情到默认（清除「疑惑」等，用于成功回复后恢复正常神态）。"""
        self.page().runJavaScript("window.live2d && window.live2d.resetExpression()")

    def tap_at(self, x: int, y: int, on_miss=None) -> None:
        """点脸检测：把点击坐标交给前端做命中测试，命中则换表情，未命中回调 on_miss。"""

        def _handle(result) -> None:
            hit = result is True or str(result).lower() == "true"
            if not hit and on_miss is not None:
                on_miss()

        self.page().runJavaScript(f"window.live2d ? window.live2d.tapAt({x}, {y}) : false", _handle)

    def random_expression(self) -> None:
        """随机换一个表情（语音输入时的反应）。"""
        self.page().runJavaScript("window.live2d && window.live2d.randomExpression()")
