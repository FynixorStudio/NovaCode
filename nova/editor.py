

from __future__ import annotations

import os
import re
import tkinter as tk
from tkinter import messagebox

from .completions import describe, get_completions
from .config import COLORS, COMMON_WORDS, FONT_MONO_TUPLE, language_for
from .syntax import SyntaxHighlighter, configure_tags


PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'", "`": "`"}
CLOSERS = set(PAIRS.values())


class CodeEditor(tk.Frame):
    

    def __init__(self, master, path: str | None = None, on_change=None,
                 on_cursor=None, app=None):
        super().__init__(master, bg=COLORS["bg_deep"])
        self.path = path
        self.app = app
        self.on_change = on_change
        self.on_cursor = on_cursor
        self.language = language_for(path)
        self.dirty = False
        self.encoding = "utf-8"
        self._highlight_job = None
        self._ac_job = None
        self._suppress_complete_once = False
        self._completion = None          
        self._current_line_tag = None
        self._last_cursor = "1.0"
        self._highlighter = SyntaxHighlighter()
        self._word_cache: set[str] = set()
        self._word_cache_dirty = True

        self._build_widgets()
        self._bind_events()
        self.configure_tags_once()
        self.update_line_numbers()
        self._update_cursor()
        if path and os.path.isfile(path):
            self.load(path)

    
    def _build_widgets(self):
        bg = COLORS["bg_deep"]
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.gutter = tk.Text(
            self, width=5, wrap="none", bg=COLORS["gutter"], fg=COLORS["muted"],
            font=FONT_MONO_TUPLE, relief="flat", bd=0, padx=6, pady=6,
            takefocus=0, highlightthickness=0, state="disabled",
        )
        self.gutter.grid(row=0, column=0, sticky="ns")

        self.text = tk.Text(
            self, wrap="none", bg=bg, fg=COLORS["text"],
            insertbackground=COLORS["text_bright"],
            selectbackground=COLORS["selection"], selectforeground=COLORS["text_bright"],
            font=FONT_MONO_TUPLE, relief="flat", bd=0, padx=8, pady=6,
            undo=True, autoseparators=True, maxundo=-1,
            highlightthickness=0, tabs="    ",
        )
        self.text.grid(row=0, column=1, sticky="nsew")

        self.vbar = tk.Scrollbar(
            self, orient="vertical", command=self._yview,
            bg=COLORS["bg_light"], troughcolor=bg,
            activebackground=COLORS["bg_lighter"], highlightthickness=0, bd=0,
        )
        self.vbar.grid(row=0, column=2, sticky="ns")

        self.hbar = tk.Scrollbar(
            self, orient="horizontal", command=self.text.xview,
            bg=COLORS["bg_light"], troughcolor=bg,
            activebackground=COLORS["bg_lighter"], highlightthickness=0, bd=0,
        )
        self.hbar.grid(row=1, column=1, sticky="ew")

        self.text.configure(yscrollcommand=self._yscroll, xscrollcommand=self.hbar.set)

    def configure_tags_once(self):
        configure_tags(self.text)
        self.text.tag_configure("currentline", background=COLORS["current_line"])
        self.text.tag_lower("currentline")
        self.text.tag_configure(
            "diagnostic", background=COLORS["red_soft"],
            underline=True, underlinefg=COLORS["red"])
        self.gutter.tag_configure(
            "diagnostic", foreground=COLORS["red"], background=COLORS["red_soft"])

    def _bind_events(self):
        t = self.text
        t.bind("<<Modified>>", self._on_modified)
        t.bind("<KeyPress>", self._on_key_press)
        t.bind("<KeyRelease>", self._on_key_release)
        t.bind("<ButtonRelease-1>", lambda e: self._update_cursor())
        t.bind("<Control-Home>", lambda e: self._go_start())
        t.bind("<Control-End>", lambda e: self._go_end())
        
        self.winfo_toplevel().bind("<Button-1>", lambda e: self._close_completion(), add="+")

    def _yview(self, *args):
        self.text.yview(*args)
        self.gutter.yview(*args)

    def _yscroll(self, *args):
        
        self.vbar.set(*args)
        if args:
            self.gutter.yview("moveto", args[0])

    
    def load(self, path: str):
        
        self.path = path
        self.language = language_for(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self.encoding = "utf-8"
        except UnicodeDecodeError:
            with open(path, "r", encoding="latin-1") as f:
                content = f.read()
            self.encoding = "latin-1"
        except OSError as exc:
            messagebox.showerror("NovaCode", f"Gagal membuka file:\n{exc}")
            return

        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.mark_set("insert", "1.0")
        self.text.see("1.0")
        self.text.edit_modified(False)
        self.dirty = False
        self._word_cache_dirty = True
        self.update_line_numbers()
        self.schedule_highlight()
        self._update_cursor()
        self._notify_change()

    def set_content(self, content: str, language: str | None = None):
        self.text.delete("1.0", "end")
        self.text.insert("1.0", content)
        self.text.mark_set("insert", "1.0")
        self.text.see("1.0")
        self.text.edit_modified(False)
        self.dirty = False
        if language:
            self.language = language
        self._word_cache_dirty = True
        self.update_line_numbers()
        self.schedule_highlight()
        self._update_cursor()
        self._notify_change()

    def get_content(self) -> str:
        return self.text.get("1.0", "end-1c")

    def save(self, path: str | None = None) -> bool:
        target = path or self.path
        if not target:
            return False
        try:
            with open(target, "w", encoding=self.encoding, newline="") as f:
                f.write(self.get_content())
        except OSError as exc:
            messagebox.showerror("NovaCode", f"Gagal menyimpan file:\n{exc}")
            return False
        self.path = target
        self.language = language_for(target)
        self.dirty = False
        self._notify_change()
        return True

    
    def _on_modified(self, event=None):
        if not self.text.edit_modified():
            return
        self.text.edit_modified(False)
        self.dirty = True
        self.clear_diagnostics()
        self.update_line_numbers()
        self.schedule_highlight()
        self._word_cache_dirty = True
        self._notify_change()

    def _notify_change(self):
        if self.on_change:
            self.on_change(self)

    
    def clear_diagnostics(self):
        self.text.tag_remove("diagnostic", "1.0", "end")
        self.gutter.configure(state="normal")
        self.gutter.tag_remove("diagnostic", "1.0", "end")
        self.gutter.configure(state="disabled")

    def show_diagnostics(self, diags):
        
        self.clear_diagnostics()
        if not self.path:
            return
        target = os.path.normcase(os.path.abspath(self.path))
        total = int(self.text.index("end-1c").split(".")[0])
        for diag in diags:
            diag_file = getattr(diag, "file", "")
            if not diag_file:
                continue
            if os.path.normcase(os.path.abspath(diag_file)) != target:
                continue
            line = max(1, min(int(getattr(diag, "line", 1) or 1), total))
            self.text.tag_add("diagnostic", f"{line}.0", f"{line}.end")
            self.gutter.configure(state="normal")
            self.gutter.tag_add("diagnostic", f"{line}.0", f"{line}.end")
            self.gutter.configure(state="disabled")
        self.text.tag_raise("diagnostic")

    def update_line_numbers(self):
        total = int(self.text.index("end-1c").split(".")[0])
        nums = "\n".join(str(i) for i in range(1, total + 1))
        self.gutter.configure(state="normal")
        self.gutter.delete("1.0", "end")
        self.gutter.insert("1.0", nums)
        self.gutter.configure(state="disabled")

    def schedule_highlight(self, delay: int = 160):
        if self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(
            delay, lambda: self._highlighter.highlight(
                self.text, self.get_content(), self.language))

    def highlight_now(self):
        self._highlighter.highlight(self.text, self.get_content(), self.language)

    def _update_cursor(self):
        index = self.text.index("insert")
        self._last_cursor = index
        line = int(index.split(".")[0])
        col = int(index.split(".")[1]) + 1

        
        if self._current_line_tag:
            self.text.tag_remove("currentline", *self._current_line_tag)
        self._current_line_tag = (f"{line}.0", f"{line}.end")
        self.text.tag_add("currentline", *self._current_line_tag)

        if self.on_cursor:
            self.on_cursor({"line": line, "col": col, "editor": self})

    
    def _on_key_press(self, event):
        
        if self._completion and event.keysym in ("Up", "Down", "Tab", "Return", "Escape"):
            return self._completion_key(event)

        ctrl = event.state & 0x0004
        shift = event.state & 0x0001
        alt = event.state & 0x0008

        
        if not ctrl and not alt:
            paired = self._auto_pair(event)
            if paired is not None:
                return paired

        if ctrl and event.keysym == "slash":
            self.toggle_comment()
            return "break"
        if ctrl and event.keysym.lower() == "d" and not shift:
            self.duplicate_line()
            return "break"
        if ctrl and shift and event.keysym.lower() == "k":
            self.delete_line()
            return "break"
        if ctrl and event.keysym == "space":
            self.show_completion(force=True)
            return "break"
        if shift and event.keysym == "Tab":
            self.indent_selection(dedent=True)
            return "break"
        if event.keysym == "Tab":
            self.indent_selection()
            return "break"
        if event.keysym == "Return":
            self._newline_with_indent()
            self.after(60, self._maybe_complete)
            return "break"
        if event.keysym == "Escape":
            self._close_completion()
        return None

    def _auto_pair(self, event):
        
        t = self.text
        keysym = event.keysym

        
        if keysym in ("BackSpace", "Delete"):
            index = t.index("insert")
            if keysym == "BackSpace" and index == "1.0":
                return None
            prev = t.get("insert-1c", "insert")
            nxt = t.get("insert", "insert+1c")

            
            if (prev in "\"'" and nxt == prev
                    and t.get("insert-3c", "insert") == prev * 3
                    and t.get("insert", "insert+3c") == prev * 3):
                t.delete("insert-3c", "insert+3c")
                return "break"

            if keysym == "BackSpace" and prev in CLOSERS:
                before_prev = t.get("insert-2c", "insert-1c")
                if any(cl == prev and op == before_prev for op, cl in PAIRS.items()):
                    t.delete("insert-2c", "insert")
                    return "break"

            if prev in PAIRS and PAIRS[prev] == nxt:
                t.delete("insert-1c", "insert+1c")
                return "break"
            return None

        ch = event.char
        if not ch or len(ch) != 1:
            return None

        
        if ch in CLOSERS:
            nxt = t.get("insert", "insert+1c")
            if nxt == ch:
                t.mark_set("insert", "insert+1c")
                return "break"

        opening = PAIRS.get(ch)
        if not opening:
            return None
        
        if ch in "\"'`" and self._inside_comment_or_string():
            return None

        
        if ch in "\"'" and t.get("insert-2c", "insert") == ch * 2:
            t.insert("insert", ch * 4)
            t.mark_set("insert", "insert-3c")
            return "break"

        if t.tag_ranges("sel"):
            start, end = t.index("sel.first"), t.index("sel.last")
            selected = t.get(start, end)
            t.delete(start, end)
            combined = ch + selected + opening
            t.insert(start, combined)
            t.mark_set("insert", t.index(f"{start}+{len(ch) + len(selected)}c"))
        else:
            index = t.index("insert")
            t.insert(index, ch + opening)
            t.mark_set("insert", f"{index}+1c")
        t.see("insert")
        return "break"

    def _on_key_release(self, event):
        self._update_cursor()
        if event.keysym not in ("Up", "Down", "Left", "Right", "Shift_L", "Shift_R",
                                "Control_L", "Control_R", "Alt_L", "Alt_R"):
            self._maybe_complete()

    def _newline_with_indent(self):
        t = self.text
        if t.tag_ranges("sel"):
            t.delete("sel.first", "sel.last")
        index = t.index("insert")
        line_index = index.split(".")[0]
        line_text = t.get(f"{line_index}.0", f"{line_index}.end")
        indent = re.match(r"[ \t]*", line_text).group(0)

        
        prev = t.get("insert-1c", "insert") if index != "1.0" else ""
        nxt = t.get("insert", "insert+1c")
        if prev in PAIRS and PAIRS[prev] == nxt:
            t.insert("insert", "\n" + indent + "    " + "\n" + indent)
            t.mark_set("insert", f"insert-{len(indent) + 1}c")
            t.see("insert")
            return

        stripped = line_text.rstrip()
        if stripped.endswith((":", "{", "(", "[")):
            indent += "    "
        t.insert("insert", "\n" + indent)
        t.see("insert")

    def indent_selection(self, dedent: bool = False):
        t = self.text
        if t.tag_ranges("sel"):
            first = int(t.index("sel.first").split(".")[0])
            last = int(t.index("sel.last").split(".")[0])
            if t.index("sel.last").endswith(".0"):
                last -= 1
            for n in range(first, last + 1):
                start = f"{n}.0"
                line = t.get(start, f"{n}.end")
                if dedent:
                    if line.startswith("    "):
                        t.delete(start, f"{n}.4")
                    elif line.startswith("\t"):
                        t.delete(start, f"{n}.1")
                else:
                    t.insert(start, "    ")
        elif dedent:
            line_no = int(t.index("insert").split(".")[0])
            start = f"{line_no}.0"
            if t.get(start, f"{line_no}.4") == "    ":
                t.delete(start, f"{line_no}.4")
        else:
            t.insert("insert", "    ")

    def toggle_comment(self):
        t = self.text
        langdef = COMMON_WORDS.get(self.language, COMMON_WORDS["text"])
        marker = langdef["line_comment"]
        if not marker:
            marker_open, marker_close = langdef["block_comment"]
            if not marker_open:
                return
        if t.tag_ranges("sel"):
            first = int(t.index("sel.first").split(".")[0])
            last = int(t.index("sel.last").split(".")[0])
            if t.index("sel.last").endswith(".0"):
                last -= 1
        else:
            first = last = int(t.index("insert").split(".")[0])

        for n in range(first, last + 1):
            start = f"{n}.0"
            line = t.get(start, f"{n}.end")
            stripped = line.lstrip()
            pos = len(line) - len(stripped)
            if marker and stripped.startswith(marker):
                t.delete(f"{n}.{pos}", f"{n}.{pos + len(marker)}")
            elif not marker and stripped.startswith(marker_open):
                t.delete(f"{n}.{pos}", f"{n}.{pos + len(marker_open)}")
                endpos = len(line) - len(stripped) + len(marker_close)
                t.delete(f"{n}.{endpos - len(marker_close)}", f"{n}.{endpos}")
            else:
                if marker:
                    t.insert(f"{n}.{pos}", marker)
                else:
                    t.insert(f"{n}.{len(line)}", " " + marker_close)
                    t.insert(f"{n}.{pos}", marker_open)

    def duplicate_line(self):
        t = self.text
        line_no = int(t.index("insert").split(".")[0])
        content = t.get(f"{line_no}.0", f"{line_no}.end")
        t.insert(f"{line_no + 1}.0", content + "\n")
        t.see("insert")

    def delete_line(self):
        t = self.text
        line_no = int(t.index("insert").split(".")[0])
        t.delete(f"{line_no}.0", f"{line_no + 1}.0")
        t.see("insert")

    def move_line(self, direction: int):
        t = self.text
        line_no = int(t.index("insert").split(".")[0])
        target = line_no + direction
        if target < 1:
            return
        total = int(t.index("end-1c").split(".")[0])
        if target > total:
            return
        content = t.get(f"{line_no}.0", f"{line_no}.end")
        t.delete(f"{line_no}.0", f"{line_no + 1}.0")
        t.insert(f"{target}.0", content + "\n")
        t.mark_set("insert", f"{target}.{min(len(content), 80)}")
        t.see("insert")

    def goto_line(self, line: int):
        line = max(1, min(line, int(self.text.index("end-1c").split(".")[0])))
        self.text.mark_set("insert", f"{line}.0")
        self.text.see("insert")
        self._update_cursor()
        self.text.focus_set()

    def _go_start(self):
        self.text.mark_set("insert", "1.0")
        self.text.see("1.0")
        self._update_cursor()

    def _go_end(self):
        self.text.mark_set("insert", "end-1c")
        self.text.see("end-1c")
        self._update_cursor()

    
    def find_all(self, needle: str, case_sensitive: bool = False,
                 whole_word: bool = False):
        if not needle:
            return []
        content = self.get_content()
        flags = 0 if case_sensitive else re.IGNORECASE
        pattern = re.escape(needle)
        if whole_word:
            pattern = r"\b" + pattern + r"\b"
        matches = []
        for m in re.finditer(pattern, content, flags):
            start = self.text.index(f"1.0+{m.start()}c")
            end = self.text.index(f"1.0+{m.end()}c")
            matches.append((start, end))
        return matches

    def show_matches(self, matches, current: int = 0):
        self.text.tag_remove("search", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")
        for idx, (start, end) in enumerate(matches):
            self.text.tag_add("search", start, end)
            if idx == current and matches:
                self.text.tag_add("search_current", start, end)
                self.text.see(start)
        self.text.tag_raise("search_current")
        self.text.tag_raise("search")

    def clear_matches(self):
        self.text.tag_remove("search", "1.0", "end")
        self.text.tag_remove("search_current", "1.0", "end")

    def replace_one(self, start: str, end: str, replacement: str):
        self.text.delete(start, end)
        self.text.insert(start, replacement)

    
    def _collect_words(self) -> set[str]:
        if not self._word_cache_dirty:
            return self._word_cache
        words: set[str] = set()
        langdef = COMMON_WORDS.get(self.language, COMMON_WORDS["text"])
        words.update(w for w in langdef["keywords"] if len(w) >= 2)
        words.update(w for w in langdef["builtins"] if len(w) >= 2)
        content = self.get_content()
        
        words.update(w for w in re.findall(r"[A-Za-z_]\w{2,}", content))
        self._word_cache = {w for w in words if len(w) >= 2}
        self._word_cache_dirty = False
        return self._word_cache

    def _current_prefix(self) -> str:
        t = self.text
        line = t.index("insert").split(".")[0]
        col = int(t.index("insert").split(".")[1])
        line_text = t.get(f"{line}.0", f"{line}.{col}")
        m = re.search(r"[A-Za-z_]\w*$", line_text)
        return m.group(0) if m else ""

    def _inside_comment_or_string(self) -> bool:
        
        t = self.text
        index = t.index("insert")
        line, _col = index.split(".")
        before = t.get(f"{line}.0", index)
        langdef = COMMON_WORDS.get(self.language, COMMON_WORDS["text"])
        marker = langdef["line_comment"]
        if marker and marker in before:
            return True
        for quote in langdef["strings"]:
            if len(quote) == 1 and before.count(quote) % 2 == 1:
                return True
        return False

    def _maybe_complete(self):
        
        if self._suppress_complete_once:
            self._suppress_complete_once = False
            self._close_completion()
            return
        if self._ac_job:
            try:
                self.after_cancel(self._ac_job)
            except Exception:
                pass
        self._ac_job = self.after(70, self._complete_now)

    def _complete_now(self):
        self._ac_job = None
        prefix = self._current_prefix()
        if not prefix or self._inside_comment_or_string():
            self._close_completion()
            return
        self.show_completion(force=False)

    def show_completion(self, force: bool = False):
        prefix = self._current_prefix()
        if not prefix and not force:
            self._close_completion()
            return
        if prefix and self._inside_comment_or_string():
            self._close_completion()
            return

        matches = get_completions(
            self.language, prefix, document_words=self._collect_words(), limit=14)
        if force and not prefix and not matches:
            matches = get_completions(self.language, "", (), limit=14)
        if not matches:
            self._close_completion()
            return

        popup = self._completion["popup"] if self._completion else None
        if self._completion:
            listbox = self._completion["listbox"]
        else:
            popup = tk.Toplevel(self)
            popup.withdraw()
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            listbox = tk.Listbox(
                popup, height=min(len(matches), 12), width=30,
                bg=COLORS["bg_light"], fg=COLORS["text"],
                selectbackground=COLORS["accent"], selectforeground=COLORS["white"],
                font=FONT_MONO_TUPLE, relief="flat", bd=1,
                highlightthickness=0, exportselection=False, activestyle="none",
            )
            listbox.pack(side="left", padx=(2, 0), pady=2)
            listbox.bind("<ButtonRelease-1>", lambda e: self._accept_completion())
            listbox.bind("<<ListboxSelect>>", self._show_item_help)
            scroll = tk.Scrollbar(popup, orient="vertical", command=listbox.yview,
                                  bg=COLORS["bg_lighter"], troughcolor=COLORS["bg_light"],
                                  highlightthickness=0, bd=0, width=8)
            scroll.pack(side="right", fill="y", padx=(0, 2), pady=2)
            listbox.configure(yscrollcommand=scroll.set)
            help_lbl = tk.Label(
                popup, text="", anchor="w", justify="left", wraplength=360,
                bg=COLORS["bg_deep"], fg=COLORS["muted"],
                font=("Segoe UI", 9), padx=10, pady=5,
            )
            help_lbl.pack(fill="x")
            self._completion = {"popup": popup, "listbox": listbox,
                                "help": help_lbl, "prefix_len": len(prefix),
                                "items": []}

        listbox.delete(0, "end")
        for item in matches:
            listbox.insert("end", item.word)
        listbox.selection_clear(0, "end")
        listbox.selection_set(0)
        listbox.activate(0)
        self._completion["items"] = matches
        self._completion["prefix_len"] = len(prefix)
        self._show_item_help()

        
        self.update_idletasks()
        bbox = self.text.bbox("insert")
        if bbox:
            x, y, w, h = bbox
            sx = self.text.winfo_rootx() + x
            sy = self.text.winfo_rooty() + y + h + 2
        else:
            sx = self.text.winfo_rootx() + 20
            sy = self.text.winfo_rooty() + 20
        if popup is not None:
            try:
                popup.geometry(f"+{sx}+{sy}")
                popup.deiconify()
                popup.lift()
            except Exception:
                pass

    def _show_item_help(self, _event=None):
        
        comp = self._completion
        if not comp:
            return
        sel = comp["listbox"].curselection()
        if not sel:
            return
        comp["help"].configure(text=describe(comp["items"][sel[0]], self.language))

    def _completion_key(self, event):
        comp = self._completion
        listbox = comp["listbox"]
        items = comp["items"]
        if event.keysym == "Escape":
            self._suppress_complete_once = True
            self._close_completion()
            return "break"
        if event.keysym == "Down":
            sel = listbox.curselection()
            idx = (sel[0] + 1) % len(items) if sel else 0
            listbox.selection_clear(0, "end")
            listbox.selection_set(idx)
            listbox.activate(idx)
            listbox.see(idx)
            return "break"
        if event.keysym == "Up":
            sel = listbox.curselection()
            idx = (sel[0] - 1) % len(items) if sel else len(items) - 1
            listbox.selection_clear(0, "end")
            listbox.selection_set(idx)
            listbox.activate(idx)
            listbox.see(idx)
            return "break"
        if event.keysym in ("Tab", "Return"):
            self._accept_completion()
            return "break"
        return None

    def _accept_completion(self):
        comp = self._completion
        self._suppress_complete_once = True
        if not comp:
            return
        sel = comp["listbox"].curselection()
        if not sel:
            self._close_completion()
            return
        item = comp["items"][sel[0]]
        prefix_len = comp["prefix_len"]
        index = self.text.index("insert")
        line, col = index.split(".")
        start = f"{line}.{max(0, int(col) - prefix_len)}"
        self.text.delete(start, index)

        template = item.insert if item.insert is not None else item.word
        if "{cursor}" in template:
            offset = template.index("{cursor}")
            text = template.replace("{cursor}", "")
        else:
            offset, text = len(template), template
        self.text.insert(start, text)
        if template != text:
            self.text.mark_set("insert", self.text.index(f"{start}+{offset}c"))
        self.text.see("insert")
        self._close_completion()
        self._update_cursor()

    def _close_completion(self):
        if self._ac_job:
            try:
                self.after_cancel(self._ac_job)
            except Exception:
                pass
            self._ac_job = None
        if self._completion:
            try:
                self._completion["popup"].destroy()
            except Exception:
                pass
            self._completion = None

    
    def focus_editor(self):
        self.text.focus_set()
