"""tools 注册表测试：用假后端验证工具绑定与结果格式化，隔离网络。"""

from pet.tools import build_tools, tool_schema


class _FakeBackend:
    def __init__(self) -> None:
        self.courses: list[dict] = []
        self.tasks: list[dict] = []
        self.created_tasks: list[dict] = []
        self.reminder: dict | None = None

    def list_courses(self):
        return self.courses

    def list_tasks(self):
        return self.tasks

    def create_task(self, title, note="", due_at=None, remind_at=None):
        self.created_tasks.append(
            {"title": title, "note": note, "due_at": due_at, "remind_at": remind_at}
        )
        return {"id": 1, "title": title}

    def update_task(self, task_id, **fields):
        self.updated = (task_id, fields)

    def delete_task(self, task_id):
        self.deleted = task_id

    def create_reminder(self, title, remind_at, body="", channel="both", task_id=None):
        self.reminder = {"title": title, "remind_at": remind_at, "body": body, "channel": channel}


def test_build_tools_has_expected_names():
    tools = build_tools(_FakeBackend())
    expected = {
        "list_courses",
        "list_tasks",
        "create_task",
        "update_task",
        "delete_task",
        "create_reminder",
        "get_weather",
        "web_search",
    }
    assert expected <= set(tools)


def test_list_courses_formats():
    b = _FakeBackend()
    b.courses = [
        {
            "name": "高等数学",
            "day_of_week": 1,
            "start_time": "08:00",
            "end_time": "09:40",
            "location": "A101",
        }
    ]
    out = build_tools(b)["list_courses"].fn()
    assert "高等数学" in out
    assert "周1 08:00-09:40" in out


def test_create_task_calls_backend():
    b = _FakeBackend()
    tools = build_tools(b)
    result = tools["create_task"].fn(title="复习英语", due_at="2026-10-12T09:00:00")
    assert result == "已新增日程「复习英语」"
    assert b.created_tasks[0]["title"] == "复习英语"
    assert b.created_tasks[0]["due_at"] == "2026-10-12T09:00:00"


def test_create_reminder_calls_backend():
    b = _FakeBackend()
    tools = build_tools(b)
    tools["create_reminder"].fn(title="喝水", remind_at="2026-10-11T10:00:00", channel="pc")
    assert b.reminder["title"] == "喝水"
    assert b.reminder["channel"] == "pc"


def test_tool_schema_shape():
    tools = build_tools(_FakeBackend())
    schema = tool_schema(tools["create_task"])
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "create_task"
    assert "title" in schema["function"]["parameters"]["properties"]
