"""形象抽象层（策略模式）。

PetWindow 只依赖 Avatar 接口，不关心底层用「图片精灵」还是「Live2D 渲染」，
从而能在 config.json 里一键切换，也便于日后扩展新引擎（如 Spine、视频形象）。
"""

from abc import ABC, abstractmethod
from pathlib import Path

from PyQt6.QtWidgets import QWidget

from .sprite import PetSprite


class Avatar(ABC):
    """形象引擎抽象基类：对外暴露统一接口，隐藏渲染实现差异。"""

    supports_motion: bool = False  # 是否支持动作 / 表情交互
    expressions: list[str] = []  # 可选表情名列表

    def __init__(self, parent: QWidget | None = None) -> None:
        self.widget: QWidget = self._build(parent)

    @abstractmethod
    def _build(self, parent: QWidget | None) -> QWidget:
        """构造底层控件（策略的具体实现）。"""

    @abstractmethod
    def react(self, event: str) -> None:
        """对外部事件做出动作（如 speak / poke）。"""

    def set_appearance(self, path: Path, size: int) -> None:
        """运行时更换形象；仅支持换图的引擎覆写。"""

    def clear(self) -> None:
        """释放当前形象占用的资源（图片文件句柄等）；无资源需释放的引擎保持空实现。"""

    def set_expression(self, name: str) -> None:
        """切换表情；仅 Live2D 覆写。"""

    def reset_expression(self) -> None:
        """复位表情到默认；仅 Live2D 覆写。"""

    def tap(self, pos, on_miss=None) -> None:
        """点击形象：Live2D 命中脸则换表情，未命中回调 on_miss；静态形象直接回调。"""
        if on_miss is not None:
            on_miss()


class SpriteAvatar(Avatar):
    """图片 / 动图精灵引擎（QLabel + QPixmap / QMovie）。"""

    def __init__(
        self, assets_dir: Path, frames: list[str], size: int, parent: QWidget | None = None
    ) -> None:
        self._assets_dir = assets_dir
        self._frames = frames
        self._size = size
        super().__init__(parent)

    def _build(self, parent: QWidget | None) -> QWidget:
        return PetSprite(self._assets_dir, self._frames, self._size, parent=parent)

    def react(self, event: str) -> None:
        return  # 静态精灵暂无对应动作

    def set_appearance(self, path: Path, size: int) -> None:
        self._size = size
        self.widget.set_image(path, size)  # type: ignore[attr-defined]

    def clear(self) -> None:
        self.widget.clear()  # type: ignore[attr-defined]


class Live2DAvatar(Avatar):
    """Live2D 渲染引擎（透明 WebView + pixi-live2d-display）。"""

    supports_motion = True

    def __init__(
        self,
        model_name: str = "",
        width: int = 360,
        height: int = 360,
        parent: QWidget | None = None,
    ) -> None:
        self._model_name = model_name
        self._width = width
        self._height = height
        super().__init__(parent)

    @property
    def expressions(self) -> list[str]:
        """表情名从模型元数据动态发现，覆盖基类默认空列表。"""
        return getattr(self.widget, "expressions", [])

    def _build(self, parent: QWidget | None) -> QWidget:
        # 延迟导入：PyQt6-WebEngine 是可选依赖，缺失时不拖累精灵引擎
        from .live2d_view import Live2DView

        return Live2DView(self._width, self._height, parent=parent, model_name=self._model_name)

    def react(self, event: str) -> None:
        view = self.widget
        if event in ("speak", "poke"):
            view.play_motion()  # type: ignore[attr-defined]
        elif event == "voice":
            view.random_expression()  # type: ignore[attr-defined]

    def set_expression(self, name: str) -> None:
        self.widget.set_expression(name)  # type: ignore[attr-defined]

    def reset_expression(self) -> None:
        self.widget.reset_expression()  # type: ignore[attr-defined]

    def tap(self, pos, on_miss=None) -> None:
        # 窗口坐标 → WebView 坐标，交给前端做命中测试（点脸换表情）
        view = self.widget
        local = view.mapFromParent(pos)
        view.tap_at(local.x(), local.y(), on_miss)  # type: ignore[attr-defined]


def create_avatar(settings, parent: QWidget | None = None) -> Avatar:
    """根据配置构造形象引擎；Live2D 不可用时自动回退到图片精灵。"""
    if getattr(settings, "image_engine", "sprite") == "live2d":
        try:
            return Live2DAvatar(
                getattr(settings, "live2d_model", ""),
                settings.live2d_width,
                settings.live2d_height,
                parent=parent,
            )
        except Exception as exc:  # WebEngine 未安装 / 加载失败等
            print(f"[avatar] Live2D 不可用，回退到图片精灵：{exc}")
    return SpriteAvatar(settings.assets_dir, settings.frames, settings.sprite_size, parent=parent)
