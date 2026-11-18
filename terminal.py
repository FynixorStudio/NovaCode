"""Panel terminal terintegrasi (cmd / PowerShell) dengan thread aman."""

from __future__ import annotations

import base64
import os
import queue
import re
import subprocess
import threading
import tkinter as tk

import customtkinter as ctk

from . import icons
from .config import COLORS, FONT_MONO_TUPLE, FONT_UI_TUPLE

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class TerminalPanel(ctk.CTkFrame):
    def __init__(self, master, cwd: str | None = None, on_output=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], corner_radius=0, **kwargs)
        self.cwd = cwd or os.path.expanduser("~")
        self.shell = "cmd"
        self.proc: subprocess.Popen | None = None
        self.queue: queue.Queue = queue.Queue()
        self.running = False
        self.history: list[str] = []
        self._history_idx = 0
        self.on_output = on_output
        self._running_cmd = ""
        self._current_output: list[str] = []

        self._build_ui()
        self._banner()
        self.after(60, self._drain)

    # ------------------------------------------------------------------
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg"], height=30,
                              corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="TERMINAL", font=("Segoe UI", 10, "bold"),
                     text_color=COLORS["muted"], anchor="w").pack(side="left", padx=10)

        self.shell_menu = ctk.CTkOptionMenu(
            header, values=["cmd", "powershell"], command=self._set_shell,
            width=100, height=22, font=FONT_UI_TUPLE,
            fg_color=COLORS["bg_light"], button_color=COLORS["bg_lighter"],
            button_hover_color=COLORS["bg_lighter"], text_color=COLORS["text"],
        )
        self.shell_menu.pack(side="right", padx=4)

        ctk.CTkButton(header, text="Clear", image=icons.ctk_icon("trash", COLORS["muted"], 14),
                      compound="left", width=68, height=22, corner_radius=4,
                      fg_color="transparent", hover_color=COLORS["bg_light"],
                      text_color=COLORS["muted"], font=FONT_UI_TUPLE,
                      command=self.clear).pack(side="right", padx=2)
        ctk.CTkButton(header, text="", image=icons.ctk_icon("stop", COLORS["red"], 12),
                      width=26, height=22, corner_radius=4,
                      fg_color="transparent", hover_color=COLORS["red_soft"],
                      command=self.stop).pack(side="right", padx=2)

        self.output = tk.Text(
            self, wrap="word", bg=COLORS["bg_deep"], fg=COLORS["text"],
            font=FONT_MONO_TUPLE, relief="flat", bd=0, padx=10, pady=6,
            insertbackground=COLORS["text"], highlightthickness=0,
            selectbackground=COLORS["selection"], state="disabled",
        )

        self.output.tag_configure("prompt", foreground=COLORS["green"])
        self.output.tag_configure("info", foreground=COLORS["cyan"])
        self.output.tag_configure("error", foreground=COLORS["red"])

        # Scrollbar kelihatan jelas, jadi geser atas/bawah nggak cuma mengandalkan wheel 🗿
        self.scrollbar = tk.Scrollbar(
            self, command=self.output.yview, bg=COLORS["bg_light"],
            troughcolor=COLORS["bg_deep"], activebackground=COLORS["accent"],
            highlightthickness=0,
        )
        self.output.configure(yscrollcommand=self.scrollbar.set)

        # Pakai tk.Frame biasa dengan tinggi eksplisit: CTkFrame tidak
        # menghormati pack_propagate(False) sehingga baris input menyusut 1px.
        entry_frame = tk.Frame(self, bg=COLORS["bg_deep"], height=38)
        entry_frame.pack(fill="x", side="bottom")
        entry_frame.pack_propagate(False)

        self.prompt_label = tk.Label(
            entry_frame, text=self._prompt(), bg=COLORS["bg_deep"],
            fg=COLORS["green"], font=FONT_MONO_TUPLE, anchor="w",
        )
        self.prompt_label.pack(side="left", padx=(10, 0), pady=5)

        self.entry = tk.Entry(
            entry_frame, bg=COLORS["bg_deep"], fg=COLORS["text_bright"],
            insertbackground=COLORS["text_bright"], font=FONT_MONO_TUPLE,
            relief="flat", bd=0, highlightthickness=0,
        )
        self.entry.pack(fill="x", side="left", expand=True, pady=5)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Up>", self._history_up)
        self.entry.bind("<Down>", self._history_down)
        self.entry.bind("<Control-c>", lambda e: self.stop())

        # Output di-pack PALING TERAKHIR supaya baris input lebih dulu
        # mendapat porsi tinggi; kalau tidak, expand=True mengambil semua
        # ruang dan input menyusut menjadi 1px.
        self.scrollbar.pack(side="right", fill="y")
        self.output.pack(side="left", fill="both", expand=True)

    # ------------------------------------------------------------------
    def _prompt(self) -> str:
        short = self.cwd if len(self.cwd) < 48 else "..." + self.cwd[-45:]
        return f"{short}> "

    def _set_shell(self, value: str):
        self.shell = value

    def _banner(self):
        self._write("NovaCode Terminal — ketik 'help' untuk bantuan.\n", "info")
        self._write(f"Shell: {self.shell} | Folder: {self.cwd}\n", "info")

    def set_cwd(self, path: str):
        if path and os.path.isdir(path):
            self.cwd = path
            self.prompt_label.configure(text=self._prompt())

    # ------------------------------------------------------------------
    def _write(self, text: str, tag: str | None = None):
        self.output.configure(state="normal")
        if tag:
            self.output.insert("end", text, tag)
        else:
            self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def focus(self):
        self.entry.focus_set()

    # ------------------------------------------------------------------
    def _on_enter(self, event=None):
        cmd = self.entry.get().strip()
        self.entry.delete(0, "end")
        if not cmd:
            return
        self.history.append(cmd)
        self._history_idx = len(self.history)
        self.execute(cmd)

    def _history_up(self, event=None):
        if not self.history:
            return
        self._history_idx = max(0, self._history_idx - 1)
        self.entry.delete(0, "end")
        self.entry.insert(0, self.history[self._history_idx])
        return "break"

    def _history_down(self, event=None):
        if not self.history:
            return
        self._history_idx = min(len(self.history), self._history_idx + 1)
        self.entry.delete(0, "end")
        if self._history_idx < len(self.history):
            self.entry.insert(0, self.history[self._history_idx])
        return "break"

    def send_command(self, cmd: str):
        """Dipakai tombol Run / fitur lain untuk mengirim perintah."""
        self.entry.delete(0, "end")
        self.entry.insert(0, cmd)
        self._on_enter()

    # ------------------------------------------------------------------
    def execute(self, cmd: str):
        if self.running:
            self._write("Perintah masih berjalan. Tekan ■ untuk menghentikan.\n", "error")
            return

        self._write(f"{self._prompt()}{cmd}\n", "prompt")
        lower = cmd.lower().strip()

        if lower in ("cls", "clear"):
            self.clear()
            return
        if lower == "help":
            self._write("Perintah bawaan: cd, cls, clear, exit, help\n"
                        "Selain itu semua perintah cmd/PowerShell didukung.\n", "info")
            return
        if lower == "exit":
            self._write("Ketik perintah lain atau tutup panel terminal.\n", "info")
            return

        m = re.match(r"^cd(?:\s+(.*))?$", cmd, re.IGNORECASE)
        if m:
            arg = (m.group(1) or "").strip().strip('"')
            target = self.cwd if not arg else (
                arg if os.path.isabs(arg) else os.path.join(self.cwd, arg))
            if os.path.isdir(target):
                self.cwd = os.path.abspath(target)
                self.prompt_label.configure(text=self._prompt())
            else:
                self._write(f"Folder tidak ditemukan: {arg}\n", "error")
            return

        if self.shell == "powershell":
            # EncodedCommand menghindari masalah escape tanda kutip di Windows
            encoded = base64.b64encode(
                ("& { " + cmd + " }").encode("utf-16le")).decode("ascii")
            args = ["powershell", "-NoProfile", "-EncodedCommand", encoded]
            shell = False
        else:
            # shell=True -> cmd.exe menerima string perintah apa adanya
            # (tanda kutip pada path tidak di-escape oleh list2cmdline)
            args = cmd
            shell = True

        try:
            self.proc = subprocess.Popen(
                args, shell=shell, cwd=self.cwd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, errors="replace",
                bufsize=1, creationflags=NO_WINDOW,
            )
        except OSError as exc:
            self._write(f"Gagal menjalankan: {exc}\n", "error")
            return

        self.running = True
        self._running_cmd = cmd
        self._current_output = []
        self.entry.configure(state="disabled")
        threading.Thread(target=self._reader, args=(self.proc,), daemon=True).start()

    def _reader(self, proc: subprocess.Popen):
        try:
            for line in proc.stdout:
                self.queue.put(("out", line))
        except Exception as exc:
            self.queue.put(("err", f"{exc}\n"))
        finally:
            self.queue.put(("done", proc.wait()))

    def _drain(self):
        try:
            while True:
                kind, value = self.queue.get_nowait()
                if kind == "out":
                    self._write(value)
                    self._current_output.append(value)
                elif kind == "err":
                    self._write(value, "error")
                    self._current_output.append(value)
                elif kind == "done":
                    if self.running:
                        self.running = False
                        self.entry.configure(state="normal")
                        if value != 0:
                            self._write(f"[exit code {value}]\n", "error")
                        self.entry.focus_set()
                        if self.on_output:
                            try:
                                self.on_output(self._running_cmd,
                                               "".join(self._current_output), value)
                            except Exception:
                                pass
                    self.proc = None
        except queue.Empty:
            pass
        self.after(60, self._drain)

    def stop(self):
        if self.proc and self.running:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self._write("\n[proses dihentikan]\n", "error")
