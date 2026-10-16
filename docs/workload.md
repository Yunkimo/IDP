# 工作量与协作台账

| 成员 | Issue | 类别 | 预估点数 | 状态 | 证据 | 验收人 |
|---|---|---|---:|---|---|---|
| A / Yunkimo | [#1](https://github.com/Yunkimo/IDP/issues/1) | BackendClient（httpx REST + X-API-Key） | 待团队确认 | 已完成 | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`3385fe5`/`7905385` | 待 B/C 评审 |
| A / Yunkimo | [#2](https://github.com/Yunkimo/IDP/issues/2) | Agent 工具调用（function calling + 工具循环 + 联网查询） | 待团队确认 | 已完成 | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`67de45f`/`94861b7` | 待 B/C 评审 |
| A / Yunkimo | [#3](https://github.com/Yunkimo/IDP/issues/3) | 健康关怀（久坐提醒） | 待团队确认 | 已完成 | PR [#17](https://github.com/Yunkimo/IDP/pull/17)，`c273278`→`9ff1bef` | 待 B/C 评审 |
| A / Yunkimo；本轮修复 wwweiliang | [#4](https://github.com/Yunkimo/IDP/issues/4) | 实时接收及用户授权的去重/语音补全 | 待团队确认，不重复计点 | 联调通过，待评审 | 原 PR [#17](https://github.com/Yunkimo/IDP/pull/17)；修复 PR [#21](https://github.com/Yunkimo/IDP/pull/21)、[最新验收](b2-final-acceptance.md) | 未冒充独立评审 |
| B / wwweiliang | [#5](https://github.com/Yunkimo/IDP/issues/5) | WebSocket 广播，含测试与接口文档 | 5（守则初始估算，待团队确认） | 已合并，验收记录待补 | [PR #16](https://github.com/Yunkimo/IDP/pull/16)、[测试报告](test-report.md)、[契约](api-contract.md) | 待 A/C 确认 |
| B / wwweiliang | [#6](https://github.com/Yunkimo/IDP/issues/6) | 提醒调度、故障恢复、迁移及量化验证 | 8（守则初始估算，待团队确认） | 联调通过，待评审 | 功能 cbd0f63、[最新验收](b2-final-acceptance.md)、[原始数据](evidence/b2/) | 未冒充独立评审 |

2026-10-12 核验：B1 的 PR #16 已合并到 develop；GitHub reviews 接口未返回独立评审记录，
不据合并动作补造人工评审或三端验收。#5 议题仍打开。

实际工时未人工登记；验收点数尚未确认，各条目「预估点数」待团队统一口径后填写。
代码、测试和文档均属于同一成果，不重复计分。C（YingboQi）的 C1–C5 条目待其完成后补录。
未形成最终绩效比例，不以代码行数或提交数推算个人成绩。

| C / YingboQi | [#9](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/9) | C1 小程序骨架 + api.js（含 CI 修复与真机联调） | 5（守则初始估算） | 已合并 develop | PR [#22](https://github.com/Yunkimo/Intelligent-Desktop-Pet/pull/22)（合并提交 ee1a638），真机实际使用验证 | 待 A/B 评审 |
| C / YingboQi | [#10](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/10) | C2 实时刷新（ws.js 适配层 + 三页订阅 + 陈旧卡片修复） | 3（守则初始估算） | 真机验收通过，PR 待合并 | PR [#25](https://github.com/Yunkimo/Intelligent-Desktop-Pet/pull/25)；适配层逻辑验收 7 项入 CI | 待 A/B 评审 |
| C / YingboQi | [#23](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/23) | 课表图片识别导入（视觉大模型 + 批量落库 + 教师字段） | 用户直接需求，点数待确认 | 已合并 develop | PR #22；用户原图 15 门识别验证 | 待 A/B 评审 |
| C / YingboQi | [#24](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/24) | 本周周次过滤（两页联动 + 置灰标注） | 用户直接需求，点数待确认 | 已合并 develop | PR #22；模拟器人工执行 | 待 A/B 评审 |
| C / YingboQi | [#11](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/11) | C3 订阅授权（subscribe.js 流程 + 表单提醒时间 + 逻辑测试） | 3（守则初始估算） | 小程序侧完成；真机链路待 B3 合并与模板配置 | 本分支提交 36edf56；PR 待建 | 依赖 B / 微信平台 |
| C / YingboQi | [#12](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/12) | C4 部署（三路线手册 + 启停/自检/重置脚本） | 5（守则初始估算） | 本地路线与自检实测通过；穿透/学生机待执行 | 提交 8d9d5d1；check_deployment 5/5 | 他人复现待执行 |
| C / YingboQi | [#13](https://github.com/Yunkimo/Intelligent-Desktop-Pet/issues/13) | C5 文档/CI/演示（JS 检查入 CI、手册与证据文档、演示脚本） | 6（守则初始估算） | CI 与文档已交付；演示视频待本人录制 | 提交 e19188e 及本批文档 | 待团队复核 |

2026-10-16 补录：C1–C4 完成度如上；实际工时未人工登记；验收点数待团队统一口径。
