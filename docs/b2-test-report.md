# B2 提醒调度验证报告

日期：2026-10-12；关联 [Issue #6](https://github.com/Yunkimo/IDP/issues/6)。
基线为 B1 合并提交 `9f4e9df7bbc51800be350a06e1084a2e656e6ed6`，基线 30 例通过。
被测功能提交：`cbd0f634965abdcd95f4a53896ccee52f6f43aa6`。
本报告是后端验证证据，人工评审、桌宠展示及三端验收尚未完成。

## 自动化结果

| 检查 | 实际结果 | 原始记录 |
|---|---|---|
| Windows / Python 3.13.0 | 63 passed，1 warning，6.07 秒 | [pytest](evidence/b2/pytest-py313.txt) |
| Windows / Python 3.10.22 | 63 passed，1 warning，5.47 秒 | [pytest](evidence/b2/pytest-py310.txt) |
| 后端 app 行覆盖率（3.13） | 538/561，95.90%（工具显示 96%）；scheduler 100%，reminder_store 97% | 同上覆盖率输出 |
| Ruff、格式、暂存空白、密钥扫描 | 全部通过 | [pre-commit](evidence/b2/pre-commit.txt) |
| 后端完整运行锁文件漏洞扫描 | 两版本均未发现已知漏洞；未新增依赖 | [3.13](evidence/b2/dependency-audit.json)、[3.10](evidence/b2/dependency-audit-py310.json) |
| B1 真实网络回归 | 两客户端各 30 事件、ID 一致；两种无效握手均 403；日志凭证脱敏 | [结果](evidence/b2/ws-regression.json) |

保留的 warning 是既有 Starlette TestClient 对 httpx 集成的弃用提示；没有屏蔽它。
pip-audit 对完整锁文件使用 `--no-deps --disable-pip`，工具提示建议使用依赖哈希；
当前采用精确版本锁定，远端 CI 另执行标准 `pip-audit -r requirements.txt`。

## 风险用例映射

新增 33 项（含参数化）见 `backend/tests/test_scheduler.py`；原 B1 的 30 项全部保留。

| 用例 | 主要场景与实际结果 |
|---|---|
| B-T01 | CRUD、鉴权、WS 回归全部通过；诊断接口未授权返回 401，不存在返回 404 |
| B-T03 | 到期边界、重复扫描、四连接并发领取、批量上限、停机租约恢复通过 |
| B-T03 | 发送前中断、发送后写回前中断、最后一次领取中断；稳定 event_id、拒绝旧领取覆盖、停止无限重试通过 |
| B-T04 | 零连接、发送异常与超时、数据库锁冲突、取消及生命周期资源释放通过 |
| B-T04 | 编辑/删除使旧领取失效；重新安排产生新事件；phone 保留待 B3、人工完成不重发通过 |
| B-T06 | 时区规范化、非法输入与显式 null 返回 422、异常正文不进入日志通过 |
| B-T04 | 旧库备份、幂等迁移、非法历史时间隔离、迁移中断回滚与重试通过 |
| B-T04 | 真实执行备份 CLI、拒绝覆盖已有目标、恢复到新路径并读取数据通过 |
| B-T08 | 单 worker 真实网络延迟，三组各 30 条，结果见下表 |

故障窗口以固定时钟、受控异常和状态恢复模拟，不宣称执行过操作系统强制断电测试。
迁移和恢复仅操作临时库；没有改动用户数据库。

## 真实网络测量

Windows 11、i7-1165G7、约 15.73 GiB RAM，本机 loopback，单 Uvicorn worker，单 WS 客户端。
每组提醒到期时间均匀分布在一个扫描间隔内；统计从计划 UTC 到期到 Python 客户端收包，
分位数使用 nearest-rank。原始 JSON 包含全部逐条时间、event_id 和 done 状态。

| Python / 扫描间隔 | 收到 / 样本 | 超时 / 重复 | done=1 | p50 ms | p95 ms | max ms | 墙钟漂移估计 ms |
|---|---|---|---:|---:|---:|---:|---:|
| 3.13 / 1 秒 | 30/30（100%） | 0/0 | 30 | 748.666 | 948.313 | 960.657 | 0.002 |
| 3.13 / 30 秒 | 30/30（100%） | 0/0 | 30 | 14235.036 | 27944.475 | 28925.885 | 0.000 |
| 3.10 / 1 秒 | 30/30（100%） | 0/0 | 30 | 551.943 | 725.420 | 738.380 | 1.637 |

原始记录：[1 秒](evidence/b2/latency-1s.json)、[30 秒](evidence/b2/latency-30s.json)、
[3.10 / 1 秒](evidence/b2/latency-py310-1s.json)。
失败阈值分别为 5 秒和 35 秒，全部样本在各自阈值内；没有提前触发。
重复数只覆盖脚本从连接到收齐样本的观察窗口；长期重复风险另由恢复和重复扫描用例覆盖。
墙钟漂移是同机墙钟与单调钟增量差，不是绝对时钟精度，也不测跨机器同步误差。
默认 30 秒组明显不满足五秒目标；GUI 展示、公网、多设备与微信均未测。
这些是单轮每组 30 样本的功能实测，不作为五次重复的重构性能比较。

## 复现命令

从仓库根目录运行；预先按 CONTRIBUTING 安装后端开发依赖。

```powershell
$env:COVERAGE_FILE = Join-Path $env:TEMP 'idp-b2.coverage'
backend/.venv/Scripts/python -m pytest backend/tests --cov=backend/app --cov-report=term-missing
tmp/backend-py310/Scripts/python -m pytest backend/tests
backend/.venv/Scripts/python scripts/smoke_backend_scheduler.py --interval 1 --samples 30 --max-delay 5 --output tmp/b2-1s.json
backend/.venv/Scripts/python scripts/smoke_backend_scheduler.py --interval 30 --samples 30 --max-delay 35 --output tmp/b2-30s.json
tmp/backend-py310/Scripts/python scripts/smoke_backend_scheduler.py --interval 1 --samples 30 --max-delay 5 --output tmp/b2-py310.json
backend/.venv/Scripts/python scripts/smoke_backend_ws.py
backend/.venv/Scripts/python -m pip_audit -r backend/requirements.txt --no-deps --disable-pip
```

`tmp/backend-py310` 是本机独立兼容环境路径；其他成员可用自己的 Python 3.10 虚拟环境替代。
pre-commit 需将后端虚拟环境放入 PATH 后运行 `python -m pre_commit run --all-files`。
CI 在 Linux Python 3.10/3.12 执行 pytest、两种真实网络脚本、检查及依赖审计；结果以 PR checks 为准。

## 真实修复与尚未验收项

覆盖率执行时曾发现测试 SQLite 连接的 ResourceWarning：连接上下文仅提交事务，不负责关闭。
改为 `contextlib.closing` 后双版本回归通过；备份与迁移也显式关闭连接。
没有据此编造人工评审或独立缺陷的绩效点数。

待 A/C 确认：无时区历史输入的默认 UTC+8、done 的 WS 阶段含义、#6 的计时起点与最终展示口径。
还需其他成员干净部署/恢复复现、桌宠与小程序联调、真实人工评审；B3 微信另行实施。
参见 [实现与回滚](b2-scheduler.md)、[候选质量口径](quality-baseline.md)、[契约](api-contract.md)。
