# B1 WebSocket 验证报告

议题：[Yunkimo/Intelligent-Desktop-Pet #5](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/5)。
开发基线：`49944767f441b7c625cbbb48bd28bcff1c08c844`；环境见 [environment](environment.md)。
功能与测试提交：`12635feeafe6f1204b33f43fd9485a4853841f75`。测试运行时的源码与该提交一致；
本报告及原始输出在后续文档提交中留存，未修改被测代码。
状态：本地实现与验证通过；他人评审、PR 合并和三端验收尚未完成。

## 执行与结果

在仓库根目录激活后端开发环境后执行：

```powershell
python -m pytest -c backend/pytest.ini backend/tests
python scripts/smoke_backend_ws.py
python -m ruff check .
python -m ruff format --check .
python -m pre_commit run --all-files
python -m pip_audit -r backend/requirements.txt
```

Python 3.10 审计的临时环境升级 pip 步骤出现下载失败，因此对已经完整锁定的依赖清单执行
`python -m pip_audit -r backend/requirements.txt --no-deps --disable-pip`，结果同样无已知漏洞；
完整记录保存在 `evidence/b1/dependency-audit-py310.json`。

| 验证 | 实际结果与证据 |
|---|---|
| M1 基线 | 6 passed；本次变更前执行，0.52 秒 |
| Python 3.10.22 | 30 passed；见 `evidence/b1/pytest-py310.txt` |
| Python 3.13.0 | 30 passed，后端行覆盖率 93%（328/353）；见 `evidence/b1/pytest-py313.txt` |
| 真实 Uvicorn 网络 | 两个独立连接各收 30 次事件，30 个事件 ID 一致且互异；见 `evidence/b1/smoke-py310.json` 与 `smoke-py313.json` |
| 拒绝握手 | 缺 token、错 token 均返回 HTTP 403；同一脚本校验 |
| 日志脱敏 | 实际服务器日志不含随机 token 或错误凭证，并出现脱敏标记 |
| 格式/静态检查/密钥检查 | 见 `evidence/b1/pre-commit.txt`；排除既有第三方 assets 与依赖清单的启发式扫描 |
| 依赖漏洞检查 | 未发现已知漏洞；见 `evidence/b1/dependency-audit.json`，平台条件跳过项保留在原始结果中 |

两版本均有一条 Starlette 提示：将来应从 httpx 测试传输迁移到 httpx2；当前仍可运行，未屏蔽警告。
已锁定当前运行依赖。本议题不进行无关测试传输迁移。

## 用例与边界

| 用例组 | 前置与操作 | 预期 |
|---|---|---|
| B-T01 | 临时库、测试 token；执行既有六例 | 健康检查、REST 鉴权和 CRUD 不回退 |
| B-T02 鉴权 | 缺失、空、错误、重复 token；另测服务未配置 | 拒绝且不注册；普通 HTTP GET 不是 WS 成功 |
| B-T02 广播 | 两客户端连接，POST 日程/课表 | 同一 event_id、UTC 时间、正确资源 ID，REST 可查已提交状态 |
| B-T02 隔离 | 可控慢连接、发送异常、并发广播 | 正常连接先收包；异常连接被移除，同一连接不并发写 |
| B-T04 清理 | 重复注册、断线、取消、关闭时握手 | 无重复登记、无残留连接；关闭有时间上限 |
| B-T04 一致性 | 数据库写入异常、推送异常 | 前者不通知；后者仍保留成功的 REST 写入 |
| B-T06 | 伪造客户端消息、无效 schema、query 日志 | 拒绝客户端发布；无效事件不发送；日志不留 query |
| 网络脚本 | 独立 Uvicorn 进程、临时数据库、两个客户端 | 真实 HTTP Upgrade、30 次收包一致、两类握手拒绝、日志脱敏 |

慢连接等网络故障通过可控假传输测试，与真实网络脚本分开报告。
网络脚本退出会终止测试进程，不用该步骤证明生产服务器优雅停机；应用生命周期与关闭边界由自动化测试验证。

## 真实失败与修复

1. 首次执行基线时依赖安装尚未结束，出现 `ModuleNotFoundError: fastapi`；安装完成后重新运行六例通过。
2. 跨版本解析发现 websockets 17.2 不支持 Python 3.10，改为按 Python 版本锁定依赖。
3. Python 3.10 首轮为 27 passed、2 failed：两例测试无法直接解析 ISO 8601 的 `Z` 后缀。
   修正测试时间解析后通过；另补充关闭中握手的并发边界测试，共 30 例。
4. 提交检查发现 `backend/run.py` 格式与用户手册 EOF 多余空行；按工具结果修复，没有绕过检查。
5. 密钥扫描曾报告既有文档和桌宠测试中的 `sk-xxxx`、`sk-test`；核实为占位值后，
   仅登记两条文件/内容哈希基线，不排除测试或业务文件。

## 尚未验证

- A/C 对契约的确认、三端 UI 展示、其他成员干净部署复现。
- B2 提醒调度与延迟分布、微信真机离线接收、多用户隔离、公网部署。
- 历史补发和可靠送达不在 B1 实现范围，连接中断可能丢失事件。
- 新代码未进行独立性能重构，不编造重构增益或验收视频。
