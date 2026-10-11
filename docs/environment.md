# B1 验证环境

- 日期：2026-10-11（Asia/Shanghai）。
- 基线 SHA：`49944767f441b7c625cbbb48bd28bcff1c08c844`。
- 被测功能提交：`12635feeafe6f1204b33f43fd9485a4853841f75`。
- OS：Windows 11 Home China 64-bit，版本 10.0.26200。
- CPU：Intel Core i7-1165G7，8 逻辑处理器；RAM：约 15.73 GiB。
- Python：3.13.0；兼容回归使用 uv 提供的独立 CPython 3.10.22。
- 运行依赖：见 `backend/requirements.txt`；pytest 9.1.1、Ruff 0.17.0、pre-commit 4.6.2。
- 数据：每个自动化用例独立临时 SQLite；真实网络脚本每次创建 30 条日程。
- 网络：本机 IPv4 loopback，随机空闲端口；无真实客户端设备与公网代理参与收包路径。
- Uvicorn：1 worker，`websockets-sansio`，消息最大 4096 字节；凭证随机生成，不持久化。
- 超时：单连接发送 2 秒、关闭 1 秒；故障注入用例采用更短受控超时。
- 时间：事件信封 UTC；测试不测跨机器时钟误差，也不声称达到提醒端到端延迟指标。
- 依赖下载与 GitHub 访问使用本机现有代理；未更改 Git 全局代理设置。
- 当前不是另一名成员的干净部署复现；该验收仍待执行。
