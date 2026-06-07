"""
quanquan 第二阶段应用 —— 语音互动。
继承阶段一的 StageOneApp，增加 Voice Control 面板。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# — Solution B：父目录加入 sys.path，stage1 作为包引用 —
_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

_STAGE1 = _PARENT / "stage1_pc_controller"
# stage1 目录 append 到末尾，确保 stage1 内部裸 import（如 import config）
# 能找到自己的模块，不会先找到 stage2 的同名文件
if str(_STAGE1) not in sys.path:
    sys.path.append(str(_STAGE1))

# stage1 的 app.py 和 stage2 的 app.py 同名，用 importlib 按路径加载避免冲突
_spec = importlib.util.spec_from_file_location(
    "stage1_app", str(_STAGE1 / "app.py")
)
_stage1_app = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_stage1_app)
StageOneApp = _stage1_app.StageOneApp

import tkinter as tk
from tkinter import ttk

from voice_controller import VoiceController


class VoiceApp(StageOneApp):
    """阶段二：阶段一全部功能 + 语音控制面板。"""

    def __init__(self) -> None:
        super().__init__()
        self.voice_ctrl: VoiceController | None = None
        self.voice_status_var = tk.StringVar(value="Stopped")
        self.voice_heard_var = tk.StringVar(value="—")
        self.voice_reply_var = tk.StringVar(value="—")

        self._build_voice_panel(self.left_inner)

    # ── 语音面板 UI ────────────────────────────────────────

    def _build_voice_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Voice Control", padding=12)
        frame.pack(fill=tk.X, pady=(12, 0))

        # 麦克风状态
        row1 = ttk.Frame(frame)
        row1.pack(fill=tk.X)
        ttk.Label(row1, text="Microphone:", style="Panel.TLabel").pack(
            side=tk.LEFT
        )
        ttk.Label(
            row1,
            textvariable=self.voice_status_var,
            style="Panel.TLabel",
            foreground="#0f766e",
        ).pack(side=tk.LEFT, padx=(6, 0))

        # 最近听到
        row2 = ttk.Frame(frame)
        row2.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(row2, text="Last heard:", style="Panel.TLabel").pack(
            side=tk.LEFT
        )
        ttk.Label(
            row2,
            textvariable=self.voice_heard_var,
            style="Panel.TLabel",
            wraplength=200,
        ).pack(side=tk.LEFT, padx=(6, 0))

        # 最近回复
        row3 = ttk.Frame(frame)
        row3.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(row3, text="Last reply:", style="Panel.TLabel").pack(
            side=tk.LEFT
        )
        ttk.Label(
            row3,
            textvariable=self.voice_reply_var,
            style="Panel.TLabel",
            wraplength=200,
        ).pack(side=tk.LEFT, padx=(6, 0))

        # 口令提示
        hint = ttk.Frame(frame)
        hint.pack(fill=tk.X, pady=(12, 0))
        ttk.Label(
            hint,
            text=(
                'Say: "Quanquan, wake up"\n'
                '"Shake hand" / "Again"\n'
                '"Good boy" / "Be shy" / "Sleep"'
            ),
            style="Hint.TLabel",
            font=("Segoe UI", 9),
        ).pack(anchor="w")

        # 按钮
        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(
            btns,
            text="Start Voice",
            command=self._start_voice,
            style="Accent.TButton",
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(
            btns,
            text="Stop Voice",
            command=self._stop_voice,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

    # ── 语音控制 ────────────────────────────────────────────

    def _start_voice(self) -> None:
        if self.voice_ctrl is None:
            self.voice_ctrl = VoiceController(self.link, self.log_queue)
        self.voice_ctrl.start()
        self._log("[VOICE] Voice control started. Speak in English.")
        self._poll_voice_status()

    def _stop_voice(self) -> None:
        if self.voice_ctrl is not None:
            self.voice_ctrl.stop()
        self.voice_status_var.set("Stopped")

    def _poll_voice_status(self) -> None:
        if self.voice_ctrl is None or not self.voice_ctrl._running:
            self.voice_status_var.set("Stopped")
            return

        self.voice_status_var.set(self.voice_ctrl.status)
        if self.voice_ctrl.last_heard:
            self.voice_heard_var.set(self.voice_ctrl.last_heard)
        if self.voice_ctrl.last_reply:
            self.voice_reply_var.set(self.voice_ctrl.last_reply)

        self.after(100, self._poll_voice_status)


if __name__ == "__main__":
    app = VoiceApp()
    app.mainloop()
