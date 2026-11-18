"""Mesin syntax highlighting ringan berbasis scanner karakter.

Tidak bergantung pada Pygments, sehingga aplikasi tetap mudah di-build ke .exe
dan bisa memberi warna pada banyak bahasa sekaligus.
"""

from __future__ import annotations

from tkinter import Text

from .config import COMMON_WORDS, FONT_MONO, FONT_SIZE, TOKEN_COLORS

# Tag yang dipakai scanner (search sengaja tidak dihapus saat re-highlight)
TOKEN_TAGS = [
    "keyword", "keyword2", "string", "number", "comment", "function", "class",
    "builtin", "decorator", "operator", "punct", "type", "tag", "attr",
    "css_prop", "css_value", "json_key",
]


def configure_tags(widget: Text) -> None:
    """Daftarkan konfigurasi warna tag ke widget Text sekali saat dibuat."""
    for name, color in TOKEN_COLORS.items():
        opts = {"foreground": color}
        if name == "comment":
            opts["font"] = (FONT_MONO, FONT_SIZE, "italic")
        if name in ("search", "search_current"):
            opts = {"background": color, "foreground": "#0d1117"}
        widget.tag_configure(name, **opts)
    # Prioritas: search di atas token, current line di bawah token
    widget.tag_raise("search_current")
    widget.tag_raise("search")
    try:
        widget.tag_lower("currentline")
    except Exception:
        pass


class SyntaxHighlighter:
    """Memindai teks dan menerapkan tag warna ke widget Text."""

    def highlight(self, widget: Text, content: str, language: str) -> None:
        for tag in TOKEN_TAGS:
            widget.tag_remove(tag, "1.0", "end")

        langdef = COMMON_WORDS.get(language, COMMON_WORDS["text"])
        for line_no, start, end, tag in self.tokenize(content, language, langdef):
            widget.tag_add(tag, f"{line_no}.{start}", f"{line_no}.{end}")

    # ------------------------------------------------------------------
    def tokenize(self, content: str, language: str, langdef: dict):
        """Yield (line_no, col_start, col_end, tag_name)."""
        keywords = set(langdef["keywords"])
        builtins = set(langdef["builtins"])
        line_comment = langdef["line_comment"]
        bc_open, bc_close = langdef["block_comment"]
        strings = langdef["strings"]

        # state untuk string/comment yang melewati beberapa baris
        active_block_close: str | None = None
        active_triple: str | None = None

        for lineno, line in enumerate(content.split("\n"), start=1):
            i, n = 0, len(line)

            while i < n:
                # --- lanjutkan block comment / triple string dari baris lalu ---
                if active_triple:
                    pos = line.find(active_triple, i)
                    if pos == -1:
                        yield lineno, i, n, "string"
                        i = n
                    else:
                        end = pos + len(active_triple)
                        yield lineno, i, end, "string"
                        i, active_triple = end, None
                    continue

                if active_block_close:
                    pos = line.find(active_block_close, i)
                    if pos == -1:
                        yield lineno, i, n, "comment"
                        i = n
                    else:
                        end = pos + len(active_block_close)
                        yield lineno, i, end, "comment"
                        i, active_block_close = end, None
                    continue

                ch = line[i]

                # --- komentar satu baris ---
                if line_comment and line.startswith(line_comment, i):
                    yield lineno, i, n, "comment"
                    break

                # --- komentar blok ---
                if bc_open and line.startswith(bc_open, i):
                    pos = line.find(bc_close, i + len(bc_open)) if bc_close else -1
                    if pos == -1:
                        yield lineno, i, n, "comment"
                        active_block_close = bc_close or ""
                        i = n
                    else:
                        end = pos + len(bc_close)
                        yield lineno, i, end, "comment"
                        i = end
                    continue

                # --- string ---
                string_hit = False
                for quote in strings:
                    if not line.startswith(quote, i):
                        continue
                    if len(quote) > 1:  # triple quote -> bisa multiline
                        pos = line.find(quote, i + len(quote))
                        if pos == -1:
                            yield lineno, i, n, "string"
                            active_triple = quote
                            i = n
                        else:
                            end = pos + len(quote)
                            yield lineno, i, end, "string"
                            i = end
                    else:
                        j = i + 1
                        while j < n:
                            if line[j] == "\\":
                                j += 2
                                continue
                            if line[j] == quote:
                                j += 1
                                break
                            j += 1
                        yield lineno, i, j, "string"
                        i = j
                    string_hit = True
                    break
                if string_hit:
                    continue

                # --- HTML / XML: tag & atribut ---
                if language == "html":
                    if ch == "<":
                        pos = line.find(">", i)
                        if pos == -1:
                            yield lineno, i, n, "tag"
                            i = n
                        else:
                            yield lineno, i, pos + 1, "tag"
                            i = pos + 1
                        continue

                # --- dekorator (@staticmethod, @app.route) ---
                if ch == "@" and i + 1 < n and (line[i + 1].isalpha() or line[i + 1] == "_"):
                    j = i + 1
                    while j < n and (line[j].isalnum() or line[j] in "_."):
                        j += 1
                    yield lineno, i, j, "decorator"
                    i = j
                    continue

                # --- angka ---
                if ch.isdigit():
                    j = i
                    while j < n and (line[j].isalnum() or line[j] in "._"):
                        j += 1
                    yield lineno, i, j, "number"
                    i = j
                    continue

                # --- identifier / keyword / fungsi / tipe ---
                if ch.isalpha() or ch == "_":
                    j = i
                    while j < n and (line[j].isalnum() or line[j] == "_"):
                        j += 1
                    word = line[i:j]

                    # lihat karakter setelah spasi untuk deteksi pemanggilan fungsi
                    k = j
                    while k < n and line[k] in " \t":
                        k += 1

                    lookup = word.upper() if language == "sql" else word
                    tag = None
                    if lookup in keywords:
                        tag = "keyword"
                    elif lookup in builtins:
                        tag = "builtin"
                    elif language in ("python", "javascript", "typescript", "java", "cpp", "c", "go", "rust") and k < n and line[k] == "(":
                        tag = "function"
                    elif word[:1].isupper():
                        tag = "class"

                    # JSON: string sebelum ':' adalah key
                    if language == "json" and tag is None:
                        m = k
                        while m < n and line[m] in " \t":
                            m += 1
                        if m < n and line[m] == ":":
                            tag = "json_key"

                    # CSS: property sebelum ':', value sesudahnya
                    if language == "css" and tag is None:
                        m = k
                        while m < n and line[m] in " \t":
                            m += 1
                        if m < n and line[m] == ":":
                            tag = "css_prop"

                    if tag:
                        yield lineno, i, j, tag
                    i = j
                    continue

                # --- operator (ditandai halus) ---
                if ch in "=+-*/%<>!&|^~?":
                    j = i
                    while j < n and line[j] in "=+-*/%<>!&|^~?":
                        j += 1
                    yield lineno, i, j, "operator"
                    i = j
                    continue

                i += 1
