"""Command palette (Ctrl+Shift+P) ala VSCode."""

from __future__ import annotations

import customtkinter as ctk

from .config import COLORS, FONT_UI_TUPLE


class CommandPalette(ctk.CTkToplevel):
    def __init__(self, master, commands: list[dict]):
        super().__init__(master)
        self.commands = commands
        self.filtered = list(commands)
        self.selected = 0
        self.buttons = []

        self.title("Command Palette")
        self.overrideredirect(True)
        self.transient(master)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORS["bg"])

        width, height = 620, 420
        x = master.winfo_rootx() + (master.winfo_width() - width) // 2
        y = master.winfo_rooty() + 80
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

        self.entry = ctk.CTkEntry(
            self, placeholder_text="Ketik perintah... (Ctrl+Shift+P)",
            font=("Segoe UI", 13), height=38, corner_radius=0,
            fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
            border_width=1, text_color=COLORS["text"],
        )
        self.entry.pack(fill="x", padx=8, pady=(8, 4))
        self.entry.focus_set()
        self.entry.bind("<KeyRelease>", self._filter)
        self.entry.bind("<Return>", lambda e: self._execute())
        self.entry.bind("<Escape>", lambda e: self.destroy())
        self.entry.bind("<Up>", lambda e: self._move(-1))
        self.entry.bind("<Down>", lambda e: self._move(1))

        self.list_frame = ctk.CTkScrollableFrame(
            self, fg_color=COLORS["bg_deep"], corner_radius=0,
        )
        self.list_frame.pack(fill="both", expand=True, padx=8, pady=(2, 8))
        self._render()

    # ------------------------------------------------------------------
    def _filter(self, event=None):
        query = self.entry.get().strip().lower()
        self.filtered = [
            c for c in self.commands
            if query in c["title"].lower() or query in c.get("hint", "").lower()
        ]
        self.selected = 0
        self._render()

    def _render(self):
        for b in self.buttons:
            b.destroy()
        self.buttons.clear()
        for idx, cmd in enumerate(self.filtered[:60]):
            text = cmd["title"]
            if cmd.get("shortcut"):
                text += f"    {cmd['shortcut']}"
            btn = ctk.CTkButton(
                self.list_frame, text=text, anchor="w", height=34,
                font=FONT_UI_TUPLE, corner_radius=4,
                fg_color=COLORS["accent_soft"] if idx == self.selected else "transparent",
                hover_color=COLORS["bg_light"],
                text_color=COLORS["text_bright"] if idx == self.selected else COLORS["text"],
                command=lambda c=cmd: self._execute(c),
            )
            btn.pack(fill="x", pady=1)
            self.buttons.append(btn)

    def _move(self, step: int):
        if not self.buttons:
            return
        self.selected = (self.selected + step) % len(self.buttons)
        for idx, btn in enumerate(self.buttons):
            on = idx == self.selected
            btn.configure(
                fg_color=COLORS["accent_soft"] if on else "transparent",
                text_color=COLORS["text_bright"] if on else COLORS["text"])
        self.buttons[self.selected].focus_set()

    def _execute(self, cmd=None):
        if cmd is None:
            if not self.filtered:
                return
            cmd = self.filtered[self.selected]
        self.destroy()
        self.after(50, cmd["action"])
