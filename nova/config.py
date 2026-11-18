

from __future__ import annotations

import getpass
import os
import sys

APP_NAME = "NovaCode"
APP_VERSION = "1.1.0"
APP_TITLE = f"{APP_NAME} — {APP_VERSION}"


THEMES = {
    "Ember": {            
        "colors": {
            "bg_deep": "#191817", "bg": "#201f1d", "bg_light": "#2a2825",
            "bg_lighter": "#383531", "border": "#33302c",
            "text": "#d4d0c8", "text_bright": "#f0ece4", "muted": "#8c867b",
            "accent": "#e5a24b", "accent_hover": "#efb869", "accent_soft": "#3b2f1d",
            "green": "#9bbf7a", "green_soft": "#232b1d", "yellow": "#dcb65f",
            "red": "#e0695f", "red_soft": "#3d2220", "purple": "#b9a0d6",
            "cyan": "#7dbab2", "orange": "#e08c55", "selection": "#3d3425",
            "current_line": "#222120", "gutter": "#191817",
            "gutter_active": "#d4d0c8", "white": "#1b1916",
        },
        "tokens": {
            "keyword": "#e0845f", "keyword2": "#c4a3d8", "string": "#a7c47f",
            "number": "#e5b567", "comment": "#857f73", "function": "#8fc0d4",
            "class": "#e8c07a", "builtin": "#7dbab2", "decorator": "#c4a3d8",
            "operator": "#c9a27f", "punct": "#a8a398", "type": "#e8c07a",
            "tag": "#e0845f", "attr": "#e5b567", "css_prop": "#8fc0d4",
            "css_value": "#a7c47f", "json_key": "#8fc0d4",
            "search": "#5c4720", "search_current": "#8a6a24",
        },
    },
    "Graphite": {         
        "colors": {
            "bg_deep": "#15171a", "bg": "#1c1e22", "bg_light": "#26292e",
            "bg_lighter": "#343840", "border": "#2c2f35",
            "text": "#c8ccd2", "text_bright": "#eceef2", "muted": "#7f8791",
            "accent": "#e07a5f", "accent_hover": "#ea937b", "accent_soft": "#3b2823",
            "green": "#8ab887", "green_soft": "#1f2a20", "yellow": "#d6b25e",
            "red": "#e0635d", "red_soft": "#3a2123", "purple": "#b6a2d9",
            "cyan": "#78b7c5", "orange": "#e0935a", "selection": "#3a3f4a",
            "current_line": "#1a1c20", "gutter": "#15171a",
            "gutter_active": "#c8ccd2", "white": "#1a1412",
        },
        "tokens": {
            "keyword": "#e07a5f", "keyword2": "#b6a2d9", "string": "#9ec38a",
            "number": "#d9a85e", "comment": "#7b838d", "function": "#8fb9d6",
            "class": "#e3bd7a", "builtin": "#78b7c5", "decorator": "#b6a2d9",
            "operator": "#c9a08c", "punct": "#9aa0a8", "type": "#e3bd7a",
            "tag": "#e07a5f", "attr": "#d9a85e", "css_prop": "#8fb9d6",
            "css_value": "#9ec38a", "json_key": "#8fb9d6",
            "search": "#55402a", "search_current": "#8a6428",
        },
    },
    "Moss": {             
        "colors": {
            "bg_deep": "#151a17", "bg": "#1b221e", "bg_light": "#252e29",
            "bg_lighter": "#323d37", "border": "#2b352f",
            "text": "#cdd3c6", "text_bright": "#eef2e8", "muted": "#838d80",
            "accent": "#b5c96b", "accent_hover": "#c6d884", "accent_soft": "#2f3a1e",
            "green": "#8fcf8b", "green_soft": "#1e2f20", "yellow": "#d9c15f",
            "red": "#df6f68", "red_soft": "#38211f", "purple": "#b8a5d6",
            "cyan": "#7fc0b4", "orange": "#e0975a", "selection": "#34443a",
            "current_line": "#19201c", "gutter": "#151a17",
            "gutter_active": "#cdd3c6", "white": "#161b10",
        },
        "tokens": {
            "keyword": "#d98a5f", "keyword2": "#b8a5d6", "string": "#b5c96b",
            "number": "#e0b563", "comment": "#7a8577", "function": "#86c2d2",
            "class": "#e4c27b", "builtin": "#7fc0b4", "decorator": "#b8a5d6",
            "operator": "#c8a78a", "punct": "#9ea896", "type": "#e4c27b",
            "tag": "#d98a5f", "attr": "#e0b563", "css_prop": "#86c2d2",
            "css_value": "#b5c96b", "json_key": "#86c2d2",
            "search": "#4a4a1e", "search_current": "#7d7424",
        },
    },
    "Paper": {            
        "light": True,
        "colors": {
            "bg_deep": "#fbf9f4", "bg": "#f1eee6", "bg_light": "#e8e4da",
            "bg_lighter": "#d9d4c7", "border": "#dcd7ca",
            "text": "#2b2926", "text_bright": "#14130f", "muted": "#6a655a",
            "accent": "#a8571a", "accent_hover": "#8f4813", "accent_soft": "#f3dfc8",
            "green": "#4f7a2f", "green_soft": "#e3ecd6", "yellow": "#8f6a12",
            "red": "#b8362c", "red_soft": "#f6dcd7", "purple": "#7a5aa6",
            "cyan": "#2e7f86", "orange": "#b8651f", "selection": "#ecd9b8",
            "current_line": "#f5f2ea", "gutter": "#fbf9f4",
            "gutter_active": "#4a463f", "white": "#fffdf8",
        },
        "tokens": {
            "keyword": "#b04a1c", "keyword2": "#7a5aa6", "string": "#4f7a2f",
            "number": "#a0661a", "comment": "#736d62", "function": "#2a6f93",
            "class": "#8f5f0f", "builtin": "#2e7f86", "decorator": "#7a5aa6",
            "operator": "#8a5a3a", "punct": "#4a463f", "type": "#8f5f0f",
            "tag": "#b04a1c", "attr": "#a0661a", "css_prop": "#2a6f93",
            "css_value": "#4f7a2f", "json_key": "#2a6f93",
            "search": "#f0dd9a", "search_current": "#e0b84a",
        },
    },
    "Purple Moon": {      
        "colors": {
            "bg_deep": "#100e1a", "bg": "#171429", "bg_light": "#221d38",
            "bg_lighter": "#302949", "border": "#332c4c",
            "text": "#d8d3e8", "text_bright": "#f4f1ff", "muted": "#9a92b5",
            "accent": "#b79aff", "accent_hover": "#cdb8ff", "accent_soft": "#352a55",
            "green": "#92d3a6", "green_soft": "#1e3328", "yellow": "#e3c784",
            "red": "#e27f9c", "red_soft": "#3d2234", "purple": "#c9a9ff",
            "cyan": "#8fd2dc", "orange": "#dfa17e", "selection": "#3a3159",
            "current_line": "#1f1a33", "gutter": "#100e1a",
            "gutter_active": "#d8d3e8", "white": "#17102a",
        },
        "tokens": {
            "keyword": "#c9a9ff", "keyword2": "#e0a8e6", "string": "#a9d9a6",
            "number": "#e6c98c", "comment": "#847da6", "function": "#8fc8ef",
            "class": "#d7b8ff", "builtin": "#8fd2dc", "decorator": "#e0a8e6",
            "operator": "#c4a4dd", "punct": "#a29abf", "type": "#d7b8ff",
            "tag": "#c9a9ff", "attr": "#e6c98c", "css_prop": "#8fc8ef",
            "css_value": "#a9d9a6", "json_key": "#8fc8ef",
            "search": "#4a3a6e", "search_current": "#7d61b5",
        },
    },
}

DEFAULT_THEME = "Ember"


LEGACY_THEMES = {
    "Midnight": "Graphite", "Aurora": "Ember",
    "Ocean": "Moss", "Nord Light": "Paper", "Ungu Moon": "Purple Moon",
}

CURRENT_THEME = DEFAULT_THEME
COLORS = dict(THEMES[DEFAULT_THEME]["colors"])
TOKEN_COLORS = dict(THEMES[DEFAULT_THEME]["tokens"])


def available_themes() -> list[str]:
    return list(THEMES.keys())


def resolve_theme(name: str | None) -> str:
    
    if name in THEMES:
        return name
    return LEGACY_THEMES.get(name or "", DEFAULT_THEME)


def is_light_theme(name: str | None = None) -> bool:
    return bool(THEMES[resolve_theme(name or CURRENT_THEME)].get("light"))


def apply_theme(name: str) -> str:
    
    global CURRENT_THEME
    name = resolve_theme(name)
    CURRENT_THEME = name
    COLORS.clear()
    COLORS.update(THEMES[name]["colors"])
    TOKEN_COLORS.clear()
    TOKEN_COLORS.update(THEMES[name]["tokens"])
    return name


FONT_UI = "Segoe UI"
FONT_MONO = "Consolas"
FONT_SIZE = 12
FONT_MONO_TUPLE = (FONT_MONO, FONT_SIZE)
FONT_UI_TUPLE = (FONT_UI, 11)


COMMON_WORDS = {
    "python": {
        "keywords": [
            "and", "as", "assert", "async", "await", "break", "class", "continue",
            "def", "del", "elif", "else", "except", "False", "finally", "for",
            "from", "global", "if", "import", "in", "is", "lambda", "None",
            "nonlocal", "not", "or", "pass", "raise", "return", "True", "try",
            "while", "with", "yield", "match", "case",
        ],
        "builtins": [
            "abs", "all", "any", "bool", "bytes", "dict", "dir", "enumerate",
            "filter", "float", "format", "frozenset", "getattr", "hasattr",
            "hash", "help", "int", "isinstance", "issubclass", "iter", "len",
            "list", "map", "max", "min", "next", "object", "open", "ord",
            "pow", "print", "property", "range", "repr", "reversed", "round",
            "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum",
            "super", "tuple", "type", "vars", "zip", "self", "cls",
        ],
        "line_comment": "#",
        "block_comment": ('"""', '"""'),
        "strings": ['"""', "'''", '"', "'"],
    },
    "javascript": {
        "keywords": [
            "async", "await", "break", "case", "catch", "class", "const", "continue",
            "debugger", "default", "delete", "do", "else", "export", "extends",
            "false", "finally", "for", "from", "function", "if", "import", "in",
            "instanceof", "let", "new", "null", "of", "return", "static", "super",
            "switch", "this", "throw", "true", "try", "typeof", "undefined", "var",
            "void", "while", "with", "yield",
        ],
        "builtins": [
            "Array", "Boolean", "console", "Date", "Error", "JSON", "Map", "Math",
            "Number", "Object", "Promise", "RegExp", "Set", "String", "Symbol",
            "document", "window", "require", "module", "exports",
        ],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"', "'", "`"],
    },
    "typescript": {
        "keywords": [
            "abstract", "as", "async", "await", "break", "case", "catch", "class",
            "const", "continue", "declare", "default", "delete", "do", "else",
            "enum", "export", "extends", "false", "finally", "for", "from",
            "function", "if", "implements", "import", "in", "instanceof",
            "interface", "let", "new", "null", "of", "private", "protected",
            "public", "readonly", "return", "static", "super", "switch", "this",
            "throw", "true", "try", "type", "typeof", "undefined", "var", "void",
            "while", "yield",
        ],
        "builtins": [
            "Array", "boolean", "console", "Date", "Error", "JSON", "Map", "Math",
            "number", "Object", "Promise", "Set", "string", "String", "unknown",
            "any", "never", "document", "window",
        ],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"', "'", "`"],
    },
    "java": {
        "keywords": [
            "abstract", "assert", "boolean", "break", "byte", "case", "catch",
            "char", "class", "const", "continue", "default", "do", "double",
            "else", "enum", "extends", "final", "finally", "float", "for", "if",
            "implements", "import", "instanceof", "int", "interface", "long",
            "native", "new", "package", "private", "protected", "public", "return",
            "short", "static", "strictfp", "super", "switch", "synchronized",
            "this", "throw", "throws", "transient", "try", "void", "volatile", "while",
        ],
        "builtins": [
            "System", "String", "Integer", "Double", "Boolean", "Object", "List",
            "Map", "ArrayList", "HashMap", "Exception", "Thread", "Math",
        ],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"', "'"],
    },
    "cpp": {
        "keywords": [
            "auto", "break", "case", "catch", "char", "class", "const", "continue",
            "default", "delete", "do", "double", "else", "enum", "explicit",
            "export", "extern", "false", "float", "for", "friend", "goto", "if",
            "inline", "int", "long", "mutable", "namespace", "new", "nullptr",
            "operator", "private", "protected", "public", "register", "return",
            "short", "signed", "sizeof", "static", "struct", "switch", "template",
            "this", "throw", "true", "try", "typedef", "typename", "union",
            "unsigned", "using", "virtual", "void", "volatile", "while",
        ],
        "builtins": [
            "cout", "cin", "cerr", "endl", "std", "string", "vector", "map",
            "size_t", "printf", "malloc", "free",
        ],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"', "'"],
    },
    "c": {
        "keywords": [
            "auto", "break", "case", "char", "const", "continue", "default", "do",
            "double", "else", "enum", "extern", "float", "for", "goto", "if",
            "inline", "int", "long", "register", "restrict", "return", "short",
            "signed", "sizeof", "static", "struct", "switch", "typedef", "union",
            "unsigned", "void", "volatile", "while",
        ],
        "builtins": ["printf", "scanf", "malloc", "calloc", "free", "strlen", "size_t"],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"', "'"],
    },
    "go": {
        "keywords": [
            "break", "case", "chan", "const", "continue", "default", "defer", "else",
            "fallthrough", "for", "func", "go", "goto", "if", "import", "interface",
            "map", "package", "range", "return", "select", "struct", "switch",
            "type", "var",
        ],
        "builtins": ["append", "cap", "close", "copy", "delete", "len", "make", "new", "panic", "print", "println", "recover"],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"', "`"],
    },
    "rust": {
        "keywords": [
            "as", "async", "await", "break", "const", "continue", "crate", "dyn",
            "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in",
            "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
            "self", "Self", "static", "struct", "super", "trait", "true", "type",
            "unsafe", "use", "where", "while",
        ],
        "builtins": ["println", "format", "Vec", "String", "Option", "Result", "Some", "None", "Ok", "Err"],
        "line_comment": "//",
        "block_comment": ("/*", "*/"),
        "strings": ['"'],
    },
    "html": {
        "keywords": [], "builtins": [],
        "line_comment": "", "block_comment": ("<!--", "-->"), "strings": ['"', "'"],
    },
    "css": {
        "keywords": [], "builtins": [],
        "line_comment": "", "block_comment": ("/*", "*/"), "strings": ['"', "'"],
    },
    "json": {
        "keywords": ["true", "false", "null"], "builtins": [],
        "line_comment": "", "block_comment": ("", ""), "strings": ['"'],
    },
    "sql": {
        "keywords": [
            "SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE", "SET",
            "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "JOIN", "LEFT", "RIGHT",
            "INNER", "OUTER", "ON", "GROUP", "BY", "ORDER", "HAVING", "LIMIT",
            "AS", "AND", "OR", "NOT", "NULL", "IS", "IN", "LIKE", "DISTINCT",
        ],
        "builtins": ["COUNT", "SUM", "AVG", "MIN", "MAX", "NOW"],
        "line_comment": "--", "block_comment": ("/*", "*/"), "strings": ["'", '"'],
    },
    "bash": {
        "keywords": ["if", "then", "else", "elif", "fi", "for", "in", "do", "done", "while", "function", "case", "esac", "echo", "export", "source", "return"],
        "builtins": ["cd", "ls", "pwd", "grep", "awk", "sed", "cat", "mkdir", "rm", "cp", "mv"],
        "line_comment": "#", "block_comment": ("", ""), "strings": ['"', "'"],
    },
    "markdown": {
        "keywords": [], "builtins": [],
        "line_comment": "", "block_comment": ("", ""), "strings": [],
    },
    "text": {
        "keywords": [], "builtins": [],
        "line_comment": "", "block_comment": ("", ""), "strings": [],
    },
}

LANGUAGE_ALIASES = {
    "py": "python", "pyw": "python",
    "js": "javascript", "jsx": "javascript", "mjs": "javascript", "cjs": "javascript",
    "ts": "typescript", "tsx": "typescript",
    "java": "java",
    "cpp": "cpp", "cc": "cpp", "cxx": "cpp", "hpp": "cpp", "hxx": "cpp", "h": "cpp",
    "c": "c",
    "go": "go",
    "rs": "rust",
    "html": "html", "htm": "html", "xml": "html", "svg": "html", "vue": "html",
    "css": "css", "scss": "css", "less": "css",
    "json": "json", "jsonc": "json",
    "sql": "sql",
    "sh": "bash", "bat": "bash", "cmd": "bash", "ps1": "bash",
    "md": "markdown", "markdown": "markdown",
    "txt": "text",
}

LANGUAGE_LABELS = {
    "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
    "java": "Java", "cpp": "C++", "c": "C", "go": "Go", "rust": "Rust",
    "html": "HTML", "css": "CSS", "json": "JSON", "sql": "SQL",
    "bash": "Shell", "markdown": "Markdown", "text": "Plain Text",
}


def language_for(path: str | None) -> str:
    
    if not path:
        return "python"
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    return LANGUAGE_ALIASES.get(ext, "text")


def language_label(lang: str) -> str:
    return LANGUAGE_LABELS.get(lang, lang.capitalize())


def app_dir() -> str:
    
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def user_name() -> str:
    
    try:
        name = getpass.getuser().strip()
        if name:
            return name
    except Exception:
        pass
    return os.path.basename(os.path.expanduser("~")) or "User"


def settings_path() -> str:
    
    appdata = os.environ.get("APPDATA")
    if appdata:
        folder = os.path.join(appdata, user_name(), APP_NAME)
        try:
            os.makedirs(folder, exist_ok=True)
            return os.path.join(folder, "novacode_settings.json")
        except OSError:
            pass
    return os.path.join(app_dir(), "novacode_settings.json")


def asset_path(*parts: str) -> str:
    
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", *parts)
