# 小程序（任务书 C）

微信小程序端：手机查改课表/日程。今日页看当天课表与到期待办，课表页/日程页增删改，经 `utils/api.js` 对接后端 FastAPI（后端是唯一数据源）；`utils/ws.js` 订阅后端 WebSocket 事件实现实时刷新。

## 目录

| 路径 | 说明 |
|---|---|
| `project.config.json` | 微信开发者工具项目配置（`appid` 为占位 `touristappid`，请替换为你注册的 appid） |
| `app.js` / `app.json` / `app.wxss` | 全局入口（启动 WebSocket 适配层）、页面注册与 TabBar、全局样式 |
| `pages/index` | 今日课表 / 待办（按本周周次过滤、勾选完成、下拉刷新） |
| `pages/schedule` | 课表增删改 + 图片识别导入（按星期分组，周次支持 `1-16` / `1,3,5` 写法） |
| `pages/task` | 日程增删改（截止日期、勾选完成） |
| `utils/api.js` | `wx.request` / `wx.uploadFile` 封装：`baseUrl` 与 `X-API-Key` 集中配置于文件顶部 |
| `utils/ws.js` | WebSocket 事件适配层：连接/重连/节流/去重集中管理（契约见 `docs/api-contract.md`） |
| `utils/datetime.js` | 日期换算与本周周次工具（后端 `day_of_week` 1=周一 … 7=周日） |
| `config.example.js` | 复制为 `config.js` 填入 `baseUrl` / `apiKey`（`config.js` 已 gitignore，密钥不入库） |

## 本地联调

1. 启动后端：`backend/` 下 `python run.py`，健康检查 `GET /api/health`。
2. 微信开发者工具导入本目录（`miniprogram/`），把 `project.config.json` 的 `appid` 换成你自己的。
3. 复制 `config.example.js` 为 `config.js`，填入后端地址与 `backend/.env` 的 `API_TOKEN`。
4. 开发期后端是 http/ws：详情 → 本地设置 → 勾选「不校验合法域名」（上线路线见 `docs/deploy.md`，任务 C4）。
5. 编译预览：增删课表/日程，后端 SQLite 同步（验收：小程序增删课表，后端 DB 同步）。

## 实时刷新（C2）

- 启动时 `utils/ws.js` 连接 `ws://<后端>/ws?token=<API_TOKEN>`（由 `config.js` 的 `baseUrl`/`apiKey` 映射，页面不各自建连）。
- 收到 `task.created` / `course.created` / `reminder.due` 事件后，相关页面自动用 REST 重读（事件按契约校验、`event_id` 去重、400ms 节流合并）。
- 断线自动退避重连（1s→30s），重连成功与回到前台都会 REST 重读（后端无历史事件补发）。
- 验收：后端加数据（curl 或桌宠），小程序页面即时刷新；杀后端进程再拉起，小程序自动重连。

## 接口约定

- 所有请求带 `X-API-Key` 头，由后端校验；401 = Key 无效，503 = 后端未配置 `API_TOKEN`。
- 课表 `/api/courses`、日程 `/api/tasks`；字段以 `backend/app/schemas.py` 为准。
- 课表 `weeks` 在后端是 JSON 字符串（如 `"[1,2,3]"`），提交时传数字数组，展示由页面解析。
