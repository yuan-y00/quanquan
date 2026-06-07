"""
电脑扬声器播放英文回应。
使用 pyttsx3（离线 Windows SAPI5），不需要网络。
"""

from __future__ import annotations

import sys
import threading
from typing import Optional

from voice_config import TTS_ENGINE, TTS_RATE, TTS_VOLUME

# 动作名 → 回应文本
RESPONSES: dict[str, str] = {
    "wake": "I am here.",
    "handshake": "Okay, hand please.",
    "again": "Again!",
    "happy": "Hehe.",
    "shy": "Oh no.",
    "sleep": "Good night.",
    "unknown": "I don't understand.",
    "greeting": "Hi! I am quanquan.",
    "confused": "I'm not sure what you mean.",
}

_engine = None
_lock = threading.Lock()
_import_error: Optional[str] = None


def _import_pyttsx3():
    """惰性导入 pyttsx3。"""
    global _import_error
    if "pyttsx3" not in sys.modules:
        try:
            import pyttsx3  # type: ignore
        except ImportError as exc:
            _import_error = str(exc)
            return None
    import pyttsx3  # type: ignore
    return pyttsx3


def _get_engine():
    """延迟初始化 TTS 引擎（单例）。"""
    global _engine, _import_error
    if _engine is not None:
        return _engine
    if _import_error is not None:
        return None
    with _lock:
        if _engine is not None:
            return _engine
        if _import_error is not None:
            return None
        try:
            mod = _import_pyttsx3()
            if mod is None:
                _import_error = _import_error or "pyttsx3 not installed"
                return None
            engine = mod.init(driverName=TTS_ENGINE)
            engine.setProperty("rate", TTS_RATE)
            engine.setProperty("volume", TTS_VOLUME)
            _engine = engine
        except Exception as exc:
            _import_error = str(exc)
            return None
    return _engine


def is_tts_available() -> bool:
    return _get_engine() is not None


def get_tts_error() -> Optional[str]:
    _get_engine()
    return _import_error


def speak(text: str) -> None:
    """同步朗读（会阻塞当前线程直到读完）。"""
    engine = _get_engine()
    if engine is None:
        print(f"[TTS unavailable] Would say: {text}")
        return
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def speak_async(text: str) -> None:
    """异步朗读，不阻塞调用者。"""
    threading.Thread(target=speak, args=(text,), daemon=True).start()


def say_response(action_name: str) -> None:
    """根据动作名播放对应的回应句子。"""
    text = RESPONSES.get(action_name, RESPONSES["unknown"])
    speak_async(text)


def cleanup() -> None:
    global _engine
    if _engine is not None:
        try:
            _engine.stop()
        except Exception:
            pass
        _engine = None
