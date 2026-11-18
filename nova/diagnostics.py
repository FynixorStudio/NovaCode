

from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    file: str
    line: int
    message: str
    hint: str
    severity: str = "ERROR"


HINT_RULES = [
    (r"ModuleNotFoundError: No module named ['\"]([^'\"]+)['\"]",
     lambda m: f"Pasang modul: pip install {m.group(1)}"),
    (r"ImportError: (.*)",
     lambda m: "Periksa nama modul, typo, atau pastikan package sudah ter-install."),
    (r"SyntaxError: (.*)",
     lambda m: "Periksa titik dua, kurung, dan tanda kutip di baris ini."),
    (r"IndentationError: (.*)",
     lambda m: "Samakan indentasi (1 level = 4 spasi; jangan campur tab & spasi)."),
    (r"TabError: (.*)",
     lambda m: "Ganti semua tab dengan 4 spasi agar konsisten."),
    (r"FileNotFoundError: \[Errno 2\].*?['\"]([^'\"]+)['\"]",
     lambda m: f"Pastikan file ada: {m.group(1)}"),
    (r"FileNotFoundError: (.*)",
     lambda m: "Periksa path file (huruf besar/kecil dan nama folder)."),
    (r"PermissionError: (.*)",
     lambda m: "Ubah izin file/folder atau jalankan sebagai Administrator."),
    (r"NameError: name ['\"]([^'\"]+)['\"]",
     lambda m: f"Definisikan '{m.group(1)}' dulu atau perbaiki ejaannya."),
    (r"TypeError: (.*)",
     lambda m: "Cek tipe dan urutan argumen yang dikirim ke fungsi."),
    (r"AttributeError: (.*)",
     lambda m: "Objek tidak punya atribut/method itu; cek tipe objeknya."),
    (r"ZeroDivisionError: (.*)",
     lambda m: "Pastikan pembagi tidak nol (tambahkan pengecekan if)."),
    (r"KeyError: ['\"]([^'\"]+)['\"]",
     lambda m: f"Tambahkan kunci '{m.group(1)}' atau pakai dict.get(...)."),
    (r"IndexError: (.*)",
     lambda m: "Indeks di luar jangkauan; cek panjang list sebelum mengakses."),
    (r"ValueError: (.*)",
     lambda m: "Nilai tidak valid untuk tipe itu; cek konversi/format input."),
    (r"AssertionError:? ?(.*)",
     lambda m: "Periksa kondisi yang di-assert; bandingkan nilai aktual vs harapan."),
    (r"ConnectionError: (.*)",
     lambda m: "Periksa koneksi jaringan, URL, dan firewall."),
    (r"RecursionError: (.*)",
     lambda m: "Tambahkan kondisi berhenti pada rekursi atau ubah menjadi perulangan."),
    (r"Unicode(?:Decode|Encode)Error: (.*)",
     lambda m: "Gunakan encoding yang sesuai, mis. open(path, encoding='utf-8')."),
    (r"MemoryError",
     lambda m: "Data terlalu besar; proses per bagian atau kosongkan variabel yang tidak dipakai."),
    (r"FileExistsError: (.*)",
     lambda m: "File/folder sudah ada; gunakan nama lain atau mode overwrite."),
    (r"OSError: (.*)",
     lambda m: "Periksa path, izin akses, dan apakah file sedang dipakai program lain."),
    (r"KeyboardInterrupt",
     lambda m: "Proses dihentikan pengguna. Jalankan ulang jika memang perlu."),
    (r"ReferenceError: (.*)",
     lambda m: "Deklarasikan variabel/fungsi tersebut dulu sebelum dipakai."),
    (r"RangeError: (.*)",
     lambda m: "Nilai/ukuran di luar batas; periksa angka dan panjang array."),
    (r"(?i)expected ['\"]?(.+?)['\"]? before",
     lambda m: "Tambahkan token yang diminta pada baris ini; cek kurung, titik koma, atau kutip."),
    (r"(?i)undefined reference to [`']([^`']+)",
     lambda m: f"Fungsi/simbol '{m.group(1)}' tidak ditemukan saat linking; pastikan implementasi/library tersedia."),
    (r"(?i)was not declared in this scope",
     lambda m: "Deklarasikan variabel/fungsi sebelum dipakai, atau periksa include/import."),
    (r"(?i)no such file or directory",
     lambda m: "Periksa nama dan path file; pastikan huruf besar/kecil sesuai."),
    (r"(?i)unused (?:variable|parameter|import)",
     lambda m: "Hapus yang tidak dipakai atau beri awalan _ agar tidak diperingatkan."),
    (r"(?i)package .* does not exist",
     lambda m: "Periksa nama package/import, lalu jalankan go mod tidy."),
    (r"error\[E\d+\]:\s*(.*)",
     lambda m: "Error kompiler Rust: periksa tipe/definisi pada baris yang ditandai."),
    (r"(?i)error\s+CS\d+:\s*(.*)",
     lambda m: "Error kompiler C#: periksa baris ini dan tipe/identifier yang dipakai."),
    (r"(?i)TS\d+:\s*(.*)",
     lambda m: "Error TypeScript: cocokkan tipe/definisi pada baris ini."),
    (r"(?i)npm ERR!\s*(.*)",
     lambda m: "Periksa dependensi/package.json lalu jalankan npm install ulang."),
    (r"(?i)MODULE_NOT_FOUND.*?['\"]([^'\"]+)['\"]",
     lambda m: f"Modul '{m.group(1)}' belum terpasang: npm install {m.group(1)}"),
]

_GENERIC_HINT = (
    "Baca pesan error di bawah, periksa baris yang ditandai, lalu perbaiki "
    "sesuai petunjuk (syntax, tipe, atau nilai)."
)


_TRACEBACK_LOC = re.compile(
    r'File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+([^\n]+))?', re.IGNORECASE)

_INLINE_LOC = re.compile(
    r'(?P<file>[A-Za-z]:[\\/][^\s:()]+|[^\s:()]+\.[A-Za-z0-9_]+|'
    r'\.?[\\/]?[^\s:()]+):(?P<line>\d+)(?::\d+)?:\s*'
    r'(?P<sev>error|warning|fatal error|note):\s*(?P<msg>.+)', re.IGNORECASE)

_ARROW_LOC = re.compile(r'-->\s*([^\s:]+):(\d+)(?::\d+)?')

_STACK_LOC = re.compile(r'\(?([^\s()]+\.(?:js|jsx|ts|tsx|mjs|cjs)):(\d+):(\d+)\)?')


def _hint_for(message: str) -> str:
    for pattern, build in HINT_RULES:
        m = re.search(pattern, message, re.IGNORECASE)
        if m:
            try:
                return build(m)
            except Exception:
                return _GENERIC_HINT
    return _GENERIC_HINT


def _absolutize(path: str, fallback_dir: str | None) -> str:
    path = path.strip().strip('"')
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    if fallback_dir:
        return os.path.normpath(os.path.join(fallback_dir, path))
    return path


def analyze_output(output: str, current_file: str | None = None,
                   cwd: str | None = None) -> list[Diagnostic]:
    
    if not output or not output.strip():
        if current_file:
            return [Diagnostic(current_file, 1, "Perintah gagal tanpa keluaran.",
                               "Lihat detail lengkap di tab Terminal.")]
        return []
    fallback_dir = cwd or (os.path.dirname(current_file) if current_file else None)
    result: list[Diagnostic] = []
    seen: set[tuple[str, int, str]] = set()

    def add(file: str, line: int, message: str, hint: str | None = None,
            severity: str = "ERROR"):
        file = _absolutize(file, fallback_dir) if file else (current_file or "")
        line = max(1, int(line or 1))
        message = (message or "Perintah gagal.").strip()[:160]
        key = (file.lower(), line, message.lower())
        if key in seen:
            return
        seen.add(key)
        result.append(Diagnostic(file, line, message, hint or _hint_for(message), severity))

    
    inline_spans: list[tuple[int, int]] = []
    for m in _INLINE_LOC.finditer(output):
        sev = m.group("sev").lower()
        if "note" in sev:
            continue
        inline_spans.append(m.span())
        msg = m.group("msg").strip()
        add(m.group("file"), int(m.group("line")), msg,
            severity="WARN" if "warning" in sev else "ERROR")

    
    locations = [
        (m.start(), m.group(1), int(m.group(2)))
        for m in _TRACEBACK_LOC.finditer(output)
    ]
    locations += [
        (m.start(), m.group(1), int(m.group(2)))
        for m in _ARROW_LOC.finditer(output)
    ]
    locations += [
        (m.start(), m.group(1), int(m.group(2)))
        for m in _STACK_LOC.finditer(output)
    ]
    locations.sort(key=lambda x: x[0])
    
    locations = [
        loc for loc in locations
        if not any(a <= loc[0] < b for a, b in inline_spans)
    ]

    messages: list[tuple[int, str]] = []
    message_lines: set[int] = set()

    def add_message(pos: int, text: str):
        text = (text or "").strip()[:160]
        if not text:
            return
        line_no = output.count("\n", 0, pos)
        if line_no in message_lines:
            return
        if any(a <= pos < b for a, b in inline_spans):
            return
        message_lines.add(line_no)
        messages.append((pos, text))

    for pattern, _build in HINT_RULES:
        for m in re.finditer(pattern, output, re.IGNORECASE):
            add_message(m.start(), m.group(0))
    
    for m in re.finditer(r"(?im)^.*\b(?:error|failed|exception)\b.*$", output):
        text = m.group(0).strip()
        if not text or text.lower().startswith(("file ", "at ")):
            continue
        if re.search(r"(?i)\b\d+\s+(?:errors?|warnings?)\s+generated\b", text):
            continue
        add_message(m.start(), text)
    messages.sort(key=lambda x: x[0])

    if not messages:
        if not result:
            
            
            last = next((ln.strip() for ln in reversed(output.splitlines())
                         if ln.strip()), "")
            add(current_file or "", 1, last or "Perintah gagal.",
                "Lihat detail lengkap di tab Terminal.")
        return result

    for pos, message in messages:
        
        
        preceding = [loc for loc in locations if loc[0] <= pos]
        chosen = preceding or locations or [(pos, current_file or "", 1)]
        for _p, file, line in chosen:
            add(file, line, message)

    if not result:
        add(current_file or "", 1, messages[-1][1])
    return result
