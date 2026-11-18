"""Manajer tab: banyak file terbuka, ganti tab, simpan & tutup."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from . import icons
from .config import COLORS
from .editor import CodeEditor


class TabManager(ctk.CTkFrame):
    def __init__(self, master, app=None, on_status=None, on_cursor=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_deep"], corner_radius=0, **kwargs)
        self.app = app
        self.on_status = on_status
        self.on_cursor = on_cursor
        self.tabs: list[dict] = []
        self.active: dict | None = None
        self._counter = 0

        # Tab bar bisa di-scroll horizontal supaya semua file yang pernah dibuka
        # tetap bisa diklik walau jumlahnya melebihi lebar jendela.
        self.tabbar = ctk.CTkFrame(self, height=38, fg_color=COLORS["bg"],
                                   corner_radius=0)
        self.tabbar.pack(fill="x", side="top")
        self.tabbar.pack_propagate(False)

        self.tab_canvas = tk.Canvas(
            self.tabbar, height=38, bg=COLORS["bg"],
            highlightthickness=0, bd=0,
        )
        self.tab_canvas.pack(fill="both", expand=True)
        self.tab_strip = ctk.CTkFrame(self.tab_canvas, fg_color=COLORS["bg"],
                                      corner_radius=0)
        self.tab_canvas.create_window((0, 0), window=self.tab_strip, anchor="nw")
        self.tab_canvas.bind("<Configure>", lambda e: self._update_tab_scroll())
        self.tab_canvas.bind("<MouseWheel>", self._tab_mousewheel)
        self.tabbar.bind("<MouseWheel>", self._tab_mousewheel)
        # Fallback: klik pada area kosong tab bar tetap memilih tab yang
        # berada di bawah kursor (mis. saat event tidak sampai ke kartu).
        self.tab_canvas.bind("<Button-1>", self._on_tabbar_click, add="+")
        self.tab_canvas.bind("<ButtonPress-1>", self._on_tabbar_click, add="+")
        # Klik sekali langsung pindah tab, biasanya CTk nyumat event pertama 🗿
        self.winfo_toplevel().bind(
            "<ButtonPress-1>", self._on_global_tab_press, add="+")

        tk.Frame(self, bg=COLORS["border"], height=1).pack(fill="x", side="top")

        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_deep"], corner_radius=0)
        self.content.pack(fill="both", expand=True)

        # host untuk panel Find & Replace (dipakai aplikasi utama).
        # Pakai tk.Frame dengan tinggi 0: CTkFrame punya tinggi default 200px
        # yang akan menutupi bagian atas editor saat masih kosong.
        self.find_host = tk.Frame(self.content, bg=COLORS["bg_deep"], height=0)
        self.find_host.pack(fill="x", side="top")

    # ------------------------------------------------------------------
    # Property
    # ------------------------------------------------------------------
    @property
    def active_editor(self) -> CodeEditor | None:
        return self.active["editor"] if self.active else None

    # ------------------------------------------------------------------
    # Scroll tabbar
    # ------------------------------------------------------------------
    def _update_tab_scroll(self):
        """Sesuaikan area scroll dan pastikan tab aktif tetap terlihat."""
        if not hasattr(self, "tab_canvas"):
            return
        self.tab_strip.update_idletasks()
        bbox = self.tab_canvas.bbox("all")
        if not bbox:
            return
        x0, _y0, x1, y1 = bbox
        total = max(1, x1 - x0)
        self.tab_canvas.configure(scrollregion=(x0, _y0, x1, y1))

        frame = self.active.get("frame") if self.active else None
        if frame is None or not frame.winfo_exists():
            return
        canvas_w = self.tab_canvas.winfo_width()
        if canvas_w <= 1:
            return
        left, right = frame.winfo_x(), frame.winfo_x() + frame.winfo_width()
        view_l, view_r = self.tab_canvas.xview()
        # xview() adalah fraksi dari scrollregion, bukan piksel absolut.
        visible_l = x0 + view_l * total
        visible_r = x0 + view_r * total
        if left < visible_l:
            self.tab_canvas.xview_moveto(max(0, left - x0 - 8) / total)
        elif right > visible_r:
            self.tab_canvas.xview_moveto(max(0, right - x0 - canvas_w + 8) / total)

    def _tab_mousewheel(self, event):
        # scroll horizontal memakai mouse wheel biasa di Windows/macOS
        step = -1 if getattr(event, "delta", 0) > 0 else 1
        self.tab_canvas.xview_scroll(step, "units")
        return "break"

    # ------------------------------------------------------------------
    # Klik kartu tab
    # ------------------------------------------------------------------
    def _bind_tab_click(self, widget, tab: dict, recursive: bool = False):
        """Ikat klik kartu ke widget (dan opsional seluruh turunannya).

        CustomTkinter 5.x menyimpan binding langsung di widget, sedangkan
        6.x memakai canvas internal. Mengikat semua lapisan dengan ``add="+"``
        membuat klik tetap bekerja pada kedua versi tanpa menimpa binding
        yang sudah ada (mis. tooltip / tombol close).
        """
        try:
            widget.bind("<Button-1>", lambda e, t=tab: self.select(t), add="+")
        except Exception:
            pass
        if not recursive:
            return
        try:
            children = list(widget.winfo_children())
        except Exception:
            return
        for child in children:
            self._bind_tab_click(child, tab, recursive=True)

    def _on_tabbar_click(self, event):
        """Fallback: tentukan tab dari koordinat bila klik kena canvas kosong."""
        if event.widget is not self.tab_canvas:
            return
        x = self.tab_canvas.canvasx(event.x)
        for tab in self.tabs:
            frame = tab.get("frame")
            if frame is None or not frame.winfo_exists():
                continue
            left = frame.winfo_x()
            right = left + frame.winfo_width()
            if left <= x <= right:
                self.select(tab)
                break

    def _on_global_tab_press(self, event):
        """Tangkap klik di kartu tab dari lapisan mana pun (CTk sering nahan klik pertama)."""
        widget = event.widget
        jump = 0
        try:
            while widget is not None and widget is not self.tab_strip and jump < 30:
                widget = widget.master
                jump += 1
        except Exception:
            return
        if widget is not self.tab_strip:
            return

        # Tombol close sengaja dikecualin supaya kliknya tetap buang tab, bukan pindah tab.
        for tab in self.tabs:
            close = tab.get("close")
            if close is None or not close.winfo_exists():
                continue
            x1, y1 = close.winfo_rootx(), close.winfo_rooty()
            x2, y2 = x1 + close.winfo_width(), y1 + close.winfo_height()
            if x1 <= event.x_root <= x2 and y1 <= event.y_root <= y2:
                return

        x = self.tab_canvas.canvasx(event.x_root - self.tab_canvas.winfo_rootx())
        for tab in self.tabs:
            frame = tab.get("frame")
            if frame is None or not frame.winfo_exists():
                continue
            left = frame.winfo_x()
            right = left + frame.winfo_width()
            if left <= x <= right:
                self.select(tab)
                break

    # ------------------------------------------------------------------
    # Operasi tab
    # ------------------------------------------------------------------
    def open_file(self, path: str) -> CodeEditor | None:
        path = os.path.abspath(os.path.normpath(path))
        for tab in self.tabs:
            if tab["path"] and os.path.normcase(tab["path"]) == os.path.normcase(path):
                self.select(tab)
                return tab["editor"]

        editor = CodeEditor(
            self.content, path=path, on_change=self._editor_changed,
            on_cursor=self._on_cursor, app=self.app,
        )
        tab = {
            "path": path,
            "title": os.path.basename(path),
            "editor": editor,
        }
        editor.tab = tab
        self._add_tab(tab)
        self.select(tab)
        return editor

    def new_file(self, content: str = "", language: str = "python") -> CodeEditor:
        self._counter += 1
        title = f"Untitled-{self._counter}"
        editor = CodeEditor(
            self.content, path=None, on_change=self._editor_changed,
            on_cursor=self._on_cursor, app=self.app,
        )
        editor.set_content(content, language)
        tab = {"path": None, "title": title, "editor": editor}
        editor.tab = tab
        self._add_tab(tab)
        self.select(tab)
        return editor

    def _add_tab(self, tab: dict):
        width = max(118, min(240, len(tab["title"]) * 8 + 56))
        frame = ctk.CTkFrame(self.tab_strip, fg_color=COLORS["bg"],
                             corner_radius=0, height=36, width=width)
        frame.pack(side="left", fill="y", padx=(2, 0), pady=1)
        frame.pack_propagate(False)

        label = ctk.CTkLabel(
            frame, text=tab["title"], font=("Segoe UI", 11),
            text_color=COLORS["muted"], anchor="w", padx=8,
        )
        label.pack(side="left", fill="y")

        # pemisah tipis di sisi kanan tab
        separator = tk.Frame(frame, bg=COLORS["border"], width=1)
        separator.pack(side="right", fill="y")

        close = ctk.CTkButton(
            frame, text="", image=icons.ctk_icon("close", COLORS["muted"], 11),
            width=22, height=22, corner_radius=4,
            fg_color="transparent", hover_color=COLORS["bg_lighter"],
            command=lambda: self.close(tab),
        )
        close.pack(side="right", padx=(2, 6), pady=6)

        # Klik di seluruh kartu (teks, separator, area kosong, atau child
        # internal CustomTkinter) harus memindah tab. Tombol close sengaja
        # tidak ikut diikat supaya command-nya tetap berfungsi.
        self._bind_tab_click(frame, tab)
        self._bind_tab_click(label, tab, recursive=True)
        self._bind_tab_click(separator, tab)

        # Garis aksen tipis; hanya tampil pada tab aktif (diatur di select())
        indicator = tk.Frame(frame, bg=COLORS["accent"], height=2)
        tab["indicator"] = indicator

        tab["frame"] = frame
        tab["label"] = label
        tab["close"] = close
        self.tabs.append(tab)
        self.after_idle(self._update_tab_scroll)

    def select(self, tab: dict):
        if tab not in self.tabs:
            return
        if self.active:
            self.active["editor"].pack_forget()
            self.active["frame"].configure(fg_color=COLORS["bg"])
            self.active["label"].configure(text_color=COLORS["muted"])
            ind = self.active.get("indicator")
            if ind is not None:
                ind.place_forget()
        self.active = tab
        tab["editor"].pack(fill="both", expand=True)
        tab["frame"].configure(fg_color=COLORS["bg_deep"])
        tab["label"].configure(text_color=COLORS["text_bright"])
        ind = tab.get("indicator")
        if ind is not None:
            ind.place(relx=0, rely=1.0, anchor="sw", relwidth=1.0, height=2)
            ind.lift()
        self.after_idle(self._update_tab_scroll)
        self._refresh_title(tab)
        tab["editor"].focus_editor()
        self._notify_status()

    def _destroy_tab_frame(self, tab: dict):
        frame = tab.get("frame")
        if frame is not None and frame.winfo_exists():
            frame.destroy()

    def close(self, tab: dict):
        if tab not in self.tabs:
            return
        editor = tab["editor"]
        if editor.dirty:
            answer = messagebox.askyesnocancel(
                "NovaCode — Simpan perubahan?",
                f"Simpan perubahan pada '{tab['title']}'?",
            )
            if answer is None:
                return
            if answer:
                if editor.path:
                    editor.save()
                elif self.app and not self.app.save_as(editor):
                    return
                elif not self.app:
                    return

        if self.active is tab:
            idx = self.tabs.index(tab)
            self.active = None
            editor.pack_forget()
            self._destroy_tab_frame(tab)
            self.tabs.remove(tab)
            if self.tabs:
                self.select(self.tabs[min(idx, len(self.tabs) - 1)])
            else:
                self.new_file()
        else:
            self._destroy_tab_frame(tab)
            self.tabs.remove(tab)
        self.after_idle(self._update_tab_scroll)
        self._notify_status()

    def close_active(self):
        if self.active:
            self.close(self.active)

    def next_tab(self, step: int = 1):
        if len(self.tabs) < 2 or not self.active:
            return
        idx = (self.tabs.index(self.active) + step) % len(self.tabs)
        self.select(self.tabs[idx])

    # ------------------------------------------------------------------
    # Callbacks internal
    # ------------------------------------------------------------------
    def _editor_changed(self, editor: CodeEditor):
        tab = getattr(editor, "tab", None)
        if tab:
            self._refresh_title(tab)
        self._notify_status()

    def _refresh_title(self, tab: dict):
        base = tab["title"]
        text = f"● {base}" if tab["editor"].dirty else base
        tab["label"].configure(text=text)

    def _on_cursor(self, info: dict):
        if self.on_cursor:
            self.on_cursor(info)

    def _notify_status(self):
        if self.on_status:
            self.on_status(self.active_editor)
