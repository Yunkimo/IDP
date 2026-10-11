"""应用引导。"""

import sys

from PyQt6.QtWidgets import QApplication

from .config import Settings
from .webenv import enable_local_file_access, prepare_webengine
from .window import PetWindow


def run() -> int:
    enable_local_file_access()  # 必须在 QApplication 之前，WebEngine 才能读取本地模型

    settings = Settings()
    if settings.image_engine == "live2d":
        try:
            prepare_webengine()  # 必须在 QApplication 之前导入 WebEngineWidgets
        except ImportError:
            pass  # WebEngine 未安装，交由 create_avatar 回退到精灵引擎

    app = QApplication(sys.argv)
    app.setApplicationName("Intelligent Desk Pet")

    window = PetWindow(settings)
    window.show()

    if not settings.llm_api_key:
        window.show_hint("还没配置 LLM_API_KEY 哦～在 .env 里填好再重启我就能聊天啦")
        print("警告：未配置 LLM_API_KEY，请在 .env 中填写（参考 .env.example）。")

    return app.exec()
