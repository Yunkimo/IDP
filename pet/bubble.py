"""语音气泡：圆角矩形 + 小尾巴，支持流式打字机显示与自动收起。"""

from PyQt6.QtCore import QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

_PADDING = 12
_TAIL_H = 8


def wrap_text(text: str, max_width: int, measure) -> list[str]:
    """按字符折行（适配中文无空格）。measure(str)->int 返回像素宽度。

    拆成纯函数便于单元测试。
    """
    lines: list[str] = []
    cur = ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        if cur and measure(cur + ch) > max_width:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    lines.append(cur)
    return lines or [""]


class SpeechBubble(QWidget):
    resized = pyqtSignal()

    def __init__(self, timeout_ms: int = 8000, max_width: int = 240, parent=None) -> None:
        super().__init__(parent)
        self.timeout_ms = timeout_ms
        self.max_width = max_width
        self._text = ""

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

        self.hide()

    def set_text(self, text: str) -> None:
        self._text = text
        self._apply_text()

    def append_chunk(self, chunk: str) -> None:
        self._text += chunk
        self._apply_text()

    def clear(self) -> None:
        self._text = ""
        self.update()

    def _apply_text(self) -> None:
        self._resize_to_text()
        self.show()
        self.update()
        if self.timeout_ms > 0:
            self._timer.start(self.timeout_ms)

    def _wrap(self) -> list[str]:
        return wrap_text(self._text, self.max_width, self.fontMetrics().horizontalAdvance)

    def _resize_to_text(self) -> None:
        lines = self._wrap()
        fm = self.fontMetrics()
        line_h = fm.lineSpacing()
        text_w = max((fm.horizontalAdvance(line) for line in lines), default=0)
        w = int(min(self.max_width, text_w) + _PADDING * 2)
        h = int(line_h * len(lines) + _PADDING * 2 + _TAIL_H)
        self.resize(w, h)
        self.resized.emit()

    def paintEvent(self, event) -> None:  # noqa: N802
        if not self._text:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        body_h = h - _TAIL_H

        p.setPen(QPen(QColor(0, 0, 0, 60), 1))
        p.setBrush(QColor(255, 255, 255, 238))
        p.drawRoundedRect(QRectF(0, 0, w, body_h), 12, 12)

        cx = w / 2
        tail = QPainterPath()
        tail.moveTo(cx - 8, body_h)
        tail.lineTo(cx, h)
        tail.lineTo(cx + 8, body_h)
        tail.closeSubpath()
        p.drawPath(tail)

        p.setPen(QColor(45, 45, 45))
        fm = self.fontMetrics()
        y = _PADDING + fm.ascent()
        for line in self._wrap():
            p.drawText(_PADDING, y, line)
            y += fm.lineSpacing()
        p.end()
