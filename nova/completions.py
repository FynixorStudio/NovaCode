"""Mesin autocomplete per bahasa untuk NovaCode.

Kamus kata kunci, builtin, metode, dan snippet dikelompokkan per bahasa.
Popup menyaring daftar mengikuti prefix yang diketik (f -> semua yang diawali f,
fal -> lebih sedikit, False -> almost exact) dan menampilkan keterangan singkat
untuk item yang dipilih. Tidak bergantung pada paket eksternal.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import COMMON_WORDS, language_label

# kind -> label pendek yang ditampilkan di bawah popup
KIND_LABEL = {
    "keyword": "kata kunci",
    "builtin": "bawaan",
    "function": "fungsi",
    "method": "metode",
    "type": "tipe",
    "constant": "konstanta",
    "module": "modul",
    "tag": "tag",
    "attr": "atribut",
    "property": "properti",
    "value": "nilai",
    "command": "perintah",
    "key": "kunci",
    "snippet": "snippet",
    "word": "kata di dokumen",
}

# Urutan prioritas saat hasil difilter (lebih kecil = lebih atas).
_KIND_RANK = {
    "snippet": 0, "keyword": 1, "builtin": 2, "function": 3, "method": 4,
    "type": 5, "constant": 6, "module": 7, "tag": 8, "attr": 9,
    "property": 10, "value": 11, "command": 12, "key": 13, "word": 14,
}


@dataclass(frozen=True)
class Item:
    word: str
    kind: str = "keyword"
    detail: str = ""
    insert: str | None = None       # teks final; {cursor} = posisi kursor


def _words(words: str, kind: str, detail: str = "") -> list[Item]:
    return [Item(w, kind, detail or KIND_LABEL.get(kind, kind)) for w in words.split()]


def _snip(word: str, insert: str, detail: str) -> Item:
    return Item(word, "snippet", detail, insert)


# ---------------------------------------------------------------------------
# Tambahan per bahasa. Keyword/builtin dasar tetap diambil dari config.py.
# ---------------------------------------------------------------------------
EXTRA: dict[str, list[Item]] = {
    "python": [
        *_words("""append extend insert pop remove clear index count sort reverse copy
            get keys values items update setdefault fromkeys
            strip lstrip rstrip split rsplit splitlines join replace find rfind
            startswith endswith lower upper title capitalize casefold swapcase
            format encode decode zfill ljust rjust center isdigit isalpha isspace
            isnumeric isidentifier partition rpartition translate""", "method", "metode Python"),
        *_words("""os sys json re math random datetime time pathlib collections itertools
            functools typing subprocess threading asyncio urllib csv sqlite3 logging
            argparse unittest statistics hashlib base64 shutil tempfile socket queue""", "module", "modul standar"),
        *_words("""staticmethod classmethod property abstractmethod cache
            dataclass NamedTuple""", "builtin", "dekorator / helper"),
        Item("__init__", "method", "konstruktor kelas"),
        Item("__name__", "constant", "nama modul"),
        Item("__main__", "constant", "modul saat dijalankan langsung"),
        Item("__file__", "constant", "path file modul"),
        _snip("def", "def {cursor}(args):\n    pass", "fungsi baru"),
        _snip("class", "class {cursor}:\n    def __init__(self):\n        pass", "kelas baru"),
        _snip("for", "for {cursor} in iterable:\n    pass", "perulangan for"),
        _snip("ifmain", 'if __name__ == "__main__":\n    {cursor}', "entry point script"),
        _snip("try", "try:\n    {cursor}\nexcept Exception as e:\n    pass", "try / except"),
        _snip("with", "with open({cursor}) as f:\n    pass", "context manager"),
        _snip("fstr", 'f"{cursor}"', "f-string"),
    ],
    "javascript": [
        *_words("""push pop shift unshift map filter reduce forEach find findIndex some
            every includes indexOf slice splice sort reverse join concat flat fill
            split trim trimStart trimEnd replace replaceAll match matchAll search
            charAt charCodeAt substring substr startsWith endsWith padStart padEnd
            toUpperCase toLowerCase toString toFixed add has delete clear entries
            keys values then catch finally bind call apply""", "method", "metode JavaScript"),
        *_words("""setTimeout setInterval clearTimeout clearInterval requestAnimationFrame
            fetch alert confirm prompt parseInt parseFloat isNaN encodeURIComponent
            decodeURIComponent""", "function", "fungsi global"),
        *_words("""document window console localStorage sessionStorage location history
            navigator screen Promise JSON Math Date RegExp Error Map Set WeakMap
            ArrayBuffer Uint8Array module exports require process""", "builtin", "objek bawaan"),
        _snip("function", "function {cursor}(args) {\n    \n}", "deklarasi fungsi"),
        _snip("arrow", "const {cursor} = (args) => {\n    \n}", "arrow function"),
        _snip("const", "const {cursor} = value;", "konstanta"),
        _snip("for", "for (let {cursor} = 0; i < length; i++) {\n    \n}", "perulangan for"),
        _snip("try", "try {\n    {cursor}\n} catch (e) {\n    console.error(e);\n}", "try / catch"),
    ],
    "typescript": [
        *_words("""string number boolean any unknown never void object symbol bigint
            interface type enum namespace readonly optional""", "type", "tipe TypeScript"),
        *_words("""push pop map filter reduce forEach find some every includes slice
            split trim replace startsWith endsWith then catch""", "method", "metode TypeScript"),
        *_words("""console document window Promise JSON Math Date Map Set Record Partial
            Pick Omit ReturnType Awaited""", "builtin", "bawaan TypeScript"),
        _snip("interface", "interface {cursor} {\n    \n}", "deklarasi interface"),
        _snip("type", "type {cursor} = string;", "type alias"),
        _snip("arrow", "const {cursor} = (args: type): void => {\n    \n}", "arrow function"),
    ],
    "java": [
        *_words("""length equals hashCode toString compareTo compareToIgnoreCase
            toUpperCase toLowerCase substring split trim strip replace contains
            startsWith endsWith charAt indexOf isEmpty size add remove get put
            containsKey containsValue keySet values stream forEach collect sorted
            filter map count""", "method", "metode Java"),
        *_words("""String StringBuilder StringBuffer Integer Long Double Float Boolean
            Character Object ArrayList LinkedList HashMap HashSet TreeMap Optional
            Stream Collectors Arrays Collections Objects Scanner Random
            RuntimeException Exception IOException Thread Math System""", "type", "kelas Java"),
        _snip("main", "public static void main(String[] args) {\n    {cursor}\n}", "method main"),
        _snip("class", "public class {cursor} {\n    \n}", "kelas baru"),
        _snip("for", "for (int {cursor} = 0; i < length; i++) {\n    \n}", "perulangan for"),
        _snip("try", "try {\n    {cursor}\n} catch (Exception e) {\n    e.printStackTrace();\n}", "try / catch"),
    ],
    "cpp": [
        *_words("""size length empty clear at front back begin end rbegin rend insert
            erase find count push_back pop_back emplace_back reserve resize assign
            compare substr c_str data getline""", "method", "metode STL"),
        *_words("""vector string map unordered_map set unordered_set pair tuple list deque
            queue stack unique_ptr shared_ptr weak_ptr make_unique make_shared
            cout cin cerr endl printf scanf malloc calloc realloc free memcpy
            memset strlen strcpy sizeof nullptr""", "builtin", "bawaan C++"),
        Item("std", "module", "namespace standar"),
        _snip("for", "for (int {cursor} = 0; i < n; i++) {\n    \n}", "perulangan for"),
        _snip("class", "class {cursor} {\npublic:\n    \n};", "kelas baru"),
        _snip("main", "int main() {\n    {cursor}\n    return 0;\n}", "fungsi main"),
    ],
    "c": [
        *_words("""printf scanf sprintf snprintf fprintf fscanf fopen fclose fread fwrite
            malloc calloc realloc free memset memcpy memmove memcmp strlen strcpy
            strncpy strcmp strcat strchr strstr qsort abs pow sqrt floor ceil""", "function", "fungsi pustaka C"),
        *_words("""size_t ssize_t int8_t uint8_t int32_t uint32_t int64_t uint64_t
            NULL EOF stdin stdout stderr""", "constant", "konstanta / tipe C"),
        *_words("FILE struct enum union typedef extern static const volatile register", "keyword", "kata kunci C"),
        _snip("main", "int main(void) {\n    {cursor}\n    return 0;\n}", "fungsi main"),
        _snip("for", "for (int {cursor} = 0; i < n; i++) {\n    \n}", "perulangan for"),
    ],
    "go": [
        *_words("""fmt strings strconv time context errors sync bytes math os io bufio
            net/http encoding/json database/sql log regexp sort unicode""", "module", "paket Go"),
        *_words("""append len cap make new delete copy close panic recover print println
            Errorf Printf Println Sprintf Sscan Marshal Unmarshal Now Sleep""", "function", "fungsi Go"),
        _snip("func", "func {cursor}() {\n    \n}", "deklarasi fungsi"),
        _snip("for", "for {cursor} := 0; {cursor} < n; {cursor}++ {\n    \n}", "perulangan for"),
        _snip("iferr", 'if err != nil {\n    return {cursor}\n}', "penanganan error"),
        _snip("struct", "type {cursor} struct {\n    \n}", "deklarasi struct"),
    ],
    "rust": [
        *_words("""push pop insert remove len is_empty iter into_iter map filter fold
            find any all collect unwrap expect unwrap_or ok err clone to_string
            parse as_str contains starts_with ends_with sort dedup chunk""", "method", "metode Rust"),
        *_words("""println print format vec Some None Ok Err String Vec HashMap HashSet
            Option Result Box Rc Arc Cell RefCell""", "builtin", "bawaan Rust"),
        _snip("fn", "fn {cursor}() {\n    \n}", "deklarasi fungsi"),
        _snip("struct", "struct {cursor} {\n    \n}", "deklarasi struct"),
        _snip("impl", "impl {cursor} {\n    \n}", "implementasi"),
        _snip("for", "for {cursor} in iter {\n    \n}", "perulangan for"),
    ],
    "html": [
        *_words("""html head body title meta link style script noscript
            div span section article aside header footer nav main
            h1 h2 h3 h4 h5 h6 p br hr strong em b i u small mark
            a img figure figcaption ul ol li dl dt dd
            table thead tbody tfoot tr th td caption colgroup
            form input textarea select option optgroup button label fieldset legend
            iframe video audio source track canvas svg picture
            template details summary dialog progress meter time code pre kbd""", "tag", "tag HTML"),
        *_words("""class id style title lang dir role aria-label aria-hidden
            href src srcset alt width height type name value placeholder required
            disabled readonly checked selected multiple action method target rel
            download colspan rowspan for autocomplete maxlength min max step
            accept pattern novalidate""", "attr", "atribut HTML"),
        _snip("html5", "<!DOCTYPE html>\n<html lang=\"id\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>{cursor}</title>\n</head>\n<body>\n    \n</body>\n</html>", "kerangka HTML5"),
        _snip("div", "<div>{cursor}</div>", "elemen div"),
        _snip("a", '<a href="{cursor}">link</a>', "tautan"),
        _snip("img", '<img src="{cursor}" alt="">', "gambar"),
        _snip("ul", "<ul>\n    <li>{cursor}</li>\n</ul>", "daftar"),
        _snip("form", '<form action="{cursor}" method="post">\n    \n</form>', "formulir"),
    ],
    "css": [
        *_words("""color background background-color background-image background-size
            background-position border border-width border-style border-color
            border-radius border-collapse margin margin-top margin-right margin-bottom
            margin-left padding padding-top padding-right padding-bottom padding-left
            width height min-width max-width min-height max-height box-sizing
            display flex flex-direction flex-wrap flex-grow flex-shrink align-items
            align-content justify-content order gap row-gap column-gap
            grid grid-template-columns grid-template-rows grid-gap place-items
            position top right bottom left z-index float clear overflow overflow-x
            overflow-y visibility opacity transform translate rotate scale
            transition animation box-shadow text-shadow filter backdrop-filter
            font font-family font-size font-weight font-style line-height
            letter-spacing word-spacing text-align text-decoration text-transform
            text-overflow white-space vertical-align cursor pointer-events
            list-style outline resize object-fit aspect-ratio content""", "property", "properti CSS"),
        *_words("""flex grid block inline inline-block inline-flex none hidden visible
            absolute relative fixed sticky static center left right top bottom
            space-between space-around space-evenly stretch wrap nowrap column row
            solid dashed dotted double transparent auto cover contain repeat
            bold normal italic underline uppercase lowercase capitalize
            ease ease-in ease-out linear infinite alternate""", "value", "nilai CSS"),
        *_words("@media @keyframes @import @font-face @supports @variables", "keyword", "at-rule CSS"),
        _snip("flex", "display: flex;\nalign-items: center;\njustify-content: center;", "flex center"),
        _snip("media", "@media (max-width: {cursor}px) {\n    \n}", "media query"),
        _snip("keyframes", "@keyframes {cursor} {\n    from { opacity: 0; }\n    to { opacity: 1; }\n}", "animasi CSS"),
    ],
    "json": [
        *_words("""id name value type data items list array object status message result
            error success config settings version enabled disabled active user users
            title description url link image created_at updated_at""", "key", "kunci JSON umum"),
        *_words("true false null", "constant", "nilai JSON"),
        _snip("obj", '{\n    "{cursor}": "value"\n}', "objek JSON"),
        _snip("arr", '[\n    {cursor}\n]', "array JSON"),
    ],
    "sql": [
        *_words("""JOIN INNER LEFT RIGHT FULL CROSS OUTER NATURAL ON USING AS
            GROUP BY ORDER HAVING LIMIT OFFSET FETCH UNION UNION ALL INTERSECT
            EXCEPT DISTINCT TOP EXISTS CASE WHEN THEN ELSE END ASC DESC""", "keyword", "klausa SQL"),
        *_words("""COUNT SUM AVG MIN MAX ROUND ABS CEIL FLOOR LENGTH UPPER LOWER
            SUBSTRING CONCAT COALESCE CAST CONVERT NOW CURRENT_DATE DATE_TRUNC
            EXTRACT GROUP_CONCAT STRING_AGG ROW_NUMBER RANK DENSE_RANK""", "function", "fungsi SQL"),
        *_words("INTEGER VARCHAR CHAR TEXT BOOLEAN DATE TIMESTAMP DECIMAL NUMERIC REAL", "type", "tipe SQL"),
        _snip("select", "SELECT {cursor}\nFROM table_name\nWHERE 1 = 1;", "query SELECT"),
        _snip("insert", "INSERT INTO table_name (column1, column2)\nVALUES ({cursor});", "query INSERT"),
        _snip("create", "CREATE TABLE {cursor} (\n    id INTEGER PRIMARY KEY,\n    name TEXT\n);", "buat tabel"),
    ],
    "bash": [
        *_words("""echo printf cd pwd ls la ll find mkdir touch rm rmdir cp mv ln cat
            head tail less more grep egrep sed awk cut sort uniq wc tr xargs tee
            chmod chown chgrp ps kill pkill sleep date cal whoami uname df du
            curl wget ping ssh scp tar zip unzip git python python3 pip node npm
            source export unset set read test true false exit""", "command", "perintah shell"),
        _snip("if", 'if [ "{cursor}" ]; then\n    \nfi', "kondisi if"),
        _snip("for", "for {cursor} in *; do\n    \ndone", "perulangan for"),
        _snip("fn", "{cursor}() {\n    \n}", "fungsi shell"),
    ],
    "markdown": [
        _snip("h1", "# {cursor}", "judul utama"),
        _snip("h2", "## {cursor}", "judul bagian"),
        _snip("h3", "### {cursor}", "judul sub-bagian"),
        _snip("bold", "**{cursor}**", "teks tebal"),
        _snip("italic", "*{cursor}*", "teks miring"),
        _snip("code", "`{cursor}`", "kode inline"),
        _snip("block", "```{cursor}\n\n```", "blok kode"),
        _snip("link", "[{cursor}](url)", "tautan"),
        _snip("image", "![alt]({cursor})", "gambar"),
        _snip("quote", "> {cursor}", "kutipan"),
        _snip("list", "- {cursor}", "daftar"),
        _snip("table", "| {cursor} | Kolom |\n|---|---|\n| Isi | Isi |", "tabel"),
        _snip("hr", "---", "garis horizontal"),
    ],
}


# ---------------------------------------------------------------------------
_cache: dict[str, list[Item]] = {}


def items_for(language: str) -> list[Item]:
    """Semua item yang tersedia untuk suatu bahasa (di-cache per bahasa)."""
    lang = language if language in COMMON_WORDS else "text"
    if lang in _cache:
        return _cache[lang]

    merged: dict[str, Item] = {}
    langdef = COMMON_WORDS[lang]
    label = language_label(lang)
    for word in langdef["keywords"]:
        merged[word.lower()] = Item(word, "keyword", label)
    for word in langdef["builtins"]:
        merged[word.lower()] = Item(word, "builtin", f"bawaan {label}")
    for item in EXTRA.get(lang, ()):
        merged[item.word.lower()] = item

    items = sorted(merged.values(), key=lambda it: (it.word.lower(), it.word))
    _cache[lang] = items
    return items


def get_completions(language: str, prefix: str = "", document_words=(),
                    limit: int = 14) -> list[Item]:
    """Saring item berdasarkan prefix; hasil paling relevan di depan."""
    pool = list(items_for(language))
    seen = {it.word.lower() for it in pool}
    for word in document_words:
        key = word.lower()
        if key not in seen:
            seen.add(key)
            pool.append(Item(word, "word", "kata di dokumen ini"))

    needle = prefix.lower()
    if needle:
        pool = [it for it in pool if it.word.lower().startswith(needle)]

    pool.sort(key=lambda it: (
        0 if it.word == prefix else 1,
        0 if it.word.lower() == prefix.lower() else 1,
        _KIND_RANK.get(it.kind, 99),
        len(it.word),
        it.word.lower(),
    ))
    return pool[:limit]


def describe(item: Item, language: str) -> str:
    """Teks bantuan singkat yang tampil di bawah popup."""
    label = KIND_LABEL.get(item.kind, item.kind)
    detail = item.detail or label
    if item.kind == "word":
        return f"{label} · {item.word}"
    if item.kind == "snippet":
        first = (item.insert or "").splitlines()[0].replace("{cursor}", "")
        return f"snippet · {first[:70]}"
    return f"{label} · {detail}"
