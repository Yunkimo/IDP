"""语音合成：edge-tts 生成 mp3。纯 Python（播放由 UI 层用 QMediaPlayer 完成）。"""

import asyncio
import tempfile

import edge_tts


class TTSEngine:
    def __init__(
        self, voice: str = "zh-CN-XiaoyouNeural", rate: str = "+10%", pitch: str = "+20Hz"
    ) -> None:
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    def synthesize(self, text: str) -> str:
        """把文本合成到临时 mp3 文件，返回路径。需在非异步线程里调用。"""
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()

        async def _run() -> None:
            comm = edge_tts.Communicate(text, self.voice, rate=self.rate, pitch=self.pitch)
            await comm.save(tmp.name)

        asyncio.run(_run())
        return tmp.name
