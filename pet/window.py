"""宠物主窗口：无边框/置顶/透明，组合形象、气泡、输入框，编排聊天与语音。"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QFileDialog, QInputDialog, QMenu, QWidget

from .asr import ASREngine
from .avatar import create_avatar
from .backend_client import BackendClient, WsListener, build_ws_url
from .bubble import SpeechBubble
from .config import Settings
from .event_cache import RecentEvents
from .health import HealthMonitor
from .image_utils import normalize_image
from .input_box import ChatInput
from .llm import LLMClient
from .memory import Memory
from .persona import build_system_prompt
from .providers import create_chat_provider
from .tools import build_tools
from .tts import TTSEngine
from .worker import ASRWorker, ChatWorker, TTSWorker

_GAP = 8
_INPUT_H = 36
_BUBBLE_RESERVE = 240

# 回复里出现这些词，通常表示宠物没听懂 / 需要用户澄清，此时做「疑惑」表情
_DOUBT_KEYWORDS = (
    "不明白",
    "没听懂",
    "没听清",
    "没听明白",
    "没明白",
    "没懂",
    "不太懂",
    "不理解",
    "理解不了",
    "听不懂",
    "再说一遍",
    "再说一次",
    "能再说",
)


def _is_confused_reply(text: str) -> bool:
    """判断回复是否表示「没听懂用户提问」。"""
    return any(k in text for k in _DOUBT_KEYWORDS)


class PetWindow(QWidget):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

        # —— 引擎 ——
        self.llm = LLMClient(create_chat_provider(settings))
        self.asr_engine = ASREngine(settings.whisper_model)
        self.tts_engine = TTSEngine(
            settings.tts_voice,
            settings.tts_rate,
            settings.tts_pitch,
            settings.tts_timeout_seconds,
            settings.tts_windows_fallback,
        )

        # —— 后端客户端（惰性：不配置后端也不影响纯聊天）——
        self.backend = BackendClient(settings.backend_url, settings.api_token)
        self.tools = build_tools(self.backend)

        # —— WebSocket 实时接收（未配置 API_TOKEN 时不启动）——
        self._recent_events = RecentEvents()
        self.ws = WsListener(build_ws_url(settings.backend_url, settings.api_token), parent=self)
        self.ws.event.connect(self._on_backend_event)
        self.ws.error.connect(lambda e: print(f"[ws] {e}"))
        if settings.api_token:
            self.ws.start()

        # —— 记忆 ——
        self.memory = Memory(settings.history_path, settings.max_history, settings.persist_history)
        self.memory.set_system(build_system_prompt(settings))

        self._init_window()
        self._init_children()
        self._size_and_position()
        self._init_audio()
        self._init_hotkey()
        self._init_health()

        # 拖拽/点击状态
        self._press_pos = None
        self._moved = False

        # worker 引用（保持存活，防被 GC）
        self.chat_worker: ChatWorker | None = None
        self.asr_worker: ASRWorker | None = None
        self.tts_worker: TTSWorker | None = None
        self._tts_tmp: str | None = None
        self._tool_status_active = False

    # ---------- 初始化 ----------
    def _init_window(self) -> None:
        self.setWindowTitle(self.settings.pet_name)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _init_children(self) -> None:
        self.avatar = create_avatar(self.settings, parent=self)
        self.bubble = SpeechBubble(self.settings.bubble_timeout_ms, parent=self)
        self.input = ChatInput(parent=self)
        self.input.hide()

        self.input.submitted.connect(self.send_text)
        self.input.mic_toggled.connect(self.on_mic_toggled)
        self.bubble.resized.connect(self._position_bubble)

    def _init_audio(self) -> None:
        self.player = QMediaPlayer(self)
        self.audio_out = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_out)
        self.audio_out.setVolume(1.0)
        self.player.mediaStatusChanged.connect(self._on_media_status)

    def _size_and_position(self) -> None:
        sw = self.avatar.widget.width()
        sh = self.avatar.widget.height()
        self.win_w = max(320, sw + 120)
        self.win_h = sh + _INPUT_H + _BUBBLE_RESERVE + _GAP * 4
        self.resize(self.win_w, self.win_h)

        screen = QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.win_w - 40, geo.bottom() - self.win_h - 40)

        self._layout_children()

    def _layout_children(self) -> None:
        sw = self.avatar.widget.width()
        sh = self.avatar.widget.height()
        sx = (self.width() - sw) // 2
        sy = self.height() - sh - _INPUT_H - _GAP * 2
        self.avatar.widget.setGeometry(sx, sy, sw, sh)

        ix = (self.width() - self.input.width()) // 2
        iy = sy + sh + _GAP
        self.input.move(ix, iy)

        self._position_bubble()

    def _position_bubble(self) -> None:
        if not self.bubble.isVisible():
            return
        bx = (self.width() - self.bubble.width()) // 2
        by = self.avatar.widget.y() - self.bubble.height() - _GAP
        self.bubble.move(max(0, bx), max(0, by))

    # ---------- 拖拽与点击 ----------
    def _hit_avatar(self, pos) -> bool:
        """判断给定窗口坐标是否落在形象区域内，避免透明空白区误触。"""
        return self.avatar.widget.geometry().contains(pos)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if not self._hit_avatar(event.position().toPoint()):
            return
        self._press_pos = event.globalPosition().toPoint()
        self._moved = False

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._press_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            delta = event.globalPosition().toPoint() - self._press_pos
            if delta.manhattanLength() > 4:
                self._moved = True
                self.move(self.pos() + delta)
                self._press_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton or self._press_pos is None:
            return
        if not self._moved:
            # 点击交给形象处理：Live2D 命中脸则换表情，未命中（或静态形象）再收起/展开输入框
            self.avatar.tap(event.position().toPoint(), on_miss=self.toggle_input)
        self._press_pos = None
        self._moved = False

    def toggle_input(self) -> None:
        if self.input.isVisible():
            self.input.hide()
        else:
            self.input.show()
            self.input.focus_input()

    # ---------- 更换形象 / 切换人设 ----------
    def contextMenuEvent(self, event) -> None:  # noqa: N802
        if not self._hit_avatar(event.pos()):
            return
        menu = QMenu(self)

        change = menu.addAction("切换图片…")
        change.triggered.connect(self._choose_image)

        if self.avatar.supports_motion:
            poke = menu.addAction("逗一下 ♪")
            poke.triggered.connect(lambda: self.avatar.react("poke"))

            expr_menu = menu.addMenu("切换表情")
            for name in self.avatar.expressions:
                act = expr_menu.addAction(name)
                act.triggered.connect(lambda _checked=False, n=name: self.avatar.set_expression(n))

            model_menu = menu.addMenu("切换模型")
            self._populate_model_menu(model_menu)
            model_menu.addSeparator()
            add_model = model_menu.addAction("添加 Live2D 模型…")
            add_model.triggered.connect(self._add_live2d_model)
        else:
            to_live2d = menu.addAction("切换为 Live2D 动态形象")
            to_live2d.triggered.connect(lambda: self._switch_engine("live2d"))

        persona_menu = menu.addMenu("切换人设")
        for name in self.settings.personas:
            act = persona_menu.addAction(name)
            act.triggered.connect(lambda _checked=False, n=name: self._switch_persona(n))
        persona_menu.addSeparator()
        add_act = persona_menu.addAction("添加人设…")
        add_act.triggered.connect(self._add_persona)

        hotkey_act = menu.addAction("设置语音快捷键…")
        hotkey_act.triggered.connect(self._set_voice_hotkey)

        backend_act = menu.addAction("测试后端连接")
        backend_act.triggered.connect(self._debug_backend)

        quit_act = menu.addAction("退出")
        quit_act.triggered.connect(self.close)

        menu.exec(event.globalPos())

    def _switch_persona(self, name: str) -> None:
        if not self.settings.switch_persona(name):
            return
        self.memory.set_system(build_system_prompt(self.settings))
        self.memory.clear_history()  # 清空旧人设对话，避免语气/身份残留
        self.setWindowTitle(self.settings.pet_name)
        self.bubble.set_text(f"人设已切换为「{name}」")

    def _add_persona(self) -> None:
        name, ok = QInputDialog.getText(self, "添加人设", "人设名字：")
        if not ok or not name.strip():
            return
        personality, ok = QInputDialog.getMultiLineText(self, "添加人设", f"「{name}」的性格描述：")
        if not ok:
            return
        tone, ok = QInputDialog.getMultiLineText(self, "添加人设", f"「{name}」的说话语气：")
        if not ok:
            return
        if self.settings.add_persona(name, personality, tone):
            self._switch_persona(name)

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择桌宠形象",
            "",
            "图片 (*.png *.jpg *.jpeg *.gif *.webp *.bmp)",
        )
        if not path:
            return
        self._apply_image(Path(path))

    def _apply_image(self, src: Path) -> None:
        """更换形象：用图片/动图引擎显示所选图片（必要时先从 Live2D 切过来）。"""
        # 先释放当前形象对图片文件的占用，避免覆盖正在显示的图片时锁文件崩溃
        self.avatar.clear()
        dest = normalize_image(src, self.settings.assets_dir)
        self.settings.update_frames([dest.name])
        if self.settings.image_engine != "sprite":
            self._switch_engine("sprite")  # 会按新 frames 重建并布局
        else:
            self.avatar.set_appearance(dest, self.settings.sprite_size)
            self._size_and_position()

    def _switch_engine(self, engine: str) -> None:
        """运行时切换形象引擎（图片 ↔ Live2D），重建形象控件并重新布局。"""
        if engine == self.settings.image_engine:
            return
        self.settings.update_image_engine(engine)
        self._rebuild_avatar()

    def _rebuild_avatar(self) -> None:
        """销毁旧形象控件，按当前配置重建并重新布局。"""
        old = self.avatar.widget
        old.hide()
        old.setParent(None)
        old.deleteLater()

        self.avatar = create_avatar(self.settings, parent=self)
        self.avatar.widget.show()
        self._size_and_position()

    def _populate_model_menu(self, menu: QMenu) -> None:
        """往「切换模型」子菜单填充已发现的 Live2D 模型，勾选当前项。"""
        from .live2d_view import discover_models

        for m in discover_models():
            act = menu.addAction(m["name"])
            act.setCheckable(True)
            act.setChecked(m["name"] == self.settings.live2d_model)
            act.triggered.connect(lambda _checked=False, n=m["name"]: self._switch_live2d_model(n))

    def _switch_live2d_model(self, name: str) -> None:
        """切换到指定 Live2D 模型并重建形象。"""
        if name == self.settings.live2d_model:
            return
        self.settings.update_live2d_model(name)
        self._rebuild_avatar()

    def _add_live2d_model(self) -> None:
        """弹出「添加 Live2D 模型」对话框，导入成功后切换到新模型。"""
        from .live2d_dialog import AddModelDialog

        dialog = AddModelDialog(self)
        if not dialog.exec() or not dialog.model_name:
            return
        self.settings.update_live2d_model(dialog.model_name)
        if self.settings.image_engine != "live2d":
            self._switch_engine("live2d")
        else:
            self._rebuild_avatar()
        self.bubble.set_text(f"已添加并切换到「{dialog.model_name}」模型 ♪")

    # ---------- 文本/聊天 ----------
    def send_text(self, text: str) -> None:
        self.memory.add_user(text)
        self.input.hide()
        self.bubble.clear()
        self._start_chat(self.memory.get_messages())

    def _start_chat(self, messages: list[dict]) -> None:
        if self.chat_worker is not None and self.chat_worker.isRunning():
            return
        self.input.set_busy(True)
        self._tool_status_active = False
        self.chat_worker = ChatWorker(self.llm, messages, tools=self.tools, parent=self)
        self.chat_worker.chunk.connect(self._on_chunk)
        self.chat_worker.status.connect(self._on_tool_status)
        self.chat_worker.done.connect(self._on_chat_done)
        self.chat_worker.error.connect(self._on_chat_error)
        self.chat_worker.start()

    def _on_chunk(self, chunk: str) -> None:
        """收到流式增量；若此前显示过工具状态，先清空再开始打字机。"""
        if self._tool_status_active:
            self.bubble.clear()
            self._tool_status_active = False
        self.bubble.append_chunk(chunk)

    def _on_tool_status(self, text: str) -> None:
        """工具执行中：在气泡显示进行状态（首块回复到达时被替换）。"""
        self._tool_status_active = True
        self.bubble.set_text(text)

    def _on_chat_done(self, text: str) -> None:
        self.input.set_busy(False)
        if text:
            self.memory.add_assistant(text)
            self.memory.save()
            if _is_confused_reply(text):
                self.avatar.react("confused")  # 没听懂用户提问
            else:
                self.avatar.reset_expression()  # 成功答出，恢复正常神态
            if self.settings.enable_voice:
                self._speak(text)
        else:
            # 空回复 = 无法回答，露出「疑惑」（圈圈眼 + 问号）
            self.avatar.react("confused")
            self.bubble.set_text("嗯…这个我答不上来…")

    def _on_chat_error(self, msg: str) -> None:
        self.input.set_busy(False)
        self.avatar.react("confused")
        self.bubble.set_text(f"呜…出错了：{msg}")

    # ---------- 语音合成 ----------
    def _speak(self, text: str) -> None:
        self.tts_worker = TTSWorker(self.tts_engine, text, parent=self)
        self.tts_worker.ready.connect(self._play_voice)
        self.tts_worker.error.connect(lambda e: print(f"[TTS] {e}"))
        self.tts_worker.start()

    def _play_voice(self, path: str) -> None:
        self._tts_tmp = path
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()
        self.avatar.react("speak")

    def _on_media_status(self, status) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.player.setSource(QUrl())
            self._cleanup_tts_tmp()

    def _cleanup_tts_tmp(self) -> None:
        if self._tts_tmp:
            try:
                os.remove(self._tts_tmp)
            except OSError:
                pass
            self._tts_tmp = None

    # ---------- 语音识别 ----------
    def on_mic_toggled(self, listening: bool) -> None:
        if listening:
            self.avatar.react("voice")  # 语音输入时随机换表情
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self) -> None:
        if self.asr_worker is not None and self.asr_worker.isRunning():
            return
        self.asr_worker = ASRWorker(self.asr_engine, self.settings.max_record_secs, parent=self)
        self.asr_worker.text.connect(self._on_asr_text)
        self.asr_worker.error.connect(self._on_asr_error)
        self.asr_worker.start()

    def _stop_recording(self) -> None:
        if self.asr_worker is not None and self.asr_worker.isRunning():
            self.asr_worker.request_stop()

    def _on_asr_text(self, text: str) -> None:
        self.input.set_listening(False)
        if text:
            self.input.edit.setText(text)
            self.send_text(text)
        else:
            self.bubble.set_text("没听清，再说一次嘛～")

    def _on_asr_error(self, msg: str) -> None:
        self.input.set_listening(False)
        self.bubble.set_text(f"听不到声音：{msg}")

    # ---------- 全局语音快捷键 ----------
    def _init_hotkey(self) -> None:
        """启动全局语音快捷键（长按说话）；pynput 未安装时优雅降级。"""
        self.hotkey = None
        try:
            from .hotkey import HotkeyManager
        except ImportError:
            print("[hotkey] pynput 未安装，全局语音快捷键不可用")
            return
        self.hotkey = HotkeyManager(self.settings.voice_hotkey, parent=self)
        self.hotkey.pressed.connect(self._on_hotkey_pressed, Qt.ConnectionType.QueuedConnection)
        self.hotkey.released.connect(self._on_hotkey_released, Qt.ConnectionType.QueuedConnection)
        self.hotkey.start()

    def _on_hotkey_pressed(self) -> None:
        """长按快捷键：开始录音。"""
        self.input.set_listening(True)
        self._start_recording()

    def _on_hotkey_released(self) -> None:
        """松开快捷键：停止录音并识别。"""
        self._stop_recording()

    # ---------- 健康关怀 ----------
    def _init_health(self) -> None:
        """启动久坐检测（按 config.json 的 health_enabled 开关）。"""
        self.health = HealthMonitor(self.settings, parent=self)
        self.health.sedentary_due.connect(self._on_sedentary_due)
        self.health.start()

    def _on_sedentary_due(self) -> None:
        self._remind_health("坐太久啦，起来喝口水、活动一下吧～")

    def _remind_health(self, text: str) -> None:
        self.show_hint(text)
        self.avatar.react("poke")
        if self.settings.enable_voice:
            self._speak(text)

    # ---------- 后端实时事件 ----------
    def _on_backend_event(self, event: dict) -> None:
        """验证信封并去重；缓存跟随窗口，断线重连不重复显示或播报。"""
        etype = event.get("type")
        event_id = event.get("event_id")
        data = event.get("data")
        if (
            event.get("version") != 1
            or etype not in {"reminder.due", "task.created", "course.created"}
            or not isinstance(event_id, str)
            or not 1 <= len(event_id) <= 128
            or not isinstance(data, dict)
            or type(data.get("id")) is not int
            or data["id"] <= 0
        ):
            return
        if self._recent_events.contains(event_id):
            return
        if etype == "reminder.due":
            self._remind_health(self._reminder_text(data["id"]))
        elif etype == "task.created":
            self.show_hint("收到新日程啦，需要我帮你看看吗～")
        elif etype == "course.created":
            self.show_hint("课表有更新啦～")
        self._recent_events.remember(event_id)

    def _reminder_text(self, reminder_id) -> str:
        """按事件里的资源 ID 用 REST 校正提醒正文；失败给兜底文案。"""
        try:
            for r in self.backend.list_reminders():
                if r.get("id") == reminder_id:
                    text = f"⏰ {r.get('title') or ''} {r.get('body') or ''}".strip()
                    return text or "有提醒到啦～"
        except Exception:  # noqa: BLE001 - 拉取失败用兜底文案
            pass
        return "有提醒到啦～"

    def _set_voice_hotkey(self) -> None:
        """弹出设置语音快捷键对话框，保存后重启监听。"""
        from .hotkey_dialog import HotkeyDialog

        dialog = HotkeyDialog(self.settings.voice_hotkey, self)
        if not dialog.exec() or not dialog.hotkey:
            return
        if dialog.hotkey == self.settings.voice_hotkey:
            return
        self.settings.update_voice_hotkey(dialog.hotkey)
        self._restart_hotkey()
        self.bubble.set_text(f"语音快捷键已设为「{dialog.hotkey}」♪")

    def _restart_hotkey(self) -> None:
        """停止旧监听并按新快捷键重建。"""
        if self.hotkey is not None:
            self.hotkey.stop()
            self.hotkey.deleteLater()
            self.hotkey = None
        self._init_hotkey()

    # ---------- 其它 ----------
    def show_hint(self, text: str) -> None:
        self.bubble.set_text(text)

    def _debug_backend(self) -> None:
        """临时调试入口：拉取后端课表/日程，在气泡显示（A1 验收）。"""
        try:
            courses = self.backend.list_courses()
            tasks = self.backend.list_tasks()
        except Exception as exc:  # noqa: BLE001 - 调试入口，直接反馈给用户
            self.show_hint(f"后端不可用：{exc}")
            return
        self.show_hint(f"后端正常～课表 {len(courses)} 条、日程 {len(tasks)} 条")

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.hotkey is not None:
            self.hotkey.stop()
        self.health.stop()
        self.ws.request_stop()
        self.ws.wait(2000)
        self.memory.save()
        self._cleanup_tts_tmp()
        super().closeEvent(event)
