"""Panel Find & Replace yang muncul di atas editor."""

from __future__ import annotations

import tkinter as tk

import customtkinter as ctk

from . import icons
from .config import COLORS, FONT_UI_TUPLE


class FindReplaceBar(ctk.CTkFrame):
    def __init__(self, master, on_close=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_light"], corner_radius=0,
                         height=68, **kwargs)
        self.editor = None
        self.matches = []
        self.index = 0
        self.on_close = on_close
        self.case_var = ctk.StringVar(value="off")
        self.word_var = ctk.StringVar(value="off")
        self.replace_mode = False
        self._job = None
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.find_entry = ctk.CTkEntry(
            self, placeholder_text="Cari...", font=FONT_UI_TUPLE,
            fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
            text_color=COLORS["text"], height=30,
        )
        self.find_entry.grid(row=0, column=0, sticky="ew", padx=(10, 4), pady=(8, 2))
        self.find_entry.bind("<KeyRelease>", self._on_search_changed)
        self.find_entry.bind("<Return>", lambda e: self.find_next(1))
        self.find_entry.bind("<Escape>", lambda e: self.hide())

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=1, sticky="w", pady=(8, 2))
        ctk.CTkButton(nav, text="", image=icons.ctk_icon("chevron_up", COLORS["muted"], 14),
                      width=26, height=28, fg_color="transparent",
                      hover_color=COLORS["bg_lighter"], command=lambda: self.find_next(-1)).pack(side="left")
        ctk.CTkButton(nav, text="", image=icons.ctk_icon("chevron_down", COLORS["muted"], 14),
                      width=26, height=28, fg_color="transparent",
                      hover_color=COLORS["bg_lighter"], command=lambda: self.find_next(1)).pack(side="left")
        self.count_label = ctk.CTkLabel(nav, text="0 hasil", font=FONT_UI_TUPLE,
                                        text_color=COLORS["muted"], width=70)
        self.count_label.pack(side="left", padx=4)
        ctk.CTkCheckBox(nav, text="Aa", variable=self.case_var, onvalue="on", offvalue="off",
                        width=34, font=FONT_UI_TUPLE,
                        command=self._on_search_changed).pack(side="left", padx=2)
        ctk.CTkCheckBox(nav, text="ab|", variable=self.word_var, onvalue="on", offvalue="off",
                        width=40, font=FONT_UI_TUPLE,
                        command=self._on_search_changed).pack(side="left", padx=2)
        self.toggle_btn = ctk.CTkButton(nav, text="▾", width=24, height=28,
                                        fg_color="transparent",
                                        hover_color=COLORS["bg_lighter"],
                                        command=self.toggle_replace)
        self.toggle_btn.pack(side="left", padx=2)
        ctk.CTkButton(nav, text="", image=icons.ctk_icon("close", COLORS["muted"], 12),
                      width=24, height=28, fg_color="transparent",
                      hover_color=COLORS["bg_lighter"], command=self.hide).pack(side="left")

        # baris replace (default tersembunyi)
        self.replace_row = ctk.CTkFrame(self, fg_color="transparent")
        self.replace_entry = ctk.CTkEntry(
            self.replace_row, placeholder_text="Ganti dengan...", font=FONT_UI_TUPLE,
            fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
            text_color=COLORS["text"], height=28,
        )
        self.replace_entry.pack(side="left", fill="x", expand=True,
                                padx=(10, 4), pady=(2, 6))
        self.replace_entry.bind("<Return>", lambda e: self.replace_current())
        ctk.CTkButton(self.replace_row, text="Ganti", width=64, height=28,
                      font=FONT_UI_TUPLE, command=self.replace_current).pack(side="left", padx=2)
        ctk.CTkButton(self.replace_row, text="Semua", width=64, height=28,
                      font=FONT_UI_TUPLE, fg_color=COLORS["accent"],
                      hover_color=COLORS["accent_hover"], text_color=COLORS["white"],
                      command=self.replace_all).pack(side="left", padx=(2, 8))

    # ------------------------------------------------------------------
    def attach(self, editor, replace_mode: bool = False):
        self.editor = editor
        if replace_mode:
            self.show_replace(True)
        self.show()
        self.find_entry.focus_set()
        self._on_search_changed()

    def show(self):
        self.pack(fill="x", side="top")
        self._on_search_changed()

    def hide(self):
        if self.editor:
            self.editor.clear_matches()
        self.pack_forget()
        if self.on_close:
            self.on_close()

    def toggle_replace(self):
        self.show_replace(not self.replace_mode)

    def show_replace(self, value: bool):
        self.replace_mode = value
        if value:
            self.replace_row.grid(row=1, column=0, columnspan=2, sticky="ew")
            self.configure(height=96)
        else:
            self.replace_row.grid_forget()
            self.configure(height=68)
        self.toggle_btn.configure(text="▴" if value else "▾")

    # ------------------------------------------------------------------
    def _on_search_changed(self, event=None):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(120, self._do_search)

    def _do_search(self):
        if not self.editor:
            return
        needle = self.find_entry.get()
        self.editor.clear_matches()
        if not needle:
            self.matches = []
            self.index = 0
            self.count_label.configure(text="0 hasil")
            return
        self.matches = self.editor.find_all(
            needle,
            case_sensitive=self.case_var.get() == "on",
            whole_word=self.word_var.get() == "on",
        )
        self.index = 0
        self.count_label.configure(text=f"{len(self.matches)} hasil")
        self.editor.show_matches(self.matches, self.index)

    def find_next(self, step: int):
        if not self.matches or not self.editor:
            return
        self.index = (self.index + step) % len(self.matches)
        self.editor.show_matches(self.matches, self.index)
        self.count_label.configure(text=f"{self.index + 1}/{len(self.matches)}")

    def replace_current(self):
        if not self.editor or not self.matches:
            return
        start, end = self.matches[self.index]
        self.editor.replace_one(start, end, self.replace_entry.get())
        self._do_search()

    def replace_all(self):
        if not self.editor or not self.matches:
            return
        replacement = self.replace_entry.get()
        # ganti dari belakang agar index tetap valid
        for start, end in reversed(self.matches):
            self.editor.replace_one(start, end, replacement)
        self._do_search()
