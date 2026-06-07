from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import config
import gcode
import motion_scripts
from serial_link import SerialLink, SerialLinkError, available_ports


DONE_MARKER = "__quanquan_sequence_done__"


class StageOneApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(config.APP_NAME)
        self.geometry("1040x700")
        self.minsize(900, 620)

        self.link = SerialLink()
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.busy = False

        self.mock_var = tk.BooleanVar(value=True)
        self.port_var = tk.StringVar(value=config.DEFAULT_PORT)
        self.baud_var = tk.StringVar(value=str(config.DEFAULT_BAUD_RATE))
        self.ending_var = tk.StringVar(value="CR")
        self.status_var = tk.StringVar(value="Offline mock mode")

        self.x_var = tk.StringVar(value="100")
        self.y_var = tk.StringVar(value="80")
        self.z_var = tk.StringVar(value="40")
        self.f_var = tk.StringVar(value=str(config.DEFAULT_FEED_RATE))
        self.custom_var = tk.StringVar(value="")

        self._build_style()
        self._build_ui()
        self._refresh_ports()
        self.after(80, self._drain_log_queue)

    def _build_style(self) -> None:
        self.configure(bg="#f5f7fa")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 10))
        style.configure("TFrame", background="#f5f7fa")
        style.configure("Panel.TFrame", background="#ffffff", borderwidth=1, relief="solid")
        style.configure("TLabel", background="#f5f7fa", foreground="#1f2937")
        style.configure("Panel.TLabel", background="#ffffff", foreground="#1f2937")
        style.configure("Title.TLabel", background="#f5f7fa", foreground="#102a43", font=("Segoe UI", 18, "bold"))
        style.configure("Hint.TLabel", background="#f5f7fa", foreground="#52616f")
        style.configure("TButton", padding=(12, 7), background="#e8eef5", foreground="#102a43")
        style.map("TButton", background=[("active", "#d8e6f3")])
        style.configure("Accent.TButton", background="#0f766e", foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", "#0d9488")])
        style.configure("Danger.TButton", background="#dc2626", foreground="#ffffff")
        style.map("Danger.TButton", background=[("active", "#ef4444")])
        style.configure("TCheckbutton", background="#f5f7fa", foreground="#1f2937")
        style.configure("TLabelframe", background="#ffffff", foreground="#102a43")
        style.configure("TLabelframe.Label", background="#ffffff", foreground="#102a43", font=("Segoe UI", 10, "bold"))

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill=tk.BOTH, expand=True)

        ttk.Label(root, text="quanquan 第一阶段控制台", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            root,
            text="先用离线模式跑通按钮和 G-code，实机回来后再校准 COM 口和坐标。",
            style="Hint.TLabel",
        ).pack(anchor="w", pady=(2, 14))

        main = ttk.Frame(root)
        main.pack(fill=tk.BOTH, expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # 可滚动的左侧面板
        left_canvas = tk.Canvas(left, bg="#f5f7fa", highlightthickness=0)
        left_canvas.grid(row=0, column=0, sticky="nsew")

        left_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=left_canvas.yview)
        left_scroll.grid(row=0, column=1, sticky="ns")

        self.left_inner = ttk.Frame(left_canvas)
        left_inner_window = left_canvas.create_window((0, 0), window=self.left_inner, anchor="nw", tags="inner")

        def _configure_inner(event: tk.Event) -> None:
            left_canvas.itemconfig("inner", width=event.width)

        def _configure_scroll(_event: tk.Event) -> None:
            left_canvas.configure(scrollregion=left_canvas.bbox("all"))

        def _on_mousewheel(event: tk.Event) -> None:
            left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.left_inner.bind("<Configure>", _configure_scroll)
        left_canvas.bind("<Configure>", _configure_inner)
        left_canvas.bind("<Enter>", lambda _e: left_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        left_canvas.bind("<Leave>", lambda _e: left_canvas.unbind_all("<MouseWheel>"))
        left_canvas.configure(yscrollcommand=left_scroll.set)

        self._build_connection_panel(self.left_inner)
        self._build_manual_panel(self.left_inner)
        self._build_action_panel(self.left_inner)
        self._build_log_panel(right)

    def _build_connection_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Connection", padding=12)
        frame.pack(fill=tk.X, pady=(0, 12))

        ttk.Checkbutton(frame, text="Offline mock mode", variable=self.mock_var).grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(frame, text="Port", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 2))
        self.port_combo = ttk.Combobox(frame, textvariable=self.port_var, width=16, values=[])
        self.port_combo.grid(row=2, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Refresh", command=self._refresh_ports).grid(row=2, column=1, sticky="ew")

        ttk.Label(frame, text="Baud", style="Panel.TLabel").grid(row=3, column=0, sticky="w", pady=(10, 2))
        ttk.Entry(frame, textvariable=self.baud_var, width=16).grid(row=4, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(frame, text="Line ending", style="Panel.TLabel").grid(row=3, column=1, sticky="w", pady=(10, 2))
        ttk.Combobox(frame, textvariable=self.ending_var, values=["CR", "LF", "CRLF"], state="readonly", width=8).grid(
            row=4, column=1, sticky="ew"
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        ttk.Button(buttons, text="Connect", command=self._connect, style="Accent.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(buttons, text="Disconnect", command=self._disconnect).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

        ttk.Label(frame, textvariable=self.status_var, style="Panel.TLabel").grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 0))

    def _build_manual_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Manual Move", padding=12)
        frame.pack(fill=tk.X, pady=(0, 12))

        for col, (label, var) in enumerate((("X", self.x_var), ("Y", self.y_var), ("Z", self.z_var), ("F", self.f_var))):
            ttk.Label(frame, text=label, style="Panel.TLabel").grid(row=0, column=col, sticky="w")
            ttk.Entry(frame, textvariable=var, width=8).grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 6, 0))

        ttk.Button(frame, text="Move XYZ", command=self._move_xyz, style="Accent.TButton").grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        quick = ttk.Frame(frame)
        quick.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        ttk.Button(quick, text="Home", command=lambda: self._run_commands([gcode.home()])).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(quick, text="Status", command=lambda: self._run_commands([gcode.status()])).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(quick, text="Endstops", command=lambda: self._run_commands([gcode.endstop_status()])).pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(frame, text="Custom G-code", style="Panel.TLabel").grid(row=4, column=0, columnspan=4, sticky="w", pady=(12, 2))
        ttk.Entry(frame, textvariable=self.custom_var).grid(row=5, column=0, columnspan=4, sticky="ew")
        ttk.Button(frame, text="Send Custom", command=self._send_custom).grid(row=6, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        ttk.Button(frame, text="Motors Off", command=lambda: self._run_commands([gcode.motors_off()]), style="Danger.TButton").grid(
            row=7, column=0, columnspan=4, sticky="ew", pady=(12, 0)
        )

    def _build_action_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Actions", padding=12)
        frame.pack(fill=tk.X)

        for index, (name, builder) in enumerate(motion_scripts.SCRIPTS.items()):
            row = index // 2
            col = index % 2
            ttk.Button(frame, text=name, command=lambda b=builder: self._run_script(b), style="Accent.TButton").grid(
                row=row, column=col, sticky="ew", padx=(0 if col == 0 else 8, 0), pady=(0 if row == 0 else 8, 0)
            )
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        top = ttk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="Log", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Button(top, text="Clear", command=self._clear_log).grid(row=0, column=1, sticky="e")

        log_wrap = ttk.Frame(parent, style="Panel.TFrame", padding=8)
        log_wrap.grid(row=1, column=0, sticky="nsew")
        log_wrap.rowconfigure(0, weight=1)
        log_wrap.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_wrap,
            wrap="word",
            bg="#0f172a",
            fg="#e5f4ff",
            insertbackground="#e5f4ff",
            relief="flat",
            font=("Consolas", 10),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_wrap, orient=tk.VERTICAL, command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)
        self._log("Ready. Offline mock mode is enabled.")

    def _refresh_ports(self) -> None:
        ports = available_ports()
        self.port_combo["values"] = ports
        if ports and self.port_var.get() == config.DEFAULT_PORT:
            self.port_var.set(ports[0])
        if ports:
            self._log("Available ports: " + ", ".join(ports))
        else:
            self._log("No serial ports found. Mock mode can still run.")

    def _line_ending(self) -> str:
        mapping = {"CR": "\r", "LF": "\n", "CRLF": "\r\n"}
        return mapping[self.ending_var.get()]

    def _connect(self) -> None:
        try:
            baud = int(self.baud_var.get())
            lines = self.link.connect(self.port_var.get(), baud, self._line_ending(), self.mock_var.get())
        except Exception as exc:
            self.status_var.set("Connection failed")
            self._log(f"[ERROR] {exc}")
            messagebox.showerror("Connection failed", str(exc))
            return
        self.status_var.set("Connected" if not self.link.mock else "Connected in mock mode")
        for line in lines:
            self._log(line)

    def _disconnect(self) -> None:
        for line in self.link.disconnect():
            self._log(line)
        self.status_var.set("Disconnected")

    def _move_xyz(self) -> None:
        try:
            command = gcode.move(float(self.x_var.get()), float(self.y_var.get()), float(self.z_var.get()), float(self.f_var.get()))
        except Exception as exc:
            self._log(f"[ERROR] {exc}")
            messagebox.showerror("Invalid move", str(exc))
            return
        self._run_commands([gcode.absolute(), command])

    def _send_custom(self) -> None:
        command = self.custom_var.get().strip()
        if not command:
            return
        self._run_commands([command])

    def _run_script(self, builder) -> None:
        try:
            commands = builder()
        except Exception as exc:
            self._log(f"[ERROR] {exc}")
            messagebox.showerror("Action failed", str(exc))
            return
        self._run_commands(commands)

    def _run_commands(self, commands: list[str]) -> None:
        if self.busy:
            self._log("[BUSY] Wait for the current command sequence to finish.")
            return
        if not self.link.connected:
            self._connect()
            if not self.link.connected:
                return

        self.busy = True
        thread = threading.Thread(target=self._send_worker, args=(commands,), daemon=True)
        thread.start()

    def _send_worker(self, commands: list[str]) -> None:
        try:
            for command in commands:
                result = self.link.send_line(command)
                for line in result.lines:
                    self.log_queue.put(line)
        except SerialLinkError as exc:
            self.log_queue.put(f"[ERROR] {exc}")
        except Exception as exc:
            self.log_queue.put(f"[ERROR] Unexpected: {exc}")
        finally:
            self.log_queue.put(DONE_MARKER)

    def _drain_log_queue(self) -> None:
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            if line == DONE_MARKER:
                self.busy = False
                self._log("[DONE]")
                continue
            self._log(line)
        self.after(80, self._drain_log_queue)

    def _log(self, message: str) -> None:
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def _clear_log(self) -> None:
        self.log_text.delete("1.0", tk.END)


if __name__ == "__main__":
    app = StageOneApp()
    app.mainloop()
