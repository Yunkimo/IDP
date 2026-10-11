# 更新日志

本项目遵循[语义化版本](https://semver.org/lang/zh-CN/)与 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范。

## [未发布]

### 新增

- 支持导入与切换任意 Live2D（Cubism 4）模型：右键菜单新增「切换模型」子菜单与「添加 Live2D 模型…」导入窗口，选择本地模型文件夹即拷入 `assets/live2d/` 并一键切换。
- 模型加载、动作组、表情名改为从模型元数据动态发现，不再硬编码具体模型；`config.json` 新增 `live2d_model` 字段记录当前模型。
- 新增全局语音快捷键：长按 Ctrl+T（默认）即可开始录音、松开自动识别并发送，无需先唤出输入框；右键「设置语音快捷键…」可自定义为任意组合键（Ctrl/Shift/Alt + 字母/符号/功能键），写入 `config.json` 的 `voice_hotkey` 并在重启后保留。依赖新增 `pynput`。

### 变更

- 右键菜单「更换形象…」改名为「切换图片…」，与「切换模型 / 切换表情 / 切换人设」措辞统一。
- 移除内置 Live2D 模型（含演示脚本）与对应人设预设，保留 Live2D 导入/切换接口，模型改由用户自行导入。

### 修复

- 修复「逗一下 ♪」/ 说话动作无反应：动作组分类改为按「是否含 `.motion3.json` 动作文件」判断，只从真实动作组随机播放，并跳过下标 0 的「回正」复位动作。

## [1.3.0] - 2026-09-14

### 修复

- 桌宠点击判定区域过大：改为仅形象区域内响应点击 / 拖拽 / 右键菜单，透明空白区不再误触。

## [1.2.0] - 2026-09-14

### 新增

- 支持 **Live2D 动态形象**（Cubism 4）：含眨眼、呼吸、物理、待机动作、表情与说话动作。
- 形象引擎抽象为策略模式（`Avatar` / `SpriteAvatar` / `Live2DAvatar` / `create_avatar`），`config.json` 的 `image_engine` 一键切换，Live2D 不可用时自动回退图片精灵。
- 右键菜单新增「逗一下 ♪」随机动作与「切换表情」子菜单（Live2D 引擎）。
- 说话播报时模型自动播放「动作#6」动作，加载时自动初始化（「Start」动作）。

### 变更

- 默认形象引擎改为 `live2d`；`PetWindow` 不再直接依赖 `PetSprite`，统一走 `Avatar` 接口。
- 依赖新增 `PyQt6-WebEngine`（Live2D 渲染，可选依赖）。

### 修复

- 修复 Qt6 在创建 `QApplication` 前未导入 `QtWebEngineWidgets`（或设置 `AA_ShareOpenGLContexts`）导致的 WebEngine 初始化报错。

## [1.1.0] - 2026-09-14

### 新增

- 桌宠人设支持自定义：预设自称「人家」、称呼主人「伙伴」、句尾常带「♪」。
- 支持 GIF / WebP 动图形象播放（QMovie），形象按宽高比等比缩放、不再拉伸变形。
- 右键菜单「更换形象…」：运行时选择本地图片即时换装，并自动写入 `config.json`（重启后保留）。
- 右键菜单「退出」：无边框窗口也能正常关闭桌宠。
- 新增 `启动桌宠.bat`，双击即可启动。

### 修复

- 单帧 WebP 改走 QPixmap 平滑缩放，修复大图缩小时锯齿、发虚的问题。
- 更换形象时自动裁掉四周透明边，形象更贴合、显示更大。

### 变更

- 默认形象改为高清透明立绘。
- 依赖新增 `Pillow`，用于图片格式归一化（规避本机 Qt 读取部分 PNG 报 `libpng error` 的问题）。

## [1.0.0] - 2026-09-14

### 新增

- 初始版本：无边框 / 置顶 / 透明的桌面宠物窗口，支持拖拽移动、点击唤起输入框。
- LLM 文字对话（DeepSeek），气泡流式显示。
- 语音合成（edge-tts）与语音识别（faster-whisper），支持双向语音对话。
- 人设系统与跨会话记忆。
- 设计文档、用户手册、单元测试与 CI 流水线。

[1.3.0]: https://github.com/Yunkimo/Intelligent-Desk-Pet/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Yunkimo/Intelligent-Desk-Pet/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Yunkimo/Intelligent-Desk-Pet/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Yunkimo/Intelligent-Desk-Pet/releases/tag/v1.0.0
