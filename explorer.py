"""Panel file explorer (treeview folder kiri)."""

from __future__ import annotations

import os
import shutil
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import customtkinter as ctk

from . import icons
from .config import COLORS, FONT_UI_TUPLE, TOKEN_COLORS, language_for

# Warna ikon file per bahasa (mengambil warna token syntax tema aktif)
LANG_COLOR = {
    "python": "type", "javascript": "number", "typescript": "function",
    "java": "keyword", "cpp": "function", "c": "function", "go": "builtin",
    "rust": "keyword", "html": "tag", "css": "keyword2", "json": "number",
    "sql": "builtin", "bash": "string", "markdown": "comment",
}


class FileExplorer(ctk.CTkFrame):
    def __init__(self, master, on_open_file=None, on_open_terminal=None, **kwargs):
        super().__init__(master, fg_color=COLORS["bg"], corner_radius=0, **kwargs)
        self.on_open_file = on_open_file
        self.on_open_terminal = on_open_terminal
        self.root_path: str | None = None
        self.paths: dict[str, str] = {}

        self._build_style()
        self._build_icons()
        self._build_ui()
        self._build_menu()

    # ------------------------------------------------------------------
    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Nova.Treeview", background=COLORS["bg"], foreground=COLORS["text"],
            fieldbackground=COLORS["bg"], borderwidth=0, rowheight=26,
            font=FONT_UI_TUPLE,
        )
        style.configure(
            "Nova.Treeview.Heading", background=COLORS["bg_light"],
            foreground=COLORS["text_bright"], relief="flat",
        )
        style.map(
            "Nova.Treeview",
            background=[("selected", COLORS["accent_soft"])],
            foreground=[("selected", COLORS["text_bright"])],
        )
        style.configure(
            "Vertical.TScrollbar", background=COLORS["bg_lighter"],
            troughcolor=COLORS["bg"], bordercolor=COLORS["bg"],
            arrowcolor=COLORS["muted"], relief="flat", gripcount=0,
        )
        style.map("Vertical.TScrollbar",
                  background=[("active", COLORS["muted"])])

    def _build_icons(self):
        self._img_folder = icons.tk_icon("folder", COLORS["muted"], 16)
        self._img_root = icons.tk_icon("folder_open", COLORS["accent"], 16)
        self._file_imgs: dict[str, object] = {}

    def _file_image(self, lang: str):
        key = LANG_COLOR.get(lang)
        color = TOKEN_COLORS.get(key, COLORS["muted"]) if key else COLORS["muted"]
        if color not in self._file_imgs:
            self._file_imgs[color] = icons.tk_icon("file", color, 16)
        return self._file_imgs[color]

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=34, corner_radius=0)
        header.pack(fill="x", padx=10, pady=(8, 0))
        ctk.CTkLabel(
            header, text="EXPLORER", font=("Segoe UI", 10, "bold"),
            text_color=COLORS["muted"], anchor="w",
        ).pack(side="left")
        ctk.CTkButton(
            header, text="", image=icons.ctk_icon("refresh", COLORS["muted"], 14),
            width=26, height=24, corner_radius=4,
            fg_color="transparent", hover_color=COLORS["bg_light"],
            command=self.refresh,
        ).pack(side="right", padx=2)

        # Pemilih root: langsung tampilkan semua file user, atau pilih folder tertentu
        roots = ctk.CTkFrame(self, fg_color="transparent")
        roots.pack(fill="x", padx=8, pady=(4, 2))
        ctk.CTkButton(
            roots, text="Home", image=icons.ctk_icon("home", COLORS["muted"], 14),
            compound="left", width=72, height=26, corner_radius=4,
            font=FONT_UI_TUPLE, fg_color="transparent", hover_color=COLORS["bg_light"],
            border_width=1, border_color=COLORS["border"], text_color=COLORS["text"],
            command=self.go_home,
        ).pack(side="left", padx=(2, 4))
        ctk.CTkButton(
            roots, text="Pilih folder",
            image=icons.ctk_icon("folder_open", COLORS["muted"], 14),
            compound="left", width=104, height=26, corner_radius=4,
            font=FONT_UI_TUPLE, fg_color="transparent", hover_color=COLORS["bg_light"],
            border_width=1, border_color=COLORS["border"], text_color=COLORS["text"],
            command=self.open_folder_dialog,
        ).pack(side="left", padx=2)
        self.root_label = ctk.CTkButton(
            roots, text="—", height=26, font=FONT_UI_TUPLE, anchor="w",
            fg_color="transparent", hover_color=COLORS["bg_light"],
            text_color=COLORS["muted"], command=self._copy_root,
        )
        self.root_label.pack(side="left", fill="x", expand=True, padx=(4, 0))

        self.tree = ttk.Treeview(self, style="Nova.Treeview", show="tree", selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=(6, 0), pady=(2, 6))

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y", pady=(2, 6))
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.tag_configure("rowhover", background=COLORS["bg_light"],
                                foreground=COLORS["text_bright"])
        self._hover_row = None
        self.tree.bind("<<TreeviewOpen>>", self._on_open_item)
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<Button-3>", self._on_right_click)
        self.tree.bind("<Motion>", self._on_row_hover)
        self.tree.bind("<Leave>", lambda e: self._clear_row_hover())

    def _clear_row_hover(self):
        if self._hover_row:
            try:
                self.tree.item(self._hover_row, tags=())
            except Exception:
                pass
            self._hover_row = None

    def _on_row_hover(self, event):
        row = self.tree.identify_row(event.y)
        if row == self._hover_row:
            return
        self._clear_row_hover()
        if row:
            self._hover_row = row
            self.tree.item(row, tags=("rowhover",))

    def _build_menu(self):
        self.menu = tk.Menu(self, tearoff=0, bg=COLORS["bg_light"],
                            fg=COLORS["text"], activebackground=COLORS["accent"],
                            activeforeground=COLORS["white"], bd=0,
                            font=FONT_UI_TUPLE)
        self.menu.add_command(label="Buka file", command=self._menu_open)
        self.menu.add_command(label="Buka di Terminal", command=self._menu_terminal)
        self.menu.add_separator()
        self.menu.add_command(label="File baru", command=self._new_file)
        self.menu.add_command(label="Folder baru", command=self._new_folder)
        self.menu.add_separator()
        self.menu.add_command(label="Ganti nama", command=self._rename)
        self.menu.add_command(label="Salin path", command=self._copy_path)
        self.menu.add_command(label="Hapus", command=self._delete)

    # ------------------------------------------------------------------
    def set_root(self, path: str):
        self.root_path = path
        name = os.path.basename(path.rstrip("\\/")) or path
        if hasattr(self, "root_label"):
            self.root_label.configure(text=name[:22])
        self.refresh()

    def go_home(self):
        """Tampilkan seluruh isi folder user (C:\\Users\\<nama>) langsung."""
        home = os.path.expanduser("~")
        self.set_root(home)
        if self.app_ref:
            self.app_ref.set_cwd(home)
            self.app_ref.set_title_path(home)

    def _copy_root(self):
        if self.root_path:
            self.clipboard_clear()
            self.clipboard_append(self.root_path)

    def open_folder_dialog(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Pilih folder proyek")
        if folder:
            self.set_root(folder)
            if self.app_ref:
                self.app_ref.set_cwd(folder)
                self.app_ref.set_title_path(folder)

    @property
    def app_ref(self):
        return getattr(self, "_app", None)

    def set_app(self, app):
        self._app = app

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.paths.clear()
        if not self.root_path or not os.path.isdir(self.root_path):
            return
        root = self.tree.insert(
            "", "end", text=" " + (os.path.basename(self.root_path) or self.root_path),
            image=self._img_root, open=True)
        self.paths[root] = self.root_path
        self._populate(root, self.root_path)

    def _populate(self, parent: str, path: str):
        try:
            entries = list(os.scandir(path))
        except OSError:
            return
        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
        for entry in entries:
            # Semua file/folder ditampilkan, termasuk yang tersembunyi,
            # supaya user bisa langsung memilih dan mengedit apa saja.
            if entry.is_dir():
                item = self.tree.insert(parent, "end", text=" " + entry.name,
                                        image=self._img_folder)
                self.paths[item] = entry.path
                # dummy child agar arrow expand muncul
                self.tree.insert(item, "end", text="")
            else:
                lang = language_for(entry.name)
                item = self.tree.insert(parent, "end", text=" " + entry.name,
                                        image=self._file_image(lang))
                self.paths[item] = entry.path

    def _on_open_item(self, event):
        item = self.tree.focus()
        path = self.paths.get(item)
        if not path or not os.path.isdir(path):
            return
        # hapus semua children lalu isi ulang (termasuk dummy)
        for child in self.tree.get_children(item):
            self.tree.delete(child)
        self._populate(item, path)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        path = self.paths.get(item)
        if path and os.path.isfile(path):
            if self.on_open_file:
                self.on_open_file(path)

    # ------------------------------------------------------------------
    # Context menu actions
    # ------------------------------------------------------------------
    def _selected_path(self):
        item = self.tree.focus()
        return self.paths.get(item), item

    def _context_target_dir(self):
        path, _ = self._selected_path()
        if not path:
            return self.root_path
        return path if os.path.isdir(path) else os.path.dirname(path)

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.tree.focus(item)
        self.menu.tk_popup(event.x_root, event.y_root)

    def _menu_open(self):
        path, _ = self._selected_path()
        if path and os.path.isfile(path) and self.on_open_file:
            self.on_open_file(path)

    def _menu_terminal(self):
        target = self._context_target_dir()
        if target and self.on_open_terminal:
            self.on_open_terminal(target)

    def _new_file(self):
        base = self._context_target_dir()
        if not base:
            return
        name = simpledialog.askstring("File baru", "Nama file:", parent=self)
        if not name:
            return
        path = os.path.join(base, name)
        if os.path.exists(path):
            messagebox.showwarning("NovaCode", "File sudah ada.")
            return
        try:
            with open(path, "w", encoding="utf-8"):
                pass
        except OSError as exc:
            messagebox.showerror("NovaCode", str(exc))
            return
        self.refresh()
        if self.on_open_file:
            self.on_open_file(path)

    def _new_folder(self):
        base = self._context_target_dir()
        if not base:
            return
        name = simpledialog.askstring("Folder baru", "Nama folder:", parent=self)
        if not name:
            return
        try:
            os.makedirs(os.path.join(base, name), exist_ok=False)
        except OSError as exc:
            messagebox.showerror("NovaCode", str(exc))
            return
        self.refresh()

    def _rename(self):
        path, _ = self._selected_path()
        if not path or path == self.root_path:
            return
        name = simpledialog.askstring("Ganti nama", "Nama baru:",
                                      initialvalue=os.path.basename(path), parent=self)
        if not name:
            return
        target = os.path.join(os.path.dirname(path), name)
        try:
            os.rename(path, target)
        except OSError as exc:
            messagebox.showerror("NovaCode", str(exc))
            return
        self.refresh()

    def _copy_path(self):
        path, _ = self._selected_path()
        if path:
            self.clipboard_clear()
            self.clipboard_append(path)

    def _delete(self):
        path, _ = self._selected_path()
        if not path or path == self.root_path:
            return
        if not messagebox.askyesno("NovaCode", f"Hapus '{os.path.basename(path)}'?"):
            return
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as exc:
            messagebox.showerror("NovaCode", str(exc))
            return
        self.refresh()
