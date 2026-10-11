# 智能桌宠 · Intelligent Desk Pet

[![CI](https://github.com/Yunkimo/IDP/actions/workflows/ci.yml/badge.svg)](https://github.com/Yunkimo/IDP/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

期末课设：三端协作的智能桌面宠物。桌宠端用文字 / 语音与用户对话，靠大模型 + 工具调用查课表、排日程、设提醒；后端是唯一数据源与调度中枢；小程序让用户在手机上查改并接收离线提醒。

```
桌宠端（A）   ↔   后端（B）   ↔   小程序（C）
PyQt6 + Agent     FastAPI + SQLite     微信小程序
HTTP REST + WebSocket                  HTTP REST + WebSocket
                          后端 → 微信订阅消息（离线推送）
```

## 当前进度

| 部分 | 状态 |
|---|---|
| **桌宠基线**：无边框窗口、文字与双向语音对话、人设与跨会话记忆、Live2D 形象接口 | ✅ 已迁入 |
| **后端 M1 骨架**：课表 / 日程 / 提醒 CRUD + `X-API-Key` 鉴权 + 6 单测 | ✅ 已完成 |
| **工程基建**：CI 双 job、ruff 检查与格式化、`main` / `develop` 分支保护 | ✅ 已完成 |
| **A1–A4** 后端客户端 / Agent 工具调用 / 健康关怀 / 实时接收 | ⬜ 待开发 |
| **B1–B4** WebSocket 广播 / 到期调度 / 微信订阅 / 联网查询 | ⬜ 待开发 |
| **C1–C5** 小程序骨架 / 实时刷新 / 订阅授权 / 部署 / 文档 | ⬜ 待开发 |

细化到验收标准的任务清单见 [docs/tasks/](docs/tasks/)。

## 快速开始

### 桌宠端

```bat
setup.bat                  :: 建 .venv 并安装依赖（一次性）
copy .env.example .env     :: 填入 LLM_API_KEY
启动桌宠.bat                :: 启动（缺 .venv 会自动先跑 setup.bat）
```

也可手动运行：`.venv\Scripts\python main.py`。无后端也能纯聊天。

> 首次使用语音识别会自动下载 faster-whisper 模型（约 100~500 MB）；下载慢可先 `set HF_ENDPOINT=https://hf-mirror.com`。

### 后端

```bat
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env     :: 填入 API_TOKEN
.venv\Scripts\python run.py
```

启动后监听 `0.0.0.0:8001`，健康检查 `GET /api/health`。接口调用需带请求头 `X-API-Key: <API_TOKEN>`。

### 小程序

尚未开始（计划目录 `miniprogram/`），见 [任务书 C](docs/tasks/C-miniprogram-deploy.md)。

## 使用说明

- **拖拽**移动宠物，**点击**唤出 / 收起输入框，回车发送，宠物流式回复并语音播报
- **说话**：点输入框右侧 🎤 录音；或全局按住 `Ctrl+T` 录音、松开自动识别发送（右键可改快捷键）
- **右键菜单**：切换形象 / 切换人设 / 切换 Live2D 模型 / 添加 Live2D 模型 / 退出
- **Live2D**：点模型脸换表情，说话与待机自动做动作；仓库不内置模型，用「添加 Live2D 模型…」导入 Cubism 4 模型文件夹即可

完整操作与配置项见 [用户手册](docs/user-manual.md)。

## 目录结构

```
pet/             桌宠端（PyQt6：窗口 / 形象 / 对话 / 语音 / 记忆）
backend/         后端（FastAPI + SQLite，唯一数据源）
miniprogram/     小程序（待建）
assets/          桌宠素材（live2d/ 为渲染运行时，模型由用户自行导入）
docs/            设计文档、用户手册、测试与安全文档、三份任务书
tests/           桌宠端测试（后端测试在 backend/tests/）
scripts/         冒烟测试
config.json      桌宠非敏感配置
.env             密钥（不提交）；后端另有 backend/.env
```

## 分工与协作

| 成员 | 负责 | 工作分支 | 任务书 |
|---|---|---|---|
| A [@Yunkimo](https://github.com/Yunkimo) | 桌宠端智能体 | `feat/desktop-agent` | [A](docs/tasks/A-desktop-agent.md) |
| B [@wwweiliang](https://github.com/wwweiliang) | 后端服务 | `feat/backend-realtime` | [B](docs/tasks/B-backend-service.md) |
| C [@YingboQi](https://github.com/YingboQi) | 小程序 + 部署 + 文档 | `feat/miniprogram` | [C](docs/tasks/C-miniprogram-deploy.md) |

分支模型：`main`（主干）/ `develop`（开发）/ `feat/*`（特性）。`main` 与 `develop` 均已开启分支保护，改动须经 PR + CI 通过 + 1 人审批。

## 文档

- [设计文档（架构与设计模式）](docs/design.md)
- [用户手册](docs/user-manual.md) ｜ [测试文档](docs/testing.md) ｜ [信息安全设计](docs/security.md)
- [任务书 A / B / C](docs/tasks/)

## 许可证与依赖

本项目采用 **MIT License**（见 [LICENSE](LICENSE)）。主要依赖及其许可证：

| 依赖 | 许可证 | 用途 |
|---|---|---|
| PyQt6 / PyQt6-WebEngine | GPL-3.0 / 商业 | GUI 与 Live2D 渲染 |
| fastapi / uvicorn / pydantic | MIT / BSD / MIT | 后端服务 |
| openai | Apache-2.0 | LLM 调用 |
| edge-tts | LGPL-3.0 | 语音合成 |
| faster-whisper | MIT | 语音识别 |
| sounddevice / numpy / Pillow / python-dotenv | MIT / BSD / MIT / BSD | 录音、数值、图像、配置 |

`assets/live2d/` 内含 Live2D 前端运行时：pixi.js（MIT）、pixi-live2d-display（MIT）、Cubism Core（Live2D 专有许可）。

> ⚠️ **模型版权**：仓库不内置任何 Live2D 模型，模型由用户自行导入，请确认其授权情况。本项目仅用于课程设计 / 学习演示。

## 常见问题

- **听不到 / 说不了话**：确认麦克风权限已允许，且首次已下载 whisper 模型。
- **LLM 报错**：检查 `.env` 的 `LLM_API_KEY` 是否正确、`LLM_BASE_URL` 是否可达。
- **后端 401 / 503**：检查 `backend/.env` 的 `API_TOKEN` 是否与请求头 `X-API-Key` 一致（未配置会返回 503）。
