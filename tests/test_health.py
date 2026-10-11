"""HealthMonitor 久坐检测逻辑测试：注入假空闲源，绕过真实系统 API 与 QTimer。"""

from pet.health import HealthMonitor


class _Settings:
    def __init__(self, enabled=True, water=30, rest=60) -> None:
        self.health_enabled = enabled
        self.water_interval_min = water
        self.rest_interval_min = rest


class _Idle:
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    def idle_seconds(self) -> float:
        return self.seconds


def test_water_due_when_idle_exceeds(qapp):
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=_Idle(120))
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()
    assert fired == ["water"]


def test_rest_due_when_idle_exceeds(qapp):
    mon = HealthMonitor(_Settings(water=0, rest=1), idle_source=_Idle(120))
    fired: list[str] = []
    mon.rest_due.connect(lambda: fired.append("rest"))
    mon._check()
    assert fired == ["rest"]


def test_no_reminder_when_active(qapp):
    mon = HealthMonitor(_Settings(water=1, rest=1), idle_source=_Idle(1))
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("w"))
    mon.rest_due.connect(lambda: fired.append("r"))
    mon._check()
    assert fired == []


def test_reminder_fires_once_per_idle_session(qapp):
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=_Idle(120))
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()
    mon._check()
    assert fired == ["water"]  # 同一轮久坐只提醒一次


def test_reset_after_activity(qapp):
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=_Idle(120))
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()
    assert fired == ["water"]

    mon._idle = _Idle(1)  # 用户恢复操作
    mon._check()  # 重置标记
    mon._idle = _Idle(120)  # 再次久坐
    mon._check()
    assert fired == ["water", "water"]


def test_settings_health_defaults():
    from pet.config import Settings

    s = Settings()
    assert isinstance(s.health_enabled, bool)
    assert s.water_interval_min > 0
    assert s.rest_interval_min > 0
