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
| `test_config.py` | 配置默认值、环境变量覆盖、config.json 字段 | 3 |
| `test_memory.py` | 增删顺序、轮数裁剪、持久化往返 | 3 |
| `test_persona.py` | 人设提示词包含名字/性格/语气 | 1 |
| `test_providers.py` | 流式拼接与回调、异常包装为 LLMError、工厂类型 | 3 |
| `test_bubble.py` | 折行纯函数（空/超长/换行）、气泡流式追加 | 4 |

合计 **14 个用例**，全部通过。

## 4. 实验环境

| 项 | 值 |
|---|---|
| OS | Windows 11 Home（开发）/ Ubuntu latest（CI） |
| Python | 3.14.5（开发）/ 3.12（CI） |
| 关键依赖 | PyQt6 6.11、openai 3.13、edge-tts 7.2、faster-whisper 1.2 |
| 测试框架 | pytest 8+，`QT_QPA_PLATFORM=offscreen` |

## 5. 结果

```
14 passed in 2.09s
ruff check . → All checks passed!
```
