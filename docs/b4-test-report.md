# B4 验收与测试报告

整理日期：2026-10-15（Asia/Shanghai）。关联 [Issue #8](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/8)，起始基线 `42a95ba`，功能提交 `43b06a7`。独立 B4 分支不包含尚待合并的 B3 功能，因此用例总数与 B3 分支不同。

## 环境与命令

Windows 11 Home China 64 位，10.0.26200；Intel Core i7-1165G7、8 逻辑处理器，约 15.73 GiB RAM。Python 3.13.0 / 3.10.22，pytest 9.1.1、Ruff 0.17.0；后端使用现有锁文件，无新增运行依赖。自动化临时 SQLite；curl 验收使用真实 Uvicorn、单 worker、随机本机端口和随机凭证。

在仓库根目录，激活对应 Python 后端环境：

```powershell
python -m pytest -c backend/pytest.ini backend/tests -q --cov=app --cov-report=term
python scripts/smoke_backend_web_query.py
python scripts/smoke_backend_web_query.py --live --output tmp/b4-live.json
python -m pre_commit run --all-files
python -m pip_audit -r backend/requirements.txt
```

桌面回归使用桌面虚拟环境和 `QT_QPA_PLATFORM=offscreen`。本机真实上游请求使用既有出口代理，未更改全局代理或个人 `.env`。证据 JSON 时间字段保留执行时 UTC 原值，报告日期按会话时区记录。

## 实测结果

| 项目 | 结果 | 证据 |
|---|---|---|
| Python 3.13 后端 | 172 passed，14.29 秒 | [输出](evidence/b4/backend-py313.txt) |
| Python 3.10 后端 | 172 passed，12.62 秒 | [输出](evidence/b4/backend-py310.txt) |
| 桌面回归 | 106 项通过 | [输出](evidence/b4/desktop.txt) |
| B4 新增用例 | 63 项；原有 109 项保留 | `backend/tests/test_web_query.py` |
| 全后端行覆盖 | 994 / 1059，93.86% | [摘要](evidence/b4/coverage-summary.json) |
| B4 路由 / 适配器行覆盖 | 100% / 98.54%；未统计分支覆盖 | 同上 |
| Mock + 真 curl | 天气、搜索均成功；未授权 401 | [JSON](evidence/b4/mock-curl.json) |
| 真实天气 curl | 退出码 0，返回 Beijing 天气摘要；2308.50 毫秒 | [JSON](evidence/b4/live-curl.json) |
| 真实搜索 curl | 退出码 0，返回 3 条标题/摘要/来源；1707.62 毫秒 | 同上 |
| 后端依赖审计 | No known vulnerabilities found | `pip-audit -r backend/requirements.txt` 实际输出 |

上游实时验收每种查询仅一个最终成功样本，耗时包括本机 curl、后端和代理网络，不可外推 p95、长期可用率或服务器吞吐。搜索结果及天气观测可能带有上游缓存；fetched_at 只表示本次获取时间。测试出现一条既有 Starlette TestClient 弃用提示，没有跳过测试或为提示改动依赖。

## 安全与异常用例

| 场景 | 验证内容 |
|---|---|
| 鉴权 | 两接口均拒绝缺失/错误 API Key，且不访问上游；不向公共服务转发 API Key |
| 输入 | 空白、超长、控制/双向格式字符、非法 limit 拒绝；城市中的 URL、IP、特殊路径拒绝 |
| 网络 | 202/403/429、500、302、超时、连接失败分别映射，异常正文脱敏；重定向不跟随，不自动重试 |
| 资源 | 原始流及解压后大小有限；gzip/deflate 压缩炸弹、截断、尾部垃圾和损坏均拒绝；超时释放并发槽位 |
| 天气 | 嵌套 JSON 结构校验，空值/布尔/NaN/无限值/明显越界数值拒绝 |
| 搜索 | 嵌套强调标签解析、实体解码、去重与数量限制；空结果、验证码与畸形页面分别报告 |
| 链接 | javascript/file、内网 IP、localhost、账号口令、非法端口或控制字符丢弃，不访问结果页面 |
| 日志 | 查询参数经 httpx 过滤器脱敏；不将上游异常正文传给客户端 |

## 失败、修正与量化口径

首次真实 curl 的天气成功、搜索被上游拒绝，原始记录保留在 [第一次](evidence/b4/live-curl-first.json) 和 [第二次](evidence/b4/live-curl-second.json)，没有把失败删除或改写为成功。移除未经需求要求的固定搜索地区参数后，拒绝仍然存在。

随后对相同关键词比较请求：普通 `gzip, deflate` 协商返回 200、10 个结果链接；`identity` 返回 202 验证页面。依据该观察补充标准压缩支持，同时改用原始响应流和有输出上限的解压，增加 5 项压缩用例。最终天气与搜索均通过真实 curl。这里只记录观察到的差异，不断言平台风控内部原因；生产路径没有验证码绕过、自动重试或更换搜索引擎。

另复用 B3 已验证的 SQLite 锁恢复测试修正：通过真实事务提交事件观察恢复，停止扫描后读库，避免测试观察者自身与写事务争锁。该改动属于共享测试维护，不计为 B4 新增功能或新增用例；B4 不依赖 B3 微信业务代码。

共享锁恢复用例同步后，33 项调度测试再次通过（3.27 秒）。提交检查中，Windows 默认编码的密钥扫描通过，而强制 UTF-8 后检测到拒绝测试中的假账号口令 URL；因此将钩子固定为 `python -X utf8 -m detect_secrets.pre_commit_hook`，只对该行假值增加带原因的 allowlist，保留其余扫描范围。Ruff、格式、空白及修正后的 UTF-8 扫描均已通过，提交钩子保持启用。共享测试修正与扫描配置分别以 `c58f9a1`、`dbbd213` 单独提交。

本次是新增后端接口，没有将 A2 本地工具迁移为后端，因此不申报“旧桌面工具重构加速”。可量化证据为 63 项新增自动化、0 项新增运行依赖、每次调用至多一次上游请求，以及明确的 8 秒默认期限、256 KiB 双重大小上限和最多 5 条结果。结构收益是路由/网络适配器分层及可注入 transport；无未经测量的性能增益。

## 交付边界

接口、真实 curl 和 Mock 故障验收已完成；待其他成员评审、PR 合并及 A/C 接入确认。远端 CI 以本次 PR 最新运行记录为准。公网部署、跨端 GUI 演示和视频不由本报告冒充完成，具体使用与安全边界见 [B4 接口说明](b4-web-query.md)。

## 人工验收发现的终端日志问题与修正

用户在 PowerShell 中启动验收服务时发现进程号显示为 `%d`，监听地址显示为 `%s://%s:%d`。实际健康检查返回 200，但日志脱敏过滤器提前清空了 `record.args`，使 Uvicorn 的彩色模板无法插值；访问日志格式器也因缺少五个请求字段而报错。此前自动验收确认了 HTTP 响应，却没有断言真实终端日志，这是原验证范围的缺口。

修正后访问日志保留五个结构化字段，仅脱敏请求路径；普通消息和彩色消息分别完成插值并脱敏，再清空原始参数。查询串仍整体隐藏，没有关闭彩色输出、访问日志或安全过滤器。

- 新增 12 项回归用例，直接使用 Uvicorn 的 DefaultFormatter / AccessFormatter。修正前 9 项失败、3 项通过；修正后全部通过，覆盖彩色/非彩色输出、实际进程号和 URL、普通/敏感路径、重复过滤及彩色消息脱敏。
- 修正后的 Python 3.13 全量后端 184 项通过，10.89 秒；Python 3.10 同为 184 项通过，12.29 秒。见 [3.13 输出](evidence/b4/log-fix-backend-py313.txt) 与 [3.10 输出](evidence/b4/log-fix-backend-py310.txt)。前文 172 项及覆盖率保留为初次验收记录，本次没有重新测量覆盖率。
- 独立临时库和随机端口启动真实 Uvicorn，强制启用彩色日志；健康检查 200，进程号/URL 插值正确、访问日志含 200 OK、查询内容脱敏，无日志异常。见 [实际控制台验证](evidence/b4/console-log-check.json)。没有停止用户正在运行的验收服务。

已经启动的进程不会自动加载本次修改：在原终端按 Ctrl+C，再执行原 Uvicorn 启动命令，之后继续人工天气与搜索验收。此次修正不代表用户已完成剩余人工检查。
