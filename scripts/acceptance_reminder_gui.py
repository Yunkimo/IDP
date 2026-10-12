"""以真实 PetWindow、WS 和临时后端验收到期提醒；不调用聊天或语音服务。"""

import argparse
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def run(args) -> dict:
    """仅修改本进程 Settings；数据库、凭证和应用历史均隔离。"""
    from PyQt6.QtCore import QEvent, QObject, Qt, QTimer
    from PyQt6.QtWidgets import QApplication

    from pet.config import Settings
    from pet.window import PetWindow

    with tempfile.TemporaryDirectory(prefix="idp-gui-acceptance-") as directory:
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        token = secrets.token_urlsafe(32)
        environment = os.environ.copy()
        environment.update(
            API_TOKEN=token,
            DB_PATH=str(Path(directory) / "acceptance.db"),
            SCHEDULER_ENABLED="true",
            SCHEDULER_INTERVAL_SECONDS=str(args.interval),
        )
        server_code = (
            "import uvicorn; uvicorn.run('app.main:app',host='127.0.0.1',port=%d,ws='websockets-sansio')"
            % port
        )
        if args.fail_first_commit:
            environment.update(
                SCHEDULER_LEASE_SECONDS="3",
                SCHEDULER_SEND_TIMEOUT_SECONDS="1",
                DB_TIMEOUT_SECONDS="0.2",
            )
            server_code = (
                "from app import reminder_store\n"
                "original = reminder_store.finish\n"
                "failed = False\n"
                "def finish(*args):\n"
                " global failed\n"
                " if not failed:\n"
                "  failed = True\n"
                "  raise RuntimeError('acceptance: crash after send before commit')\n"
                " return original(*args)\n"
                "reminder_store.finish = finish\n"
            ) + server_code
        with tempfile.TemporaryFile() as log:
            server = subprocess.Popen(
                [str(ROOT / "backend/.venv/Scripts/python.exe"), "-c", server_code],
                cwd=ROOT / "backend",
                env=environment,
                stdout=log,
                stderr=log,
            )
            try:
                base_url = f"http://127.0.0.1:{port}"
                with httpx.Client(base_url=base_url, timeout=5, trust_env=False) as client:
                    deadline = time.monotonic() + 15
                    while True:
                        try:
                            client.get("/api/health").raise_for_status()
                            break
                        except httpx.HTTPError:
                            if server.poll() is not None or time.monotonic() > deadline:
                                raise RuntimeError("Temporary backend did not start") from None
                            time.sleep(0.05)

                settings = Settings()
                settings.backend_url, settings.api_token = base_url, token
                settings.llm_api_key = ""
                settings.persist_history = False
                settings.history_path = Path(directory) / "history.json"
                settings.enable_voice = False
                settings.health_enabled = False
                settings.image_engine, settings.frames = "sprite", []
                settings.bubble_timeout_ms = 60000
                settings.pet_name = (
                    "B2 故障恢复验收（临时环境）"
                    if args.fail_first_commit
                    else "B2 提醒验收（临时环境）"
                )
                app = QApplication([])
                window = PetWindow(settings)
                # 截图工具不枚举 Qt Tool 窗口；只在验收进程改为普通顶层窗口。
                if args.capture_window:
                    window.setWindowFlag(Qt.WindowType.Tool, False)
                report = {
                    "head_sha": subprocess.check_output(
                        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                    ).strip(),
                    "interval_seconds": args.interval,
                    "lead_seconds": args.lead,
                    "fault_after_first_send": args.fail_first_commit,
                    "voice_enabled": False,
                    "capture_window": args.capture_window,
                    "measurement": "real WsListener -> PetWindow -> REST -> bubble paint callback",
                    "events": [],
                    "paints": [],
                }

                def save():
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(
                        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                    )

                def received(event):
                    if event.get("type") != "reminder.due":
                        return
                    report["events"].append(
                        {"event_id": event["event_id"], "handled_epoch": time.time()}
                    )
                    save()

                class PaintObserver(QObject):
                    def eventFilter(self, obj, event):  # noqa: N802
                        if event.type() == QEvent.Type.Paint and len(report["paints"]) < len(
                            report["events"]
                        ):
                            index = len(report["events"])
                            QTimer.singleShot(0, lambda: painted(index))
                        return False

                def painted(index):
                    if len(report["paints"]) >= index:
                        return
                    now = time.time()
                    report["paints"].append(
                        {
                            "event_number": index,
                            "painted_epoch": now,
                            "from_created_seconds": now - report["created_epoch"],
                            "from_due_seconds": now - report["due_epoch"],
                            "visible": window.bubble.isVisible(),
                            "text": window.bubble._text,
                        }
                    )
                    report["reminder"] = window.backend.list_reminders()[0]
                    save()

                def create():
                    created = time.time()
                    due = created + args.lead
                    report.update(created_epoch=created, due_epoch=due)
                    report["created_reminder"] = window.backend.create_reminder(
                        "B2 验收提醒",
                        datetime.fromtimestamp(due, timezone.utc).isoformat(),
                        body="请确认桌宠已显示到期提醒",
                        channel="pc",
                    )
                    save()

                def finish():
                    report["reminder"] = window.backend.list_reminders()[0]
                    report["duplicate_events"] = len(report["events"]) - len(
                        {event["event_id"] for event in report["events"]}
                    )
                    report["completed"] = True
                    save()
                    window.close()
                    app.quit()

                observer = PaintObserver(window)
                window.bubble.installEventFilter(observer)
                window.ws.event.connect(received)
                window.show()
                QTimer.singleShot(2000, create)
                QTimer.singleShot(int((2 + args.lead + args.interval + args.hold) * 1000), finish)
                app.exec()
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=5)
            log.seek(0)
            assert token not in log.read().decode("utf-8", errors="replace")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=1)
    parser.add_argument("--lead", type=float, default=10)
    parser.add_argument("--hold", type=float, default=20)
    parser.add_argument("--fail-first-commit", action="store_true")
    parser.add_argument("--capture-window", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    options = parser.parse_args()
    if options.interval <= 0 or options.lead <= 0 or options.hold < 5:
        parser.error("interval/lead must be positive and hold must be at least five seconds")
    result = run(options)
    assert result["events"] and result["paints"] and result["reminder"]["done"] == 1
