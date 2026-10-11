# 用户手册

## 1. 系统要求

- Windows 10/11
- Python 3.10+（开发环境为 3.14）
- 麦克风（语音输入用）
- 可访问 DeepSeek（或其它 OpenAI 兼容 API）的网络

## 2. 安装

### 2.1 一键安装

双击 `setup.bat`，脚本会自动创建虚拟环境 `.venv` 并安装依赖。

或手动执行：

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 配置密钥

```bash
copy .env.example .env
```

编辑 `.env`：

```
LLM_API_KEY=sk-你的密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat
```

> 若用通义/智谱等其它 OpenAI 兼容服务，改 `LLM_BASE_URL` 与 `LLM_MODEL` 即可。

## 3. 运行

双击 `启动桌宠.bat`，或在命令行执行：

```bash
.venv\Scripts\python main.py
```

宠物会出现在桌面右下角。

> 首次使用语音识别会自动下载 faster-whisper 模型（约 100~500 MB）。若下载缓慢，先执行 `set HF_ENDPOINT=https://hf-mirror.com` 再运行。

## 4. 使用说明

| 操作 | 效果 |
|---|---|
| 按住宠物拖动 | 移动位置 |
| 点击宠物 | 唤出 / 收起输入框 |
| 输入文字后回车 | 发送，宠物流式回复并语音播报 |
| 点输入框右侧 🎤 | 开始录音（变 ⏹）；再点停止，转写后发送 |
| 按 Esc | 收起输入框 |

- 回复以气泡流式显示，同时用语音播报。
- 对话历史保存在 `data/history.json`，重启后仍在。

## 5. 自定义

所有非敏感配置在 `config.json`：

```jsonc
{
  "pet_name": "小萌",            // 宠物名字
  "persona": { "personality": "…", "tone": "…" },  // 人设
  "frames": ["idle_0.png"],       // 形象帧（见 assets/README.md）
  "sprite_size": 180,
  "tts_voice": "zh-CN-XiaoyouNeural",  // 音色
  "tts_rate": "+10%", "tts_pitch": "+20Hz",
  "whisper_model": "base",        // 识别精度：base/small/medium
  "enable_voice": true,           // 关闭语音播报
  "max_history": 20               // 记忆轮数
}
```

## 6. 常见问题

| 现象 | 处理 |
|---|---|
| 启动提示未配置 LLM_API_KEY | 按 2.2 填 `.env` 后重启 |
| 语音识别没反应 | 确认麦克风权限已允许、whisper 模型已下载 |
| 回复乱码/报错 | 检查 `.env` 密钥与 base_url 是否可达 |
| 想换宠物形象 | 图片放入 `assets/` 并更新 `frames` |
