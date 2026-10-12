# B2：提醒调度与故障恢复

对应 [Issue #6](https://github.com/Yunkimo/IDP/issues/6)。本分支实现提案，等待 A/C 对契约和验收口径评审。

## 数据与调度流程

```text
lifespan 启动唯一 Scheduler
    |
    v
线程执行 BEGIN IMMEDIATE -> 领取一个到期提醒 -> 提交事务
    |                       保存事件 ID、尝试次数、领取代号与租约
    v
检查领取仍有效 -> broadcast(reminder.due)，不持有 DB 锁
    |
    +-- 至少一个 WS send 成功 -> 校验领取代号 -> sent 与 done=1 同一事务提交
    |
    +-- 无连接/失败/超时 -> retry + 退避；达到尝试上限 -> failed，done=0

未写回就停机 -> 租约到期后重试，复用 event_id
服务关闭 -> 取消循环 -> 释放 WS 连接
```

连接 SQLite、领取和写回在线程中执行，每个操作自建并关闭连接；不跨线程共享连接对象。
SQLite 锁等待有配置上限，扫描失败记录固定错误信息后等待下轮，不忙轮询、不记录提醒正文或异常中的凭证。
取消时线程内已开始的短事务可能继续提交，因此保留租约恢复机制，不把取消等同于数据库回滚。

新增 `reminder_deliveries` 是必要的发送状态记录：原有 done 布尔值不足以区分未尝试、发送中、重试、失败和成功，
也无法在重启后复用 event_id。没有引入 ORM、消息中间件或分布式部署。`schema_migrations` 记录迁移版本与历史时区偏移。
本次为功能扩展，不申报没有基线对照的“重构性能增益”。

## 配置

环境变量优先于 `backend/.env`，最后使用默认值。完整示例见 `backend/.env.example`。

| 配置 | 默认 | 作用 |
|---|---:|---|
| SCHEDULER_ENABLED | true | false 可停用调度，但仍执行数据库迁移 |
| SCHEDULER_INTERVAL_SECONDS | 30 | 每轮完成后的等待秒数，启动立即扫描；联调用 1 或 2 |
| SCHEDULER_BATCH_SIZE | 100 | 每轮最多处理数量，一次只领取一个，避免整批租约提前过期 |
| SCHEDULER_SEND_TIMEOUT_SECONDS | 5 | 单次广播的总超时 |
| SCHEDULER_LEASE_SECONDS | 30 | 中断领取的恢复等待；必须大于发送超时加两倍 DB 锁等待 |
| SCHEDULER_MAX_ATTEMPTS | 3 | 总尝试上限，允许 1–10 |
| SCHEDULER_RETRY_SECONDS | 30 | 首次重试退避，随后翻倍 |
| SCHEDULER_MAX_RETRY_SECONDS | 300 | 退避上限 |
| DB_TIMEOUT_SECONDS | 2 | SQLite 锁等待上限 |
| DB_BACKUP_TIMEOUT_SECONDS | 30 | 自动迁移备份上限 |
| REMINDER_NAIVE_OFFSET_MINUTES | 480 | 无时区输入的固定偏移，允许 -1439–1439 分钟 |

此时区设置是兼容旧输入的固定偏移，不是夏令时地区规则。新客户端应总是发送明确偏移。
已规范化的数据不会因以后修改配置而被重新解释。所有秒数须为正有限数。
默认配置不是五秒提醒 SLA；大量积压、慢客户端、重试和数据库等待会额外增加延迟。

## 迁移、备份与回滚

1. 部署前停止旧服务，记录数据库路径与服务版本。在项目根目录执行：

   ```powershell
   backend/.venv/Scripts/python scripts/backup_backend_db.py <原数据库路径> <新的备份路径>
   ```

   脚本通过 SQLite backup 复制并检查完整性，拒绝覆盖任何已有目标。不能只复制仍在写入的 db 文件而遗漏 WAL。

2. 新服务 `init_db()` 迁移版本一；存在旧提醒时会额外自动保存同目录 `*.pre-b2-<唯一编号>.db`。
   迁移在一个事务中建立状态表、规范化有效时间并记录版本，重复启动不重复迁移。
   旧非法时间保留原文，状态为 failed / invalid_remind_at，避免一条坏数据阻塞全部提醒；应通过 REST 修正。

3. 旧 done=1 保留完成状态且不重播。旧 phone 提醒保留为待处理，不伪造微信结果。
   自动备份失败或超时会阻止迁移，不能绕过后继续使用半迁移状态。
   自动备份只有完整结束后才改为正式备份名；`.partial.db` 是失败中间文件，不用于恢复。

4. 回滚时停止新服务，以同一脚本将迁移前备份恢复到**新路径**，将旧版本的 DB_PATH 指向恢复库后启动。
   保留新库供核对；回滚会丢失备份后新写入，应先导出并人工协调，不能覆盖用户数据。
   迁移备份没有执行过另一成员的生产恢复验收；当前仅有临时库自动化验证。

失败任务通过 `/api/reminders/{id}/delivery` 排查。确认原因后 PUT `{"done":false}` 重置新事件，
或者同时修改 remind_at 重新安排。失败记录中的标识不含消息正文；后续成功会清除 last_error，历史失败原因保留在脱敏应用日志。

## 启停与复现

开发从 backend 执行 `python run.py`；服务器按 [用户手册](user-manual.md) 使用单 worker、无热重载命令。
多 worker 即使原子领取能减少冲突，WebSocket 集合仍分裂，不能据此扩容。

```powershell
backend/.venv/Scripts/python scripts/smoke_backend_scheduler.py --interval 1 --samples 30 --max-delay 5 --output tmp/b2-1s.json
backend/.venv/Scripts/python scripts/smoke_backend_scheduler.py --interval 30 --samples 30 --max-delay 35 --output tmp/b2-30s.json
```

脚本启动独立服务、创建临时库和随机凭证，测量真实 WS 收包后清理，不修改个人数据库。
测试会按配置等待，默认 30 秒组大约需半分钟。输出包括逐条数据、超时、重复、p50/p95/max、done 数量和本机墙钟漂移估计。
这不是桌宠 GUI 展示时间，也不是公网、多设备或微信测试。

实现依据：[Python sqlite3 事务与 backup](https://docs.python.org/3.10/library/sqlite3.html)、
[asyncio 取消与线程调用](https://docs.python.org/3.10/library/asyncio-task.html)。
