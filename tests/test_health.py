"""HealthMonitor 久坐检测逻辑测试：注入假空闲源与假时钟，绕过真实系统 API 与 QTimer。"""

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


class _Clock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t


def test_water_due_after_sitting_threshold(qapp):
    clock = _Clock()
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=_Idle(10), clock=clock)
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()  # 在座，开始计时
    clock.t = 61
    mon._check()
    assert fired == ["water"]


def test_rest_due_after_sitting_threshold(qapp):
    clock = _Clock()
    mon = HealthMonitor(_Settings(water=0, rest=1), idle_source=_Idle(10), clock=clock)
    fired: list[str] = []
    mon.rest_due.connect(lambda: fired.append("rest"))
    mon._check()
    clock.t = 61
    mon._check()
    assert fired == ["rest"]


def test_no_reminder_when_away(qapp):
    clock = _Clock()
    mon = HealthMonitor(_Settings(water=1, rest=1), idle_source=_Idle(600), clock=clock)
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon.rest_due.connect(lambda: fired.append("rest"))
    mon._check()
    clock.t = 600
    mon._check()
    assert fired == []  # 离座（空闲 ≥ 5 分钟）不算久坐


def test_water_repeats_every_interval(qapp):
    clock = _Clock()
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=_Idle(10), clock=clock)
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()
    clock.t = 61
    mon._check()  # 第一次
    clock.t = 120
    mon._check()  # 距上次 59s，未到一个间隔
    clock.t = 121
    mon._check()  # 距上次 60s，第二次
    assert fired == ["water", "water"]  # 每坐满一个间隔就再提醒一次


def test_away_resets_sitting_session(qapp):
    clock = _Clock()
    idle = _Idle(10)
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=idle, clock=clock)
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()  # 在座，session 开始于 t=0
    clock.t = 61
    mon._check()
    assert fired == ["water"]

    idle.seconds = 600  # 离开座位
    mon._check()

    idle.seconds = 10  # 回来，重新计时
    clock.t = 62
    mon._check()
    clock.t = 123
    mon._check()
    assert fired == ["water", "water"]


def test_short_idle_within_session_counts_as_sitting(qapp):
    # 空闲 299 秒（< 5 分钟）仍是「在座」，累计时长照常触发
    clock = _Clock()
    mon = HealthMonitor(_Settings(water=1, rest=0), idle_source=_Idle(299), clock=clock)
    fired: list[str] = []
    mon.water_due.connect(lambda: fired.append("water"))
    mon._check()
    clock.t = 61
    mon._check()
    assert fired == ["water"]


def test_settings_health_defaults():
    from pet.config import Settings

    s = Settings()
    assert isinstance(s.health_enabled, bool)
    assert s.water_interval_min > 0
    assert s.rest_interval_min > 0
