# 任务书：成员 C —— 小程序 + 部署 + 文档

> 把本文件直接交给 AI 编程助手（如 Claude Code），即可按此开工。先读第 1、2、3 节，再按第 4 节顺序逐项完成。

## 1. 项目背景（agent 必读）

「智能桌宠」是期末课设项目，三端架构：

```
桌宠端（成员 A）  ↔  后端（成员 B）  ↔  小程序（你负责）
   PyQt6 + agent      FastAPI + SQLite      微信小程序
   HTTP REST + WebSocket                    HTTP REST + WebSocket
                                    后端 → 微信订阅消息（离线推送）
```

- **后端是唯一数据源**：课表、日程、提醒都存后端 SQLite，三端读写同一份数据。
- 你的端是「移动端 + 交付」：小程序让用户在手机上查改课表/日程、实时刷新、离机收订阅消息；同时负责部署与文档交付。

## 2. 你负责的范围

| 编号 | 任务 | 说明 |
|---|---|---|
| C1 | 小程序骨架 + api.js | 页面 + `wx.request` 对接后端 |
| C2 | 实时刷新 | `wx.connectSocket` 连后端 `/ws` |
| C3 | 订阅消息授权 | 「订阅提醒」按钮 + 一次性订阅 |
| C4 | 部署 | 内网穿透 + `docs/deploy.md`（含学生机路线） |
| C5 | 文档 + CI + 演示 | README / 设计文档 / CI / 演示脚本 |

## 3. 当前状态与起点

- 仓库：本仓库（`origin = https://github.com/Yunkimo/IDP`），分支模型 `main` / `develop` / `feat/*`。
- 现状：仓库已有 `backend/`（M1 后端骨架已完成）和 `pet/`（桌宠基线）。小程序是全新目录 `miniprogram/`。
- 前置：安装「微信开发者工具」；注册小程序（个人主体即可，需实名）拿到 `appid`。
- 你的工作分支：从 `develop` 切出 `feat/miniprogram`。

## 4. 任务清单

### C1. 小程序骨架 + api.js
- 新建 `miniprogram/`：`project.config.json`（填 appid）、`app.js` / `app.json` / `app.wxss`、页面 `pages/index`（今日课表/待办）、`pages/schedule`（课表增删改）、`pages/task`（日程增删改）。
- 新建 `utils/api.js`：封装 `wx.request` 调 FastAPI（带 `X-API-Key` 头），`baseUrl` 集中在文件顶部配置。
- 依赖：后端 M1（已就绪）。
- 验收：小程序增删课表，后端 DB 同步。

### C2. 实时刷新
- 在 `utils/api.js` 加 `wx.connectSocket` 连后端 `/ws`，收到 `reminder.due` / `task.created` 等事件刷新页面。
- 依赖：成员 B 的 B1。
- 验收：后端加数据，小程序即时刷新。

### C3. 订阅消息授权
- 「订阅提醒」按钮 → `wx.requestSubscribeMessage` → 把 openid + 授权交给后端（`POST /api/wechat/subscribe`）。
- 依赖：成员 B 的 B3。
- 验收：订阅后触发提醒，手机微信收到订阅消息（小程序关着也能收）。

### C4. 部署
- 内网穿透（ngrok / cpolar）拿公网 HTTPS，写 `docs/deploy.md`：含开发路线（内网穿透）+ 上线路线（学生机 + 域名 + ICP 备案 + systemd + Nginx + certbot）。
- 开发期在「微信开发者工具 → 详情 → 本地设置」勾选「不校验合法域名」即可连内网穿透地址。
- 依赖：B1 就绪后后端可被公网访问。
- 验收：公网 HTTPS 能访问后端 `/api/health`，小程序连上。

### C5. 文档 + CI + 演示
- `README.md`（项目说明 + 快速开始）、用户手册、设计文档（UML 图，图文并茂）。
- CI（GitHub Actions）补后端 pytest + 覆盖率。
- 演示脚本/视频（视频由用户本人录制）。
- 开源依赖许可证清单 + 信息安全设计说明（HTTPS / API Key / 密钥管理）。

## 5. 技术约定（必须遵守）

- 小程序所有请求/长连接都指向后端 `baseUrl`（`utils/api.js` 顶部统一配置）。
- 订阅消息为**一次性授权**（点一次收一条）；演示用一次性订阅即可，长期订阅需特殊类目资质。
- 密钥不写进小程序源码；API key 走请求头，由后端校验。

## 6. 分支与提交

- 分支：`feat/miniprogram`（从 `develop` 切）。
- 原子提交 + Conventional Commits：`feat(miniprogram): ...`、`docs: ...` 分开。
- 每个任务单独提交，完成后开 PR 到 `develop`。

## 7. 验证方式

- 微信开发者工具 + 真机预览走通：增删课表、实时刷新、订阅提醒。
- `docs/deploy.md` 步骤可复现（别人照着能跑通）。

## 8. 协作与依赖

- C2 依赖 B1、C3 依赖 B3；**先做 C1 和 C5 的文档部分**，C2/C3 等后端就绪再联调。
- 与成员 B 联调订阅消息；接口字段以 `backend/app/schemas.py` 为准。
