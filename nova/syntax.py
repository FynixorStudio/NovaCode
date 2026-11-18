

from __future__ import annotations

from tkinter import Text

from .config import COMMON_WORDS, FONT_MONO, FONT_SIZE, TOKEN_COLORS


TOKEN_TAGS = [
    "keyword", "keyword2", "string", "number", "comment", "function", "class",
    "builtin", "decorator", "operator", "punct", "type", "tag", "attr",
    "css_prop", "css_value", "json_key",
]


def configure_tags(widget: Text) -> None:
    
    for name, color in TOKEN_COLORS.items():
        opts = {"foreground": color}
        if name == "comment":
            opts["font"] = (FONT_MONO, FONT_SIZE, "italic")
        if name in ("search", "search_current"):
            opts = {"background": color, "foreground": "#0d1117"}
        widget.tag_configure(name, **opts)
    
    widget.tag_raise("search_current")
    widget.tag_raise("search")
    try:
        widget.tag_lower("currentline")
    except Exception:
        pass


class SyntaxHighlighter:
    

    def highlight(self, widget: Text, content: str, language: str) -> None:
        for tag in TOKEN_TAGS:
            widget.tag_remove(tag, "1.0", "end")

        langdef = COMMON_WORDS.get(language, COMMON_WORDS["text"])
        for line_no, start, end, tag in self.tokenize(content, language, langdef):
            widget.tag_add(tag, f"{line_no}.{start}", f"{line_no}.{end}")

    
    def tokenize(self, content: str, language: str, langdef: dict):
        
        keywords = set(langdef["keywords"])
        builtins = set(langdef["builtins"])
        line_comment = langdef["line_comment"]
        bc_open, bc_close = langdef["block_comment"]
        strings = langdef["strings"]

        
        active_block_close: str | None = None
        active_triple: str | None = None

        for lineno, line in enumerate(content.split("\n"), start=1):
            i, n = 0, len(line)

            while i < n:
                
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

                
                if line_comment and line.startswith(line_comment, i):
                    yield lineno, i, n, "comment"
                    break

                
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

                
                string_hit = False
                for quote in strings:
                    if not line.startswith(quote, i):
                        continue
                    if len(quote) > 1:  
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

                
                if ch == "@" and i + 1 < n and (line[i + 1].isalpha() or line[i + 1] == "_"):
                    j = i + 1
                    while j < n and (line[j].isalnum() or line[j] in "_."):
                        j += 1
                    yield lineno, i, j, "decorator"
                    i = j
                    continue

                
                if ch.isdigit():
                    j = i
                    while j < n and (line[j].isalnum() or line[j] in "._"):
                        j += 1
                    yield lineno, i, j, "number"
                    i = j
                    continue

                
                if ch.isalpha() or ch == "_":
                    j = i
                    while j < n and (line[j].isalnum() or line[j] == "_"):
                        j += 1
                    word = line[i:j]

                    
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

                    
                    if language == "json" and tag is None:
                        m = k
                        while m < n and line[m] in " \t":
                            m += 1
                        if m < n and line[m] == ":":
                            tag = "json_key"

                    
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

                
                if ch in "=+-*/%<>!&|^~?":
                    j = i
                    while j < n and line[j] in "=+-*/%<>!&|^~?":
                        j += 1
                    yield lineno, i, j, "operator"
                    i = j
                    continue

                i += 1
