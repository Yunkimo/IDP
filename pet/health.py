"""健康关怀：定时检测系统空闲时长，久坐后提醒喝水/休息。

Windows 用 GetLastInputInfo 读取键盘鼠标的「最后输入时刻」；其它平台无该 API，
空闲时长恒为 0（即不触发提醒），保证跨平台不崩。
"""

import ctypes

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

_CHECK_INTERVAL_MS = 15_000  # 每 15 秒检测一次空闲时长
_ACTIVE_RESET_SECS = 5.0  # 空闲低于该值视为「用户已回来」，重置提醒标记


class _IdleTimer:
    """读取系统空闲时长（秒）。"""

    def __init__(self) -> None:
        self._get_last_input = None
        self._get_tick = None
        if not hasattr(ctypes, "windll"):
            return
        try:
            self._get_last_input = ctypes.windll.user32.GetLastInputInfo
            self._get_tick = ctypes.windll.kernel32.GetTickCount
        except Exception:
            self._get_last_input = None
            self._get_tick = None

    def idle_seconds(self) -> float:
        if self._get_last_input is None or self._get_tick is None:
            return 0.0

        class _LastInputInfo(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

        info = _LastInputInfo()
        info.cbSize = ctypes.sizeof(_LastInputInfo)
        if not self._get_last_input(ctypes.byref(info)):
            return 0.0
        elapsed_ms = self._get_tick() - info.dwTime
        return max(0.0, elapsed_ms / 1000.0)


class HealthMonitor(QObject):
    """用 QTimer 周期性检测久坐，超过阈值发出提醒信号。"""

    water_due = pyqtSignal()
    rest_due = pyqtSignal()

    def __init__(self, settings, idle_source=None, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._idle = idle_source or _IdleTimer()
        self._water_reminded = False
        self._rest_reminded = False

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)

    def start(self) -> None:
        """按配置启用；health_enabled 关闭时不启动定时器。"""
        if not self._settings.health_enabled:
            return
        self._timer.start(_CHECK_INTERVAL_MS)

    def stop(self) -> None:
        self._timer.stop()

    def _check(self) -> None:
        idle = self._idle.idle_seconds()
        # 用户恢复活动后重置标记，允许下一轮久坐再次触发
        if idle < _ACTIVE_RESET_SECS:
            self._water_reminded = False
            self._rest_reminded = False
            return

        water_min = self._settings.water_interval_min
        rest_min = self._settings.rest_interval_min
        if water_min > 0 and idle >= water_min * 60 and not self._water_reminded:
            self._water_reminded = True
            self.water_due.emit()
        if rest_min > 0 and idle >= rest_min * 60 and not self._rest_reminded:
            self._rest_reminded = True
            self.rest_due.emit()
