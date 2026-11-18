

from __future__ import annotations

import datetime
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from .config import COLORS, FONT_MONO_TUPLE, FONT_UI_TUPLE
from .terminal import TerminalPanel


class BottomPanel(ctk.CTkFrame):
    def __init__(self, master, on_terminal_output=None, height=240, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], corner_radius=0,
                         height=height, **kwargs)
        self.pack_propagate(False)
        self.on_terminal_output = on_terminal_output
        self.on_problem_open = None
        self._drag = None
        self._build()

    
    def _build(self):
        
        grip = ctk.CTkFrame(self, height=5, fg_color=COLORS["border"],
                            corner_radius=0, cursor="sb_v_double_arrow")
        grip.pack(fill="x", side="top")
        grip.pack_propagate(False)
        grip.bind("<ButtonPress-1>", self._start_resize)
        grip.bind("<B1-Motion>", self._on_resize)
        grip.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag", None))

        tabbar = ctk.CTkFrame(self, height=32, fg_color=COLORS["bg"],
                              corner_radius=0)
        tabbar.pack(fill="x", side="top")
        tabbar.pack_propagate(False)

        self.tab_buttons = {}
        self._tab_base = {}
        for name in ("TERMINAL", "OUTPUT", "PROBLEMS"):
            btn = ctk.CTkButton(
                tabbar, text=name, width=92, height=24, corner_radius=4,
                fg_color=COLORS["bg_deep"] if name == "TERMINAL" else "transparent",
                text_color=COLORS["text_bright"] if name == "TERMINAL" else COLORS["muted"],
                hover_color=COLORS["bg_light"], font=("Segoe UI", 10, "bold"),
                command=lambda n=name: self.select_tab(n),
            )
            btn.pack(side="left", padx=(6, 0), pady=4)
            self.tab_buttons[name] = btn
            self._tab_base[name] = name

        self.body = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"], corner_radius=0)
        self.body.pack(fill="both", expand=True)

        
        self.page_terminal = ctk.CTkFrame(self.body, fg_color=COLORS["bg_deep"],
                                          corner_radius=0)
        self.terminal = TerminalPanel(
            self.page_terminal, on_output=self._on_terminal_done)
        self.terminal.pack(fill="both", expand=True)

        
        self.page_output = ctk.CTkFrame(self.body, fg_color=COLORS["bg_deep"],
                                        corner_radius=0)
        head_o = ctk.CTkFrame(self.page_output, fg_color=COLORS["bg"],
                              height=26, corner_radius=0)
        head_o.pack(fill="x", side="top")
        head_o.pack_propagate(False)
        ctk.CTkLabel(head_o, text="LOG APLIKASI", font=("Segoe UI", 10, "bold"),
                     text_color=COLORS["muted"], anchor="w").pack(side="left", padx=10)
        ctk.CTkButton(head_o, text="Bersihkan", width=70, height=20,
                      fg_color="transparent", hover_color=COLORS["bg_lighter"],
                      font=FONT_UI_TUPLE, command=self.clear_logs).pack(side="right", padx=4)

        self.log_text = tk.Text(
            self.page_output, wrap="word", bg=COLORS["bg_deep"], fg=COLORS["text"],
            font=FONT_MONO_TUPLE, relief="flat", bd=0, padx=10, pady=6,
            highlightthickness=0, state="disabled",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_configure("INFO", foreground=COLORS["cyan"])
        self.log_text.tag_configure("SUCCESS", foreground=COLORS["green"])
        self.log_text.tag_configure("WARN", foreground=COLORS["yellow"])
        self.log_text.tag_configure("ERROR", foreground=COLORS["red"])
        self.log_text.tag_configure("HINT", foreground=COLORS["muted"])

        
        self.page_problems = ctk.CTkFrame(self.body, fg_color=COLORS["bg_deep"],
                                          corner_radius=0)
        head_p = ctk.CTkFrame(self.page_problems, fg_color=COLORS["bg"],
                              height=26, corner_radius=0)
        head_p.pack(fill="x", side="top")
        head_p.pack_propagate(False)
        ctk.CTkLabel(head_p, text="PROBLEMS & SARAN", font=("Segoe UI", 10, "bold"),
                     text_color=COLORS["muted"], anchor="w").pack(side="left", padx=10)
        ctk.CTkButton(head_p, text="Bersihkan", width=70, height=20,
                      fg_color="transparent", hover_color=COLORS["bg_lighter"],
                      font=FONT_UI_TUPLE, command=self.clear_problems).pack(side="right", padx=4)

        style = ttk.Style()
        style.configure("Nova.Prob.Treeview", background=COLORS["bg_deep"],
                        foreground=COLORS["text"], fieldbackground=COLORS["bg_deep"],
                        borderwidth=0, rowheight=26, font=FONT_UI_TUPLE)
        style.map("Nova.Prob.Treeview",
                  background=[("selected", COLORS["accent_soft"])])
        self.tree = ttk.Treeview(
            self.page_problems, style="Nova.Prob.Treeview",
            columns=("file", "line", "message", "hint"), show="headings",
        )
        self.tree.heading("file", text="File")
        self.tree.heading("line", text="Baris")
        self.tree.heading("message", text="Masalah")
        self.tree.heading("hint", text="Cara perbaikan")
        self.tree.column("file", width=180, anchor="w")
        self.tree.column("line", width=55, anchor="center")
        self.tree.column("message", width=300, anchor="w")
        self.tree.column("hint", width=380, anchor="w")
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)
        self.tree.bind("<Double-1>", self._open_problem)

        for page in (self.page_terminal, self.page_output, self.page_problems):
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.select_tab("TERMINAL")

    
    def _start_resize(self, event):
        self._drag = (event.y_root, self.winfo_height())

    def _on_resize(self, event):
        if not self._drag:
            return
        start_y, start_h = self._drag
        max_h = max(140, self.master.winfo_height() - 170)
        height = max(110, min(max_h, start_h + (start_y - event.y_root)))
        self.configure(height=height)

    
    def select_tab(self, name: str):
        pages = {"TERMINAL": self.page_terminal, "OUTPUT": self.page_output,
                 "PROBLEMS": self.page_problems}
        if name not in pages:
            return
        pages[name].tkraise()
        for key, btn in self.tab_buttons.items():
            on = key == name
            btn.configure(
                fg_color=COLORS["bg_deep"] if on else "transparent",
                text_color=COLORS["text_bright"] if on else COLORS["muted"])
        self.active_tab = name
        if name in self.tab_buttons:
            base = self._tab_base.get(name, name)
            self.tab_buttons[name].configure(text=base)
        if name == "TERMINAL":
            self.terminal.focus()

    def set_badge(self, name: str, count: int):
        
        btn = self.tab_buttons.get(name)
        if not btn:
            return
        base = self._tab_base.get(name, name)
        if name == self.active_tab or count <= 0:
            btn.configure(text=base)
        else:
            btn.configure(text=f"{base} ({count})")

    def show_terminal(self):
        self.pack(fill="x", side="bottom")
        self.select_tab("TERMINAL")

    def toggle(self):
        if self.winfo_ismapped():
            self.pack_forget()
        else:
            self.show_terminal()

    
    def log(self, message: str, level: str = "INFO", hint: str | None = None):
        stamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{stamp}] ", "INFO")
        self.log_text.insert("end", f"{level:<7} ", level if level in
                             ("INFO", "SUCCESS", "WARN", "ERROR") else "INFO")
        self.log_text.insert("end", message + "\n", level if level in
                             ("INFO", "SUCCESS", "WARN", "ERROR") else "INFO")
        if hint:
            self.log_text.insert("end", f"          ↳ saran: {hint}\n", "HINT")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def clear_logs(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def add_problem(self, file: str, line, message: str, hint: str):
        self.tree.insert("", "end", values=(file or "-", line or "-", message, hint))

    def clear_problems(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _open_problem(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        file, line, _, _ = self.tree.item(item, "values")
        if self.on_problem_open and file and file != "-":
            self.on_problem_open(file, int(line) if str(line).isdigit() else 1)

    
    def _on_terminal_done(self, cmd: str, output: str, code: int):
        if self.on_terminal_output:
            self.on_terminal_output(cmd, output, code)
