"""后端 REST 客户端：封装 httpx 调用，统一携带 X-API-Key 鉴权头。

桌宠端与后端交互的唯一入口，屏蔽 URL 拼接、鉴权、错误处理细节；
上层（Agent 工具 / 调试入口）只关心业务方法。
"""

import httpx


class BackendError(Exception):
    """后端调用失败（网络异常或非 2xx 响应）。"""


class BackendClient:
    """访问后端 REST 的客户端，封装课表 / 日程 / 提醒的 CRUD。

    base_url 与 api_token 来自配置（见 Settings.backend_url / Settings.api_token）。
    """

    def __init__(self, base_url: str, api_token: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self._token = api_token
        self._timeout = timeout

    # ---------- 底层 ----------
    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._token}

    def _request(self, method: str, path: str, json: dict | None = None):
        url = f"{self.base_url}{path}"
        try:
            resp = httpx.request(
                method, url, headers=self._headers(), json=json, timeout=self._timeout
            )
        except httpx.HTTPError as exc:
            raise BackendError(f"后端不可达：{exc}") from exc
        if resp.status_code >= 400:
            raise BackendError(f"后端返回 {resp.status_code}: {resp.text}")
        if resp.status_code == 204:
            return None
        return resp.json()

    # ---------- 健康检查（无鉴权） ----------
    def health(self) -> dict:
        """GET /api/health，返回后端健康状态。"""
        return self._request("GET", "/api/health")

    # ---------- 课表 ----------
    def list_courses(self) -> list[dict]:
        return self._request("GET", "/api/courses")

    def create_course(
        self,
        name: str,
        day_of_week: int,
        start_time: str,
        end_time: str,
        location: str = "",
        weeks: list[int] | None = None,
    ) -> dict:
        return self._request(
            "POST",
            "/api/courses",
            json={
                "name": name,
                "day_of_week": day_of_week,
                "start_time": start_time,
                "end_time": end_time,
                "location": location,
                "weeks": weeks,
            },
        )

    def update_course(self, course_id: int, **fields) -> dict:
        return self._request("PUT", f"/api/courses/{course_id}", json=fields)

    def delete_course(self, course_id: int) -> None:
        self._request("DELETE", f"/api/courses/{course_id}")

    # ---------- 日程 / 待办 ----------
    def list_tasks(self) -> list[dict]:
        return self._request("GET", "/api/tasks")

    def create_task(
        self, title: str, note: str = "", due_at: str | None = None, remind_at: str | None = None
    ) -> dict:
        return self._request(
            "POST",
            "/api/tasks",
            json={"title": title, "note": note, "due_at": due_at, "remind_at": remind_at},
        )

    def update_task(self, task_id: int, **fields) -> dict:
        return self._request("PUT", f"/api/tasks/{task_id}", json=fields)

    def delete_task(self, task_id: int) -> None:
        self._request("DELETE", f"/api/tasks/{task_id}")

    # ---------- 提醒 ----------
    def list_reminders(self) -> list[dict]:
        return self._request("GET", "/api/reminders")

    def create_reminder(
        self,
        title: str,
        remind_at: str,
        body: str = "",
        channel: str = "both",
        task_id: int | None = None,
    ) -> dict:
        return self._request(
            "POST",
            "/api/reminders",
            json={
                "title": title,
                "body": body,
                "remind_at": remind_at,
                "channel": channel,
                "task_id": task_id,
            },
        )

    def update_reminder(self, reminder_id: int, **fields) -> dict:
        return self._request("PUT", f"/api/reminders/{reminder_id}", json=fields)

    def delete_reminder(self, reminder_id: int) -> None:
        self._request("DELETE", f"/api/reminders/{reminder_id}")
