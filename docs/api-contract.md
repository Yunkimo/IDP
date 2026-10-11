# 后端实时事件契约（B1，待 A/C 评审）

关联 [Issue #5](https://github.com/Yunkimo/IDP/issues/5)。版本一提案与本分支实现一致；
尚未经 A/C 评审、合并或三端联调，不作为已确认的跨端契约。

## 连接与鉴权

- 路径：`ws://<后端地址>:8001/ws?token=<URL 编码的 API_TOKEN>`。
- 必须发起 HTTP Upgrade；普通 `GET /ws` 返回 404，不表示连接成功。
- 成功握手为 HTTP 101。缺失、空、错误、重复 token，或服务端未配置 `API_TOKEN`，
  均在接受连接前拒绝，真实 Uvicorn 返回 HTTP 403。
  ASGI TestClient 报 `WebSocketDisconnect(1008)`，不要混淆这两种观察方式。
- 同一演示 token 可连接多个客户端，各连接独立注册。断开后重连是新连接。
- 这是单用户受控演示的共享密钥，没有用户隔离、到期会话或刷新令牌。
  更换密钥并重启服务可撤销现有连接；公网发布前另行评审会话、TLS 和限流方案。
- 应用不接收客户端业务消息；发送文本或二进制数据帧将以 1008 关闭。
  WebSocket 协议层 ping/pong 由 Uvicorn 处理。
- 发送失败或超过配置超时移除连接，尽力以 1013 关闭；服务退出以 1001 关闭。
  已断网时客户端未必能收到 close 帧，应按断线处理。

## 事件信封

每条事件是一个 UTF-8 JSON 文本帧；同一次广播所有接收端获得相同 `event_id`。

| 字段 | 类型 | 语义 |
|---|---|---|
| `version` | 整数，当前为 1 | 不兼容变更递增版本，并先经 A/C 评审 |
| `event_id` | 非空字符串，生成时为 UUID | 一次逻辑事件的标识；接收端可去重 |
| `type` | 字符串 | 当前 schema 支持下表三类事件 |
| `occurred_at` | 带时区的 ISO 8601 字符串 | 服务端产生通知的时间，默认 UTC；不是提醒计划到期时间 |
| `data.id` | 正整数 | 由 `type` 确定资源类别的资源 ID；通知不包含业务正文 |

| `type` | 当前产生位置 | 获取状态 |
|---|---|---|
| `task.created` | `POST /api/tasks` 提交 SQLite 成功后 | `GET /api/tasks` |
| `course.created` | `POST /api/courses` 提交 SQLite 成功后 | `GET /api/courses` |
| `reminder.due` | 仅预留 schema 和广播入口；B2 调度器尚未实现 | `GET /api/reminders` |

样例（ID 与时间仅用于说明）：

```json
{"version":1,"event_id":"e2277dd9-8672-4d52-8e04-ec16845c3021","type":"task.created","occurred_at":"2026-10-11T08:00:00Z","data":{"id":1}}
{"version":1,"event_id":"1f6be7de-42d4-444a-9c4c-d6ed531958bd","type":"course.created","occurred_at":"2026-10-11T08:00:01Z","data":{"id":2}}
{"version":1,"event_id":"48a930c8-66f0-4f46-88f6-61a9b6947053","type":"reminder.due","occurred_at":"2026-10-11T08:00:02Z","data":{"id":3}}
```

服务内部调用入口：`await app.state.push_service.broadcast(event)`，返回成功执行发送的连接数。
输入先经 `Event` 校验，无效输入不发送；不是可被客户端调用的 HTTP 发布接口。
生产者若重试同一事件，应复用完整信封，包括 `event_id`。

## 一致性、失败与兼容

- 后端是唯一持久化数据源；事件只是提示。收到事件后用 REST 读取状态。
- 先建立连接，再读取初始快照；重连后重新拉取。客户端忽略未知字段、未知事件类型；
  遇到不支持的版本先刷新 REST，并记录兼容问题。
- B1 不提供历史补发、确认回执、持久队列或可靠送达保证。离线、重启或崩溃窗口会丢事件。
  `send` 成功也不能证明客户端展示。不能宣称 exactly-once。
- 一次广播并发发送给各连接，每条连接的发送串行化。并发 REST 请求间不承诺全局事件顺序。
- 推送失败不回滚已提交的 SQLite 写入，REST 仍返回原有 201 及资源正文。
  HTTP 本身断线时先查 REST 确认，不能仅因未收到事件就重试写入。
- B1 仅对日程和课表的创建发送事件；更新、删除、提醒创建没有新增广播。
- 固定单进程、单 worker。多 worker 的连接集合互不可见，不可直接扩容后声称广播等价。
- `WS_SEND_TIMEOUT_SECONDS` 默认 2；`WS_CLOSE_TIMEOUT_SECONDS` 默认 1。
  含锁等待的单连接发送超过上限会被移除；清理另有关闭上限。二者都必须为正有限秒数。
  环境变量优先于 `backend/.env`，最后使用默认值。
- Uvicorn 的应用日志移除 URL 整个 query。反向代理、监控和客户端日志仍需独立脱敏，
  禁止记录完整连接 URL；调试级第三方协议日志不在本次脱敏保证内。

复现方法见 [后端 WebSocket 验证报告](test-report.md)。实现参考：
[FastAPI WebSockets 官方文档](https://fastapi.tiangolo.com/advanced/websockets/)。
