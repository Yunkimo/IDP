# B4 压缩处理复验报告

日期：2026-10-16（Asia/Shanghai）。被测后端版本：`39f790c`，关联 [Issue #8](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/8) 与 [PR #30](https://github.com/Yunkimo/Intelligent-Desktop-Pet/pull/30)。本次交付复验报告、证据和复现脚本，后端业务实现未改动。

## 结论与原始记录

复核未发现压缩处理或 PR 中相关说明存在需要修正的问题。两次早期搜索失败与后续成功均保留：

- [第一次失败](evidence/b4/live-curl-first.json)、[第二次失败](evidence/b4/live-curl-second.json)：搜索 curl 退出码 22，错误为 `upstream_unavailable`，总结果 false。
- [首次完成真实验收](evidence/b4/live-curl.json)：天气与搜索均成功，不覆盖此前失败。
- [本次真实复验](evidence/b4/live-recheck-20261016.json)：天气与搜索均成功，搜索返回 3 条结果。

压缩支持与上游拒绝是不同层面的行为：此前观察到不同协商方式返回不同响应，不能据此断言免费搜索服务以后不会拒绝请求。异常压缩数据只在本机 MockTransport 中构造，不向公共服务发送。

## 结果与口径

| 项目 | 实际结果 |
|---|---|
| B4 现有接口用例 | 63 项通过，3.02 秒；包含 5 项已有压缩用例 |
| 独立压缩边界矩阵 | gzip / deflate 各 10 类输入、4 种分块大小，共 80/80 通过 |
| 真实天气 curl | 退出码 0，status=ok，摘要非空，3877.44 毫秒 |
| 真实搜索 curl | 退出码 0，status=ok，3 条结果，3766.51 毫秒 |

环境沿用 [B4 测试报告](b4-test-report.md)：Windows 11、Python 3.13.0、现有锁定依赖。独立矩阵整理为正式脚本后，Python 3.13.0 与 3.10.22 再次运行均 80/80 通过，并接入两组后端 CI。

真实请求使用 Uvicorn 单 worker、临时数据库、随机凭证和真实 curl，经本机已有 `127.0.0.1:7890` 代理访问上游；验收期限 15 秒，产品默认仍为 8 秒。执行时间为上海时间 2026-10-16 00:05，JSON 保留 UTC 原值。每种查询仅一个本轮成功样本，不据此推断长期可用率或 p95。

80 组检查是独立脚本的组合数，不计入仓库已有的 184 项 pytest 用例；没有重新测量覆盖率。用户此前已反馈人工验收全部正常，此处记录的是助手执行的复验，不代填新的人工结果。

## 边界矩阵

| 维度 | 内容 |
|---|---|
| 编码 | gzip、deflate |
| 分块大小 | 1、7、64、4096 字节 |
| 正常输入 | 小响应、解压后恰好 1024 字节 |
| 大小限制 | 解压后超出 1 字节、10 万字节高压缩率展开、原始传输超限 |
| 异常输入 | 无效压缩流、截断、校验损坏、尾部垃圾、拼接流 |
| 每组附加检查 | 响应流已关闭，并发槽位已释放 |

检查预算为 1024 字节，单并发。正常输入须还原原文；超限返回 `upstream_response_too_large`，损坏等返回 `upstream_invalid_compression`，均为 502。脚本修改的配置只存在于自身进程，结束时恢复；不修改 `.env` 或用户数据库。

## 复现方法

在仓库根目录、已安装后端开发依赖的 Python 环境中执行：

```powershell
python -m pytest -c backend/pytest.ini backend/tests/test_web_query.py -q --tb=short
python scripts/check_backend_compression.py --output tmp/b4-compression-recheck.json
# 下条命令显式访问真实上游；仅在有对应出口代理时传 --proxy。
python scripts/smoke_backend_web_query.py --live --proxy http://127.0.0.1:7890 --output tmp/b4-live-recheck.json
```

[复现脚本](../scripts/check_backend_compression.py) 不访问外网，任何结果或资源释放检查失败均以非零退出码结束；默认只输出汇总，`--output` 保存完整 JSON。CI 执行前两类离线检查，真实上游另测。

完整矩阵结果见 [原始 JSON](evidence/b4/compression-recheck-20261016.json)。本轮原始结果从本地复验文件复制归档，不覆盖旧证据；脚本整理后的 Python 3.13 输出与原始 JSON 内容完全一致。
