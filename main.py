#!/usr/bin/env python3
"""NovaCode — editor kode modern berbasis CustomTkinter.

Jalankan:  python main.py
Build exe: python build_exe.py
"""

from __future__ import annotations

import json
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

import customtkinter as ctk

from nova import icons
from nova.ai_chat import AIAssistant
from nova.config import (APP_NAME, APP_TITLE, APP_VERSION, COLORS,
                         apply_theme, asset_path, available_themes,
                         is_light_theme, language_for, language_label,
                         settings_path, user_name)
from nova.diagnostics import analyze_output
from nova.explorer import FileExplorer
from nova.findreplace import FindReplaceBar
from nova.palette import CommandPalette
from nova.splash import SplashScreen
from nova.tabmanager import TabManager
from nova.outputpanel import BottomPanel
from nova.widgets import Tooltip

WELCOME = """# NovaCode

# Mulai
#   Ctrl+O ........... buka file
#   Ctrl+Shift+O ..... buka folder proyek
#   Ctrl+N ........... file baru
#   Ctrl+S ........... simpan
#   Ctrl+Shift+P ..... command palette (semua perintah)
#   F5 ............... jalankan file Python
#
# Menyunting
#   Ctrl+D ........... duplikat baris
#   Ctrl+/ ........... komentari baris
#   Alt+Up / Down .... pindahkan baris
#   Ctrl+Shift+K ..... hapus baris
#   Ctrl+Space ....... autocomplete
#
# Tekan Ctrl+O untuk membuka file pertama Anda.
"""


class NovaApp(ctk.CTk):
    def __init__(self, show_splash: bool = True):
        super().__init__()
        # Jendela utama disembunyikan dulu; splash yang tampil lebih dulu.
        self.withdraw()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1440x860")
        self.minsize(900, 560)

        self.recent_files: list[str] = []
        self.last_folder: str | None = None
        self.open_tabs: list[str] = []
        self.diagnostics: list = []      # hasil analisis error terakhir
        self.settings_data: dict = {}
        self._load_settings()
        self.theme_name = apply_theme(self.theme_name)   # dipakai semua widget
        ctk.set_appearance_mode("light" if is_light_theme() else "dark")
        self._tune_ctk_theme()
        icons.set_scale(self)
        self._set_window_icon()
        self.configure(fg_color=COLORS["bg"])
        self._theme_var = tk.StringVar(value=self.theme_name)

        self._build_menu()
        self._build_toolbar()
        self._build_layout()
        self._build_statusbar()
        self._bind_shortcuts()
        self._register_commands()
        self._apply_hover_effects()

        self.after(80, self._restore_session)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        if show_splash:
            try:
                self.splash = SplashScreen(self, duration=4.2,
                                           on_done=self._finish_startup)
                self.splash.start()
            except Exception:
                self._finish_startup()
        else:
            self._finish_startup()

    def _finish_startup(self):
        """Tampilkan jendela utama setelah splash selesai."""
        self.deiconify()
        self.lift()
        self.focus_force()
        self._set_window_icon()
        try:
            from nova.animation import fade_window
            fade_window(self, 0.0, 1.0, 260)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_menu(self):
        self.menubar = tk.Menu(
            self, tearoff=0, bg=COLORS["bg_light"], fg=COLORS["text"],
            activebackground=COLORS["accent"], activeforeground=COLORS["white"],
        )

        file_menu = tk.Menu(self.menubar, tearoff=0, bg=COLORS["bg_light"],
                            fg=COLORS["text"], activebackground=COLORS["accent"],
                            activeforeground=COLORS["white"])
        file_menu.add_command(label="New File            Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open File...        Ctrl+O", command=self.open_file_dialog)
        file_menu.add_command(label="Open Folder...   Ctrl+Shift+O", command=self.open_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Save                  Ctrl+S", command=self.save)
        file_menu.add_command(label="Save As...          Ctrl+Shift+S", command=self.save_as_active)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab            Ctrl+W",
                              command=lambda: self.tabman.close_active())
        file_menu.add_command(label="Exit", command=self.on_close)

        edit_menu = tk.Menu(self.menubar, tearoff=0, bg=COLORS["bg_light"],
                            fg=COLORS["text"], activebackground=COLORS["accent"],
                            activeforeground=COLORS["white"])
        edit_menu.add_command(label="Find                  Ctrl+F", command=lambda: self.show_find(False))
        edit_menu.add_command(label="Replace              Ctrl+H", command=lambda: self.show_find(True))
        edit_menu.add_separator()
        edit_menu.add_command(label="Toggle Comment    Ctrl+/", command=self._action_toggle_comment)
        edit_menu.add_command(label="Duplicate Line    Ctrl+D", command=self._action_duplicate)
        edit_menu.add_command(label="Delete Line         Ctrl+Shift+K", command=self._action_delete_line)
        edit_menu.add_command(label="Move Line Up      Alt+↑", command=lambda: self._action_move(-1))
        edit_menu.add_command(label="Move Line Down  Alt+↓", command=lambda: self._action_move(1))

        view_menu = tk.Menu(self.menubar, tearoff=0, bg=COLORS["bg_light"],
                            fg=COLORS["text"], activebackground=COLORS["accent"],
                            activeforeground=COLORS["white"])
        view_menu.add_command(label="Toggle Explorer   Ctrl+B", command=self.toggle_explorer)
        view_menu.add_command(label="Toggle Terminal  Ctrl+`", command=self.toggle_terminal)
        view_menu.add_command(label="Toggle AI Panel  Ctrl+Shift+A", command=self.ai_toggle)
        view_menu.add_command(label="Output / Log", command=self.show_output)
        view_menu.add_command(label="Problems & Saran", command=self.show_problems)
        view_menu.add_command(label="Command Palette  Ctrl+Shift+P", command=self.open_palette)

        theme_menu = tk.Menu(self.menubar, tearoff=0, bg=COLORS["bg_light"],
                             fg=COLORS["text"], activebackground=COLORS["accent"],
                             activeforeground=COLORS["white"])
        for name in available_themes():
            theme_menu.add_radiobutton(
                label=name, variable=self._theme_var, value=name,
                command=lambda n=name: self.change_theme(n))
        theme_menu.add_separator()
        theme_menu.add_command(label="Pengaturan AI...", command=self.ai_settings)

        help_menu = tk.Menu(self.menubar, tearoff=0, bg=COLORS["bg_light"],
                            fg=COLORS["text"], activebackground=COLORS["accent"],
                            activeforeground=COLORS["white"])
        help_menu.add_command(label="Shortcuts & Fitur", command=self.show_help)
        help_menu.add_command(label=f"Tentang {APP_NAME}", command=self.show_about)

        self.menubar.add_cascade(label="File", menu=file_menu)
        self.menubar.add_cascade(label="Edit", menu=edit_menu)
        self.menubar.add_cascade(label="View", menu=view_menu)
        self.menubar.add_cascade(label="Theme", menu=theme_menu)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        self.configure(menu=self.menubar)

    def _tune_ctk_theme(self):
        """Samakan warna bawaan CustomTkinter (biru) dengan palet NovaCode."""
        try:
            T = ctk.ThemeManager.theme
            c = COLORS

            def pair(v):
                return [v, v]

            T["CTkButton"].update(
                fg_color=pair(c["bg_light"]), hover_color=pair(c["bg_lighter"]),
                border_color=pair(c["border"]), text_color=pair(c["text"]))
            T["CTkCheckBox"].update(
                fg_color=pair(c["accent"]), hover_color=pair(c["accent_hover"]),
                border_color=pair(c["bg_lighter"]), checkmark_color=pair(c["white"]),
                text_color=pair(c["text"]))
            T["CTkOptionMenu"].update(
                fg_color=pair(c["bg_light"]), button_color=pair(c["bg_lighter"]),
                button_hover_color=pair(c["accent"]), text_color=pair(c["text"]))
            T["CTkComboBox"].update(
                border_color=pair(c["border"]), button_color=pair(c["bg_lighter"]),
                button_hover_color=pair(c["accent"]), text_color=pair(c["text"]))
            T["CTkScrollbar"].update(
                button_color=pair(c["bg_lighter"]), button_hover_color=pair(c["muted"]))
            T["CTkEntry"].update(border_color=pair(c["border"]), text_color=pair(c["text"]))
        except Exception:
            pass

    def _set_window_icon(self):
        """Pasang ikon NovaCode (jangan biarkan ikon default CustomTkinter)."""
        ico = asset_path("icon.ico")
        if not os.path.isfile(ico):
            return

        def apply(target=None):
            win = target or self
            try:
                win.iconbitmap(ico)
            except Exception:
                pass

        apply()       # tandai sebagai "sudah dipilih user" untuk CustomTkinter
        # Beberapa build Windows mengganti ikon sekali lagi setelah intro.
        self.after(250, apply)

    def _set_dialog_icon(self, window):
        ico = asset_path("icon.ico")
        if os.path.isfile(ico):
            try:
                window.iconbitmap(ico)
            except Exception:
                pass

    def _brand_mark(self):
        """Logo kecil untuk toolbar (versi gelap/terang sesuai tema)."""
        try:
            from PIL import Image
            name = "mark_light.png" if is_light_theme() else "mark_dark.png"
            img = Image.open(asset_path(name)).convert("RGBA")
            self._brand_img = ctk.CTkImage(light_image=img, dark_image=img, size=(18, 18))
            return self._brand_img
        except Exception:
            return None

    def _build_toolbar(self):
        bar = ctk.CTkFrame(self, height=42, fg_color=COLORS["bg"], corner_radius=0)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"],
                     corner_radius=0).pack(fill="x", side="top")

        self.toolbar_buttons: list[ctk.CTkButton] = []

        def icon_btn(icon, tip, command):
            widget = ctk.CTkButton(
                bar, text="", image=icons.ctk_icon(icon, COLORS["muted"], 16),
                width=32, height=28, corner_radius=5,
                fg_color="transparent", hover_color=COLORS["bg_light"],
                command=command,
            )
            Tooltip(widget, tip)
            self.toolbar_buttons.append(widget)
            return widget

        # Merek: logo + nama
        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=(14, 10))
        mark = self._brand_mark()
        if mark is not None:
            ctk.CTkLabel(brand, text="", image=mark).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(brand, text="NovaCode", font=("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_bright"]).pack(side="left")

        ctk.CTkFrame(bar, width=1, fg_color=COLORS["border"]).pack(
            side="left", fill="y", padx=(2, 8), pady=9)

        icon_btn("plus", "File baru (Ctrl+N)", self.new_file).pack(side="left", padx=1, pady=7)
        icon_btn("file", "Buka file (Ctrl+O)", self.open_file_dialog).pack(side="left", padx=1, pady=7)
        icon_btn("folder_open", "Buka folder (Ctrl+Shift+O)", self.open_folder).pack(side="left", padx=1, pady=7)
        icon_btn("save", "Simpan (Ctrl+S)", self.save).pack(side="left", padx=1, pady=7)

        ctk.CTkFrame(bar, width=1, fg_color=COLORS["border"]).pack(
            side="left", fill="y", padx=8, pady=9)

        run = ctk.CTkButton(
            bar, text="Run", image=icons.ctk_icon("play", COLORS["white"], 14),
            compound="left", width=70, height=28, corner_radius=5,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            text_color=COLORS["white"], font=("Segoe UI", 12, "bold"),
            command=self.run_file,
        )
        Tooltip(run, "Jalankan file Python (F5)")
        run.pack(side="left", padx=2, pady=7)

        # Asisten AI: toggle panel dock di toolbar
        ai_btn = ctk.CTkButton(
            bar, text="Asisten", image=icons.ctk_icon("chat", COLORS["muted"], 15),
            compound="left", width=88, height=28, corner_radius=5,
            fg_color="transparent", hover_color=COLORS["bg_light"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text"], font=("Segoe UI", 12),
            command=lambda: self.ai.toggle(),
        )
        Tooltip(ai_btn, "Tampil/sembunyikan panel AI (Ctrl+Shift+A)")
        ai_btn.pack(side="right", padx=(4, 12), pady=7)
        self.toolbar_buttons.append(ai_btn)

    def _build_layout(self):
        self.main = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"], corner_radius=0)
        self.main.pack(fill="both", expand=True)

        self.explorer = FileExplorer(
            self.main, on_open_file=self.open_path,
            on_open_terminal=lambda p: self._open_terminal_at(p),
            width=268,
        )
        self.explorer.set_app(self)
        self.explorer.pack(side="left", fill="y")

        # Panel AI langsung nempel di kanan, dibuat sebelum center supaya lebarnya nggak kepangan 🗿
        self.ai = AIAssistant(
            self, self, self.settings_data,
            on_settings_saved=self._save_settings, master=self.main,
        )
        self.ai.show()

        self.center = ctk.CTkFrame(self.main, fg_color=COLORS["bg_deep"], corner_radius=0)
        self.center.pack(side="left", fill="both", expand=True)

        self.tabman = TabManager(
            self.center, app=self, on_status=self._on_status,
            on_cursor=self._on_cursor,
        )
        self.tabman.pack(fill="both", expand=True)

        self.findbar = FindReplaceBar(
            self.tabman.find_host, on_close=lambda: self.tabman.active_editor.focus_editor()
            if self.tabman.active_editor else None,
        )

        # Panel bawah: Terminal + Output/Log + Problems (langsung terlihat)
        self.bottom = BottomPanel(
            self.center, on_terminal_output=self._analyze_output, height=235)
        self.bottom.pack(fill="x", side="bottom")
        self.bottom.on_problem_open = self.open_problem
        self.terminal = self.bottom.terminal
        self.bottom.log("NovaCode siap. Panel Terminal aktif.", "SUCCESS")

    def _build_statusbar(self):
        self.statusbar = ctk.CTkFrame(self, height=26, fg_color=COLORS["bg"],
                                      corner_radius=0)
        self.statusbar.pack(fill="x", side="bottom")
        self.statusbar.pack_propagate(False)
        ctk.CTkFrame(self, height=1, fg_color=COLORS["border"],
                     corner_radius=0).pack(fill="x", side="bottom")

        font = ("Segoe UI", 10)
        self.status_file = ctk.CTkLabel(self.statusbar, text="", font=font,
                                        text_color=COLORS["text"], anchor="w")
        self.status_file.pack(side="left", padx=12)

        self.status_lang = ctk.CTkLabel(self.statusbar, text="Python", font=font,
                                        text_color=COLORS["muted"])
        self.status_lang.pack(side="right", padx=(8, 12))

        self.status_enc = ctk.CTkLabel(self.statusbar, text="UTF-8", font=font,
                                       text_color=COLORS["muted"])
        self.status_enc.pack(side="right", padx=8)

        self.status_pos = ctk.CTkLabel(self.statusbar, text="Ln 1, Col 1", font=font,
                                       text_color=COLORS["muted"], cursor="hand2")
        self.status_pos.pack(side="right", padx=8)
        self.status_pos.bind("<Button-1>", lambda e: self.goto_line_dialog())

    # ------------------------------------------------------------------
    # Shortcut & command palette
    # ------------------------------------------------------------------
    def _bind_shortcuts(self):
        b = self.bind_all
        b("<Control-n>", lambda e: self.new_file())
        b("<Control-o>", lambda e: self.open_file_dialog())
        b("<Control-Shift-O>", lambda e: self.open_folder())
        b("<Control-s>", lambda e: self.save())
        b("<Control-Shift-S>", lambda e: self.save_as_active())
        b("<Control-w>", lambda e: self.tabman.close_active())
        b("<Control-f>", lambda e: self.show_find(False))
        b("<Control-h>", lambda e: self.show_find(True))
        b("<Control-grave>", lambda e: self.toggle_terminal())
        b("<Control-Shift-A>", lambda e: self.ai_toggle())
        b("<Control-b>", lambda e: self.toggle_explorer())
        b("<Control-Shift-P>", lambda e: self.open_palette())
        b("<Control-g>", lambda e: self.goto_line_dialog())
        b("<Control-Tab>", lambda e: self.tabman.next_tab(1))
        b("<Control-Shift-Tab>", lambda e: self.tabman.next_tab(-1))
        b("<Alt-Up>", lambda e: self._action_move(-1))
        b("<Alt-Down>", lambda e: self._action_move(1))
        b("<F5>", lambda e: self.run_file())

    def _register_commands(self):
        self.commands = [
            {"title": "File: New File", "hint": "file baru", "shortcut": "Ctrl+N", "action": self.new_file},
            {"title": "File: Open File", "hint": "buka file", "shortcut": "Ctrl+O", "action": self.open_file_dialog},
            {"title": "File: Open Folder", "hint": "buka folder proyek", "shortcut": "Ctrl+Shift+O", "action": self.open_folder},
            {"title": "File: Save", "hint": "simpan", "shortcut": "Ctrl+S", "action": self.save},
            {"title": "File: Save As", "hint": "simpan sebagai", "shortcut": "Ctrl+Shift+S", "action": self.save_as_active},
            {"title": "File: Close Tab", "hint": "tutup tab", "shortcut": "Ctrl+W", "action": self.tabman.close_active},
            {"title": "Edit: Find", "hint": "cari teks", "shortcut": "Ctrl+F", "action": lambda: self.show_find(False)},
            {"title": "Edit: Replace", "hint": "cari dan ganti", "shortcut": "Ctrl+H", "action": lambda: self.show_find(True)},
            {"title": "Edit: Toggle Comment", "hint": "komentar baris", "shortcut": "Ctrl+/", "action": self._action_toggle_comment},
            {"title": "Edit: Duplicate Line", "hint": "duplikat baris", "shortcut": "Ctrl+D", "action": self._action_duplicate},
            {"title": "Edit: Delete Line", "hint": "hapus baris", "shortcut": "Ctrl+Shift+K", "action": self._action_delete_line},
            {"title": "View: Toggle Explorer", "hint": "panel folder", "shortcut": "Ctrl+B", "action": self.toggle_explorer},
            {"title": "View: Toggle Terminal", "hint": "panel terminal", "shortcut": "Ctrl+`", "action": self.toggle_terminal},
            {"title": "View: Output / Log", "hint": "log aplikasi & error", "action": self.show_output},
            {"title": "View: Problems & Saran", "hint": "daftar masalah + cara perbaikan", "action": self.show_problems},
            {"title": "Go to Line", "hint": "loncat ke baris", "shortcut": "Ctrl+G", "action": self.goto_line_dialog},
            {"title": "Run: Run Active File", "hint": "jalankan file Python", "shortcut": "F5", "action": self.run_file},
            {"title": "Theme: Ganti Tema", "hint": "ember graphite moss paper purple moon", "action": self._cycle_theme},
            {"title": "AI: Tampil/Sembunyikan Panel", "hint": "chat AI di kanan", "shortcut": "Ctrl+Shift+A", "action": self.ai_toggle},
            {"title": "AI: Lampirkan File", "hint": "teks / gambar / file", "action": lambda: self.ai.attach_file()},
            {"title": "AI: Pengaturan Model", "hint": "api key / gguf", "action": self.ai_settings},
            {"title": "Help: Shortcuts & Fitur", "hint": "panduan", "action": self.show_help},
        ]

    def open_palette(self):
        CommandPalette(self, self.commands)

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------
    def new_file(self, *args):
        self.tabman.new_file()

    def open_file_dialog(self, *args):
        paths = filedialog.askopenfilenames(
            title="Buka file",
            filetypes=[("Semua file", "*"), ("Teks", "*.txt"), ("Python", "*.py"),
                       ("Web", "*.html;*.css;*.js;*.ts"), ("JSON", "*.json")],
        )
        for path in paths:
            self.open_path(path)

    def open_path(self, path: str):
        editor = self.tabman.open_file(path)
        if editor:
            # File yang dibuka ulang ikut dapat penanda error yang masih aktif.
            editor.show_diagnostics(self.diagnostics)
        if path not in self.recent_files:
            self.recent_files.insert(0, path)
            self.recent_files = self.recent_files[:12]

    def open_folder(self, *args):
        self.explorer.open_folder_dialog()

    def save(self, *args):
        editor = self.tabman.active_editor
        if not editor:
            return
        if editor.path:
            editor.save()
        else:
            self.save_as(editor)

    def save_as(self, editor) -> bool:
        path = filedialog.asksaveasfilename(
            title="Simpan sebagai", defaultextension=".py",
            initialfile=os.path.basename(editor.path) if editor.path else "untitled.py",
            filetypes=[("Python", "*.py"), ("Semua file", "*")],
        )
        if not path:
            return False
        tab = getattr(editor, "tab", None)
        if tab:
            tab["path"] = path
            tab["title"] = os.path.basename(path)
        return editor.save(path)

    def save_as_active(self, *args):
        editor = self.tabman.active_editor
        if editor:
            self.save_as(editor)

    # ------------------------------------------------------------------
    # Panel & aksi
    # ------------------------------------------------------------------
    def show_find(self, replace: bool):
        editor = self.tabman.active_editor
        if editor:
            self.findbar.attach(editor, replace)

    def toggle_explorer(self):
        if self.explorer.winfo_ismapped():
            self.explorer.pack_forget()
        else:
            self.explorer.pack(side="left", fill="y", before=self.center)

    def toggle_terminal(self):
        self.bottom.toggle()

    def show_output(self):
        if not self.bottom.winfo_ismapped():
            self.bottom.pack(fill="x", side="bottom")
        self.bottom.select_tab("OUTPUT")

    def show_problems(self):
        if not self.bottom.winfo_ismapped():
            self.bottom.pack(fill="x", side="bottom")
        self.bottom.select_tab("PROBLEMS")

    def _open_terminal_at(self, path: str):
        self.bottom.show_terminal()
        self.terminal.set_cwd(path)
        self.terminal.focus()

    def open_problem(self, file: str, line: int):
        """Dari panel Problems -> buka file dan arah ke barisnya."""
        if os.path.isfile(file):
            self.open_path(file)
            editor = self.tabman.active_editor
            if editor:
                editor.goto_line(line)
            self.bottom.log(f"Membuka {os.path.basename(file)}:{line}", "INFO")
        else:
            self.bottom.log(f"File tidak ditemukan: {file}", "WARN")

    def set_cwd(self, path: str):
        self.terminal.set_cwd(path)

    def set_title_path(self, path: str):
        self.title(f"{APP_NAME} — {os.path.basename(path)}")

    def run_file(self, *args):
        editor = self.tabman.active_editor
        if not editor:
            return
        if not editor.path:
            messagebox.showinfo("NovaCode", "Simpan file terlebih dahulu sebelum menjalankan.")
            return
        if editor.dirty:
            editor.save()
        if language_for(editor.path) != "python":
            messagebox.showinfo("NovaCode", "Run otomatis saat ini hanya untuk file Python (.py).")
            return
        self.bottom.show_terminal()
        self.terminal.set_cwd(os.path.dirname(editor.path) or self.terminal.cwd)
        self.terminal.send_command(f'python "{editor.path}"')

    def goto_line_dialog(self, *args):
        editor = self.tabman.active_editor
        if not editor:
            return
        from tkinter import simpledialog
        line = simpledialog.askinteger("Go to Line", "Nomor baris:",
                                       parent=self, minvalue=1)
        if line:
            editor.goto_line(line)

    def _action_toggle_comment(self):
        e = self.tabman.active_editor
        if e:
            e.toggle_comment(); e.focus_editor()
            return "break"

    def _action_duplicate(self):
        e = self.tabman.active_editor
        if e:
            e.duplicate_line(); e.focus_editor()
            return "break"

    def _action_delete_line(self):
        e = self.tabman.active_editor
        if e:
            e.delete_line(); e.focus_editor()
            return "break"

    def _action_move(self, step: int):
        e = self.tabman.active_editor
        if e:
            e.move_line(step); e.focus_editor()
            return "break"

    # ------------------------------------------------------------------
    # Status bar & session
    # ------------------------------------------------------------------
    def _on_cursor(self, info: dict):
        self.status_pos.configure(text=f"Ln {info['line']}, Col {info['col']}")

    def _on_status(self, editor):
        if not editor:
            return
        self.status_lang.configure(text=language_label(editor.language))
        self.status_enc.configure(text=editor.encoding.upper())
        name = os.path.basename(editor.path) if editor.path else "Untitled"
        self.status_file.configure(text=f"{'● ' if editor.dirty else ''}{name}")

    def _load_settings(self):
        self.settings_data = {}
        try:
            with open(settings_path(), "r", encoding="utf-8") as f:
                self.settings_data = json.load(f)
        except Exception:
            pass
        self.recent_files = self.settings_data.get("recent_files", [])
        self.last_folder = self.settings_data.get("last_folder")
        self.open_tabs = self.settings_data.get("open_tabs", [])
        self.theme_name = self.settings_data.get("theme", "Ember")

    def _save_settings(self):
        editor = self.tabman.active_editor
        ai_cfg = self.settings_data.get("ai", {})
        if getattr(self, "ai", None):
            ai_cfg = self.ai._ai()
        data = {
            "recent_files": self.recent_files,
            "last_folder": self.last_folder,
            "last_file": editor.path if editor and editor.path else None,
            "theme": self.theme_name,
            "open_tabs": [t["path"] for t in self.tabman.tabs if t["path"]][:8],
            "ai": ai_cfg,
        }
        self.settings_data = data
        try:
            with open(settings_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _restore_session(self):
        # Default: tampilkan seluruh isi folder user agar langsung bisa dipilih
        home = os.path.expanduser("~")
        root = self.last_folder if self.last_folder and os.path.isdir(self.last_folder) else home
        self.explorer.set_root(root)
        self.terminal.set_cwd(root)
        self.bottom.log(f"Explorer: {root}", "INFO")

        opened = 0
        for path in self.open_tabs[:8]:
            if os.path.isfile(path):
                self.open_path(path)
                opened += 1
        if opened == 0:
            for path in self.recent_files[:3]:
                if os.path.isfile(path):
                    self.open_path(path)
                    opened += 1
        if opened == 0:
            self.tabman.new_file(WELCOME, "python")

    # ------------------------------------------------------------------
    # Analisis output terminal -> error di Output/Problems (Terminal tetap aktif)
    # ------------------------------------------------------------------
    def _analyze_output(self, cmd: str, output: str, code: int):
        """Hasil run tetap di Terminal; Output/Problems hanya mencatat error."""
        editor = self.tabman.active_editor
        current_file = editor.path if editor else None

        if code == 0:
            # Tidak ada perpindahan tab dan tidak ada log sukses di Output.
            # Error lama juga dibersihkan supaya tidak menyesatkan.
            self.diagnostics = []
            self.bottom.clear_problems()
            self.bottom.set_badge("PROBLEMS", 0)
            self.bottom.set_badge("OUTPUT", 0)
            for tab in self.tabman.tabs:
                tab["editor"].clear_diagnostics()
            return

        diags = analyze_output(output, current_file=current_file,
                               cwd=self.terminal.cwd)
        self.diagnostics = diags
        self.bottom.clear_problems()
        self.bottom.set_badge("OUTPUT", len(diags))

        for diag in diags:
            self.bottom.add_problem(diag.file, diag.line, diag.message, diag.hint)
            self.bottom.log(
                f"{os.path.basename(diag.file) or '-'}:{diag.line} — {diag.message}",
                "ERROR", diag.hint)

        self.bottom.set_badge("PROBLEMS", len(diags))
        self._apply_diagnostics()
        # Sengaja tidak memanggil select_tab(): fokus tetap di Terminal.

    def _apply_diagnostics(self):
        """Tandai semua baris error pada editor yang sedang terbuka."""
        for tab in self.tabman.tabs:
            tab["editor"].show_diagnostics(self.diagnostics)

    # ------------------------------------------------------------------
    # Tema, AI, dan efek interaksi
    # ------------------------------------------------------------------
    def change_theme(self, name: str):
        if name == self.theme_name:
            return
        self.theme_name = name
        self._save_settings()
        self._theme_restart = True   # dibaca oleh main() untuk rebuild UI
        self.after(80, self.destroy)

    def _cycle_theme(self):
        themes = available_themes()
        idx = themes.index(self.theme_name) if self.theme_name in themes else 0
        self.change_theme(themes[(idx + 1) % len(themes)])

    def ai_toggle(self):
        if getattr(self, "ai", None):
            self.ai.toggle()

    def ai_settings(self):
        if getattr(self, "ai", None):
            self.ai.open_settings()

    def _apply_hover_effects(self):
        """Sengaja kosong: hover diatur langsung oleh tiap widget dengan satu
        gaya seragam (tanpa glow warna-warni) agar tampilan tetap tenang."""
        return

    def on_close(self):
        self._save_settings()
        self.destroy()

    # ------------------------------------------------------------------
    def show_about(self):
        win = ctk.CTkToplevel(self)
        win.title(f"Tentang {APP_NAME}")
        win.geometry("460x460")
        win.resizable(False, False)
        win.transient(self)
        win.configure(fg_color=COLORS["bg"])
        self._set_dialog_icon(win)

        try:
            from PIL import Image
            img = Image.open(asset_path("logo.png")).convert("RGBA")
            logo = ctk.CTkImage(light_image=img, dark_image=img, size=(108, 108))
            ctk.CTkLabel(win, text="", image=logo).pack(pady=(24, 10))
        except Exception:
            pass

        ctk.CTkLabel(win, text=APP_NAME, font=("Segoe UI", 22, "bold"),
                     text_color=COLORS["text_bright"]).pack()
        ctk.CTkLabel(win, text=f"Versi {APP_VERSION}", font=("Segoe UI", 11),
                     text_color=COLORS["accent"]).pack(pady=(2, 16))

        desc = (
            "Editor kode ringan dan kaya fitur, dibuat dengan\n"
            "Python + CustomTkinter.\n\n"
            "Syntax highlighting, explorer, tab, find/replace,\n"
            "autocomplete, command palette, terminal + log/error,\n"
            "5 tema warna, dan asisten AI (GGUF/API)."
        )
        ctk.CTkLabel(win, text=desc, justify="center", font=("Segoe UI", 12),
                     text_color=COLORS["text"]).pack()
        ctk.CTkLabel(win, text=f"Diterbitkan sebagai {user_name()} — portable untuk semua pengguna.",
                     font=("Segoe UI", 10), text_color=COLORS["muted"]).pack(pady=(18, 12))
        ctk.CTkButton(win, text="Tutup", width=110, command=win.destroy).pack(pady=(0, 20))

    def show_help(self):
        text = """
SHORTCUT KEYBOARD
──────────────────────────────────────────────
Ctrl+N            File baru
Ctrl+O            Buka file
Ctrl+Shift+O      Buka folder proyek
Ctrl+S            Simpan file
Ctrl+Shift+S      Simpan sebagai
Ctrl+W            Tutup tab aktif
Ctrl+Tab          Tab berikutnya
Ctrl+F            Cari teks
Ctrl+H            Cari & ganti
Ctrl+/            Komentar / unkomentar baris
Ctrl+D            Duplikat baris
Ctrl+Shift+K      Hapus baris
Alt+↑ / Alt+↓     Pindah baris atas/bawah
Ctrl+Space        Munculkan autocomplete
Ctrl+G            Lompat ke nomor baris
Ctrl+B            Tampil/sembunyi explorer
Ctrl+`            Tampil/sembunyi terminal
Ctrl+Shift+A      Tampil/sembunyi panel AI
Ctrl+Shift+P      Command palette
F5                Jalankan file Python
──────────────────────────────────────────────

FITUR UTAMA
──────────────────────────────────────────────
• Syntax highlighting 15+ bahasa
• File explorer + menu klik kanan
• Multi-tab dengan penanda perubahan (●)
• Find & replace (case-sensitive / whole word)
• Autocomplete kontekstual
• Terminal cmd / PowerShell
• Panel bawah: Terminal / Output (log) / Problems
  (error otomatis dianalisis + saran perbaikan)
• Explorer langsung menampilkan folder user (Home)
• Command palette
• Status bar (baris, kolom, encoding, bahasa)
• 5 tema: Ember / Graphite / Moss / Paper / Purple Moon (menu Theme)
• Asisten AI panel kanan: GGUF lokal, Ollama, LM Studio,
  OpenRouter, OpenAI, Gemini, Grok, DeepSeek, OpenCode, 9Router
  (bisa teks doang, teks + file, atau gambar)
• Simpan sesi (tema, tab, folder, pengaturan AI)
"""
        win = ctk.CTkToplevel(self)
        win.title("Shortcuts & Fitur — NovaCode")
        win.geometry("620x600")
        win.transient(self)
        win.configure(fg_color=COLORS["bg"])
        self._set_dialog_icon(win)
        box = ctk.CTkTextbox(win, font=("Consolas", 12), wrap="none",
                             fg_color=COLORS["bg_deep"], text_color=COLORS["text"])
        box.pack(fill="both", expand=True, padx=10, pady=10)
        box.insert("1.0", text)
        box.configure(state="disabled")
        ctk.CTkButton(win, text="Tutup", command=win.destroy).pack(pady=(0, 10))


def main():
    # Theme change destroys & recreates the window with the new palette.
    # Splash hanya diputar sekali saat aplikasi benar-benar dibuka.
    first_run = True
    while True:
        app = NovaApp(show_splash=first_run)
        app.mainloop()
        if not getattr(app, "_theme_restart", False):
            break
        first_run = False


if __name__ == "__main__":
    main()
