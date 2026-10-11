"""WebEngine 运行环境准备：必须在创建 QApplication / 任何 WebEngine 实例前调用。"""

import os


def enable_local_file_access() -> None:
    """允许 file:// 页面通过 fetch/XHR 加载本地模型资源。

    Live2D 的 HTML 需要跨源读取模型目录下的 .moc3 与贴图，默认的 Chromium
    安全策略会拦截 file:// 的 fetch，故在此关闭同源限制（仅本地桌面应用使用）。
    """
    os.environ.setdefault(
        "QTWEBENGINE_CHROMIUM_FLAGS",
        "--disable-web-security --allow-file-access-from-files",
    )


def prepare_webengine() -> None:
    """为 Live2D 引擎准备 WebEngine 运行环境。

    Qt6 要求：在创建 QApplication 之前导入 QtWebEngineWidgets，或设置
    AA_ShareOpenGLContexts，否则实例化 QWebEngineView 会直接报错。二者都做。
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    import PyQt6.QtWebEngineWidgets  # noqa: F401  # 提前导入以满足时序要求
