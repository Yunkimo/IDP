"""语音合成：edge-tts 生成 mp3。纯 Python（播放由 UI 层用 QMediaPlayer 完成）。"""

import asyncio
import tempfile
from pathlib import Path

import edge_tts

from .config import DEFAULT_TTS_TIMEOUT_SECONDS, DEFAULT_TTS_VOICE


class TTSEngine:
    def __init__(
        self,
        voice: str = DEFAULT_TTS_VOICE,
        rate: str = "+10%",
        pitch: str = "+20Hz",
        timeout: float = DEFAULT_TTS_TIMEOUT_SECONDS,
    ) -> None:
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.timeout = timeout

    def synthesize(self, text: str) -> str:
        """把文本合成到临时 mp3 文件，返回路径。需在非异步线程里调用。"""
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()

        async def _run() -> None:
            comm = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
            await comm.save(tmp.name)

        async def bounded() -> None:
            await asyncio.wait_for(_run(), timeout=self.timeout)

        try:
            asyncio.run(bounded())
        except BaseException:
            Path(tmp.name).unlink(missing_ok=True)
            raise
        return tmp.name
