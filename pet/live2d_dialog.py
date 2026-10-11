"""添加 Live2D 模型对话框：选择一个 Cubism 模型文件夹，导入到 assets/live2d/。"""

import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from .live2d_view import LIVE2D_DIR, find_model_entry


class AddModelDialog(QDialog):
    """让用户选择本地模型文件夹，校验后复制到 assets/live2d/<名称>/ 并返回模型名。"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("添加 Live2D 模型")
        self.setMinimumWidth(440)
        self.model_name: str = ""
        self._src: Path | None = None

        self.path_label = QLabel("未选择文件夹")
        self.path_label.setWordWrap(True)
        browse = QPushButton("选择模型文件夹…")
        browse.clicked.connect(self._browse)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如 hibiki …")

        self.status = QLabel("请选择包含 *.model3.json 的 Cubism 模型文件夹。")
        self.status.setWordWrap(True)

        row = QHBoxLayout()
        row.addWidget(self.path_label, 1)
        row.addWidget(browse)

        form = QFormLayout()
        form.addRow("模型名称", self.name_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("导入")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addLayout(form)
        layout.addWidget(self.status)
        layout.addWidget(buttons)

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "选择 Live2D 模型文件夹")
        if not folder:
            return
        self._src = Path(folder)
        self.path_label.setText(str(self._src))
        if not self.name_edit.text().strip():
            self.name_edit.setText(self._src.name)
        self._validate()

    def _validate(self) -> str | None:
        if self._src is None:
            return "请先选择一个模型文件夹。"
        if find_model_entry(self._src) is None:
            return "该文件夹里没有找到 *.model3.json（或 *.model.json）入口文件。"
        return None

    def _accept(self) -> None:
        err = self._validate()
        if err:
            self.status.setText("⚠ " + err)
            return
        name = self.name_edit.text().strip()
        if not name:
            self.status.setText("⚠ 请填写模型名称。")
            return
        dest = LIVE2D_DIR / name
        if dest.exists():
            self.status.setText("⚠ 已存在同名模型，请换一个名称。")
            return
        try:
            # 只跳过 VCS / 系统垃圾文件，模型所需文件全部复制
            shutil.copytree(
                self._src,
                dest,
                ignore=shutil.ignore_patterns(
                    ".git",
                    "__pycache__",
                    "*.pyc",
                    "Thumbs.db",
                    "desktop.ini",
                    ".DS_Store",
                ),
            )
        except OSError as exc:
            self.status.setText("⚠ 导入失败：" + str(exc))
            return
        self.model_name = name
        self.accept()
