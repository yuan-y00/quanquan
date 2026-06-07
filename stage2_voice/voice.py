"""
麦克风录音 + 离线语音识别（Vosk 引擎）。
完全离线运行，无需任何网络连接。
"""

from __future__ import annotations

import json
import time
from typing import Any, Optional

import pyaudio  # type: ignore

_model: Any = None
_import_error: Optional[str] = None


def _get_model():
    """延迟加载 Vosk 模型（单例，~67MB，只加载一次到内存）。"""
    global _model, _import_error
    if _model is not None:
        return _model
    if _import_error is not None:
        return None

    from voice_config import VOSK_MODEL_NAME

    try:
        import vosk  # type: ignore
    except ImportError as exc:
        _import_error = f"vosk not installed: {exc}"
        return None

    try:
        model = vosk.Model(model_name=VOSK_MODEL_NAME, lang="en-us")
        _model = model
    except Exception as exc:
        _import_error = f"Failed to load Vosk model '{VOSK_MODEL_NAME}': {exc}"
        return None

    return _model


def is_microphone_available() -> bool:
    """检查默认麦克风是否可用。"""
    try:
        p = pyaudio.PyAudio()
        info = p.get_default_input_device_info()
        p.terminate()
        return info is not None
    except (OSError, Exception):
        return False


def get_model_error() -> Optional[str]:
    """如果模型加载失败，返回错误原因。"""
    _get_model()
    return _import_error


def listen_once(
    timeout: float | None = None,
    phrase_time_limit: float | None = None,
) -> tuple[Optional[str], Optional[str]]:
    """
    用默认麦克风监听一次，Vosk 本地离线识别。

    Returns
    -------
    (recognized_text, error_reason)
        - 成功: ("shake hand", None)
        - 超时没声音: (None, "timeout")
        - 声音听不懂: (None, "unintelligible")
        - 麦克风/模型错误: (None, str(exc))
    """
    from voice_config import VOSK_SAMPLE_RATE

    model = _get_model()
    if model is None:
        return (None, f"vosk_unavailable: {_import_error}")

    import vosk  # type: ignore

    rec = vosk.KaldiRecognizer(model, VOSK_SAMPLE_RATE)
    rec.SetWords(False)

    audio = pyaudio.PyAudio()
    try:
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=VOSK_SAMPLE_RATE,
            input=True,
            frames_per_buffer=4000,
        )
    except OSError as exc:
        audio.terminate()
        return (None, f"mic_error: {exc}")

    stream.start_stream()
    start_time = time.monotonic()

    try:
        while True:
            elapsed = time.monotonic() - start_time

            try:
                data = stream.read(4000, exception_on_overflow=False)
            except OSError:
                return (None, "mic_error: stream read failed")

            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").strip()
                if text:
                    return (text, None)
                return (None, "unintelligible")

            # 超时检查
            if phrase_time_limit is not None and elapsed > phrase_time_limit:
                partial = json.loads(rec.PartialResult())
                text = partial.get("partial", "").strip()
                if text:
                    return (text, None)
                return (None, "timeout")

            if timeout is not None and elapsed > timeout:
                return (None, "timeout")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()
