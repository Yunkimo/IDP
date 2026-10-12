"""语音请求失败和超时不遗留临时音频。"""

import asyncio
from pathlib import Path

import pytest

from pet.tts import TTSEngine


@pytest.mark.parametrize("mode", ["success", "failure", "timeout"])
def test_synthesis_lifecycle(tmp_path, monkeypatch, mode):
    import pet.tts as tts

    original = tts.tempfile.NamedTemporaryFile
    monkeypatch.setattr(
        tts.tempfile, "NamedTemporaryFile", lambda **kw: original(dir=tmp_path, **kw)
    )

    class Communicate:
        def __init__(self, *args, **kwargs):
            pass

        async def save(self, path):
            Path(path).write_bytes(b"partial audio")
            if mode == "failure":
                raise RuntimeError("upstream failure")
            if mode == "timeout":
                await asyncio.Event().wait()

    monkeypatch.setattr(tts.edge_tts, "Communicate", Communicate)
    engine = TTSEngine(timeout=0.02)
    if mode == "success":
        result = Path(engine.synthesize("test"))
        assert result.read_bytes() == b"partial audio"
    else:
        with pytest.raises(RuntimeError if mode == "failure" else asyncio.TimeoutError):
            engine.synthesize("test")
        assert list(tmp_path.glob("*.mp3")) == []
