# 工作量与协作台账

| 成员 | Issue | 类别 | 预估点数 | 状态 | 证据 | 验收人 |
|---|---|---|---:|---|---|---|
| A / Yunkimo | [#1](https://github.com/Yunkimo/IDP/issues/1) | BackendClient（httpx REST + X-API-Key） | 待团队确认 | 已完成 | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`3385fe5`/`7905385` | 待 B/C 评审 |
| A / Yunkimo | [#2](https://github.com/Yunkimo/IDP/issues/2) | Agent 工具调用（function calling + 工具循环 + 联网查询） | 待团队确认 | 已完成 | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`67de45f`/`94861b7` | 待 B/C 评审 |
| A / Yunkimo | [#3](https://github.com/Yunkimo/IDP/issues/3) | 健康关怀（久坐提醒） | 待团队确认 | 已完成 | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`c273278`→`9ff1bef` | 待 B/C 评审 |
| A / Yunkimo | [#4](https://github.com/Yunkimo/IDP/issues/4) | 实时接收（WebSocket 监听） | 待团队确认 | 进行中（`reminder.due` 待 B2 闭环） | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`fbae3c3` | 待 B/C 评审 |
| B / wwweiliang | [#5](https://github.com/Yunkimo/IDP/issues/5) | WebSocket 广播，含测试与接口文档 | 5（守则初始估算，待团队确认） | 已合并，验收记录待补 | [PR #16](https://github.com/Yunkimo/IDP/pull/16)、[测试报告](test-report.md)、[契约](api-contract.md) | 待 A/C 确认 |
| B / wwweiliang | [#6](https://github.com/Yunkimo/IDP/issues/6) | 提醒调度、故障恢复、迁移及量化验证 | 8（守则初始估算，待团队确认） | 待评审 | 功能 cbd0f63、[B2 报告](b2-test-report.md)、[原始数据](evidence/b2/) | 待 A/C 评审 |

2026-10-12 核验：B1 的 PR #16 已合并到 develop；GitHub reviews 接口未返回独立评审记录，
不据合并动作补造人工评审或三端验收。#5 议题仍打开。

实际工时未人工登记；验收点数尚未确认，各条目「预估点数」待团队统一口径后填写。
代码、测试和文档均属于同一成果，不重复计分。C（YingboQi）的 C1–C5 条目待其完成后补录。
未形成最终绩效比例，不以代码行数或提交数推算个人成绩。
