# 测试文档

## 1. 测试策略

按「纯逻辑 → 无界面 UI → mock 隔离外部依赖」分层：

- **纯逻辑单测**：配置、记忆、人设、气泡折行等无副作用逻辑，直接断言。
- **无界面 Qt 测试**：通过 `QT_QPA_PLATFORM=offscreen` 在无显示环境跑 Qt 组件。
- **mock 隔离网络**：LLM 提供者用假客户端替换，验证流式拼接、回调与异常包装，不真正联网。

真实网络（LLM/TTS）与硬件（麦克风/whisper 模型）由 `scripts/smoke_test.py` 与人工验证覆盖，不进入自动化单测。

## 2. 运行方式

```bash
pip install -r requirements-dev.txt
ruff check .          # 静态检查
pytest                # 自动化测试
```

CI（GitHub Actions）在每次 push/PR 自动执行上述两步。

## 3. 测试用例清单

| 文件 | 覆盖点 | 用例数 |
|---|---|---|
| `test_config.py` | 配置默认值、环境变量覆盖、config.json 字段（含健康项） | 3 |
| `test_memory.py` | 增删顺序、轮数裁剪、持久化往返 | 4 |
| `test_persona.py` | 人设提示词包含名字/性格/语气 | 1 |
| `test_providers.py` | 流式拼接与回调、异常包装、tool_calls 回传字段 | 4 |
| `test_bubble.py` | 折行纯函数（空/超长/换行）、气泡流式追加 | 4 |
| `test_agent.py` | 工具循环次数上限、最终流式回复 | 3 |
| `test_backend_client.py` | REST 封装、绕过系统代理、WsListener | 5 |
| `test_tools.py` | 工具注册表 schema 与调度 | 5 |
| `test_health.py` | 久坐阈值、离座清零、周期重复、在座判定 | 6 |
| `test_ws_listener.py` | WebSocket 消息解析、重连、事件分发 | 6 |
| `test_hotkey.py` | 快捷键注册与触发 | 8 |
| `test_image_utils.py` | 图片缩放/裁剪纯函数 | 5 |
| `test_live2d.py` | Live2D 视图边界 | 2 |

合计 **56 个用例**，全部通过。

## 4. 实验环境

| 项 | 值 |
|---|---|
| OS | Windows 11 Home（开发）/ Ubuntu latest（CI） |
| Python | 3.14.5（开发）/ 3.12（CI） |
| 关键依赖 | PyQt6 6.11、openai 3.13、edge-tts 7.2、faster-whisper 1.2 |
| 测试框架 | pytest 8+，`QT_QPA_PLATFORM=offscreen` |

## 5. 结果

```
56 passed（无失败）
ruff check . → All checks passed!
行覆盖率 32%（pet/ 共 1598 语句、513 覆盖）：providers 97%、memory 93%、health 60%、tools 60%；
window/sprite/worker/tts/对话框等 Qt 界面层为 0%，按 §1 策略由 smoke 脚本 + 人工验证覆盖，不做无头 UI 自动化。
```
