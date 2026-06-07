"""
语音互动主控制器 —— 后台线程：监听→匹配→说话→发 G-code。
通过 queue 与 UI 线程通信，不阻塞界面。
"""

from __future__ import annotations

import queue
import sys
import threading
from pathlib import Path
from typing import Optional

# ── Solution B：父目录加入 sys.path，stage1 作为包引用 ──
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

_STAGE1 = _PARENT / "stage1_pc_controller"
if str(_STAGE1) not in sys.path:
    sys.path.append(str(_STAGE1))

# stage1 复用模块
from stage1_pc_controller.serial_link import SerialLink  # noqa: E402
from stage1_pc_controller.motion_scripts import SCRIPTS  # noqa: E402

# intent.py 返回小写 action name（如 "shy"），SCRIPTS 的 key 是首字母大写
_SCRIPTS_LOWER = {k.lower(): k for k in SCRIPTS}
# { "wake": "Wake", "handshake": "Handshake", "happy": "Happy", "shy": "Shy", "sleep": "Sleep" }

# "again" 没有独立 script，语义上就是再握一次手
_ALIASES: dict[str, str] = {"again": "handshake"}

# stage2 本地模块
from voice_config import LISTEN_RETRIES, LISTEN_TIMEOUT, PHRASE_TIME_LIMIT  # noqa: E402
from speech_out import speak, is_tts_available, get_tts_error, RESPONSES  # noqa: E402
from intent import match  # noqa: E402
from voice import listen_once, is_microphone_available, get_model_error  # noqa: E402


class VoiceController:
    """后台语音控制器。"""

    def __init__(self, link: SerialLink, log_queue: queue.Queue[str]) -> None:
        self._link = link
        self._log_queue = log_queue
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.status = "Stopped"
        self.last_heard = ""
        self.last_reply = ""

    # ── 公开接口 ──────────────────────────────────────────

    def start(self) -> None:
        if self._running:
            return

        if not is_microphone_available():
            self._emit(
                "No microphone detected. Check Windows privacy settings."
            )
            self.status = "No microphone"
            return

        err = get_model_error()
        if err:
            self._emit(f"[VOICE] Vosk model error: {err}")
            self._emit("[VOICE] Run: python setup_models.py download")
            self.status = "Model missing"
            return

        if not is_tts_available():
            self._emit(f"[VOICE] TTS unavailable: {get_tts_error()}")
            self._emit("[VOICE] Will still listen, but no spoken replies.")

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._emit("[VOICE] Listening (offline Vosk). Speak now.")

    def stop(self) -> None:
        self._running = False
        self.status = "Stopped"
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._emit("[VOICE] Stopped.")

    # ── 主循环 ─────────────────────────────────────────────

    def _loop(self) -> None:
        while self._running:
            self.status = "Listening..."
            text: Optional[str] = None
            last_error = ""

            for _ in range(LISTEN_RETRIES + 1):
                recognized, error = listen_once(
                    timeout=LISTEN_TIMEOUT,
                    phrase_time_limit=PHRASE_TIME_LIMIT,
                )
                if recognized:
                    text = recognized
                    break
                if error:
                    last_error = error
                self._running and threading.Event().wait(0.3)

            if not self._running:
                return

            if text is None:
                if last_error == "timeout":
                    pass  # 没人说话，静默继续监听
                elif last_error == "unintelligible":
                    self._emit("[VOICE] Heard sound but couldn't understand.")
                    self._handle_fallback()
                elif last_error:
                    self._emit(f"[VOICE] {last_error}")
                self.status = "Idle"
                continue

            self.last_heard = text
            self._emit(f'[HEARD] "{text}"')

            result = match(text)
            if result is None:
                self._emit(f'[VOICE] No command matched: "{text}"')
                self._handle_fallback()
                continue

            action_name, response = result
            self.last_reply = response
            self.status = f"Acting: {action_name}"

            self._emit(f'[VOICE] Matched: {action_name}')

            # ── 先发 G-code，再同步播放语音 ──
            # 同步 speak() 会阻塞直到 TTS 说完，
            # 之后回到 listen_once() 打开 PyAudio，不会抢占音频设备。
            if action_name == "greeting":
                speak(response)
            else:
                script_action = _ALIASES.get(action_name, action_name)
                script_key = _SCRIPTS_LOWER.get(script_action.lower())
                if script_key:
                    self._execute_script(script_key)
                speak(response)

            self.status = "Idle"
            self._emit("[VOICE] Done. Listening...")

    # ── 听不懂兜底：统一做 happy ────────────────────────────

    def _handle_fallback(self) -> None:
        """听不懂时做 happy 动作 + 说 Hehe. 同步阻塞直到说完。"""
        self.last_reply = RESPONSES["happy"]
        self.status = "Acting: happy (fallback)"

        self._emit('[VOICE] Fallback → happy')
        self._execute_script("Happy")
        speak(RESPONSES["happy"])

    # ── G-code 执行 ────────────────────────────────────────

    def _execute_script(self, action_name: str) -> None:
        try:
            commands = SCRIPTS[action_name]()
        except Exception as exc:
            self._emit(f"[VOICE ERROR] Script '{action_name}': {exc}")
            return

        if not self._link.connected:
            self._emit("[VOICE] Not connected. Skipping movement.")
            return

        self._emit(
            f"[VOICE] Sending '{action_name}' ({len(commands)} commands)..."
        )
        for command in commands:
            try:
                result = self._link.send_line(command)
                for line in result.lines:
                    self._emit(line)
            except Exception as exc:
                self._emit(f"[VOICE ERROR] {exc}")
                break

    def _emit(self, message: str) -> None:
        try:
            self._log_queue.put_nowait(message)
        except Exception:
            pass
