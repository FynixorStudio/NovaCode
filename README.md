<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/mark_light.png">
  <source media="(prefers-color-scheme: light)" srcset="assets/mark_dark.png">
  <img src="assets/logo.png" alt="NovaCode" width="96">
</picture>

<h1 align="center">NovaCode</h1>

<p align="center">
  <b>Editor kode ringan, cepat, dan kaya fitur untuk Windows.</b><br>
  <sub>Python · CustomTkinter · PyInstaller · satu file <code>.exe</code></sub>
</p>

<p align="center">
  <img src="assets/logo_horizontal.png" alt="NovaCode wordmark" width="440">
</p>

<p align="center">
  <a href="https://img.shields.io/badge/status-ACTIVE-22c55e?style=for-the-badge"><img src="https://img.shields.io/badge/status-ACTIVE-22c55e?style=for-the-badge" alt="status"></a>
  <a href="#quickstart"><img src="https://img.shields.io/badge/Windows-10%20%7C%2011-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows"></a>
  <a href="#quickstart"><img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="#struktur"><img src="https://img.shields.io/badge/GUI-CustomTkinter-2F81F7?style=for-the-badge" alt="CustomTkinter"></a>
  <a href="#tema"><img src="https://img.shields.io/badge/Themes-5-8B5CF6?style=for-the-badge" alt="5 tema"></a>
  <a href="#ai"><img src="https://img.shields.io/badge/AI-10%20providers-111827?style=for-the-badge&logo=openai&logoColor=white" alt="10 provider AI"></a>
  <a href="#build"><img src="https://img.shields.io/badge/Build-PyInstaller-9FE6E0?style=for-the-badge" alt="PyInstaller"></a>
  <a href="#panduan"><img src="https://img.shields.io/badge/Docs-Bahasa%20Indonesia-EA580C?style=for-the-badge" alt="Dokumentasi Indonesia"></a>
</p>

<p align="center">
  <a href="#quickstart">🚀 Quickstart</a> ·
  <a href="#fitur">✨ Fitur</a> ·
  <a href="#tema">🎨 Tema</a> ·
  <a href="#ai">🤖 AI</a> ·
  <a href="#shortcut">⌨️ Shortcut</a> ·
  <a href="#struktur">🗂️ Struktur</a> ·
  <a href="#build">📦 Build</a> ·
  <a href="#troubleshoot">🛠️ Bantuan</a>
</p>

</div>

---

<a id="quickstart"></a>

## 🚀 Quickstart

> [!TIP]
> **Paling cepat:** cari ikon **NovaCode** di Desktop, klik **sekali**, langsung jalan.

| Langkah | Aksi | Visual |
|:---:|---|---|
| 1 | Ekstrak / salin folder `NovaCode` | 📁 |
| 2 | Klik dua kali `run.bat` (auto-install dependency) | <img src="https://img.shields.io/badge/run.bat-1x%20klik-22c55e?style=flat-square&logo=windows&logoColor=white" alt="run.bat"> |
| 3 | Atau klik shortcut desktop `NovaCode.lnk` | <img src="assets/icon_64.png" alt="Ikon NovaCode" width="28"> |
| 4 | Tunggu splash ~**4,2 detik** (boleh di-skip: klik / <kbd>Esc</kbd> / <kbd>Spasi</kbd>) | ⏳ |
| 5 | Panel AI langsung nongkrong di kanan, siap dipakai | 🤖 |

<details open>
<summary><b>Cara manual (terminal)</b></summary>

```bat
cd NovaCode
python -m pip install -r requirements.txt
python main.py
```

</details>

> [!NOTE]
> Saat install Python, centang **Add Python to PATH**. Windows 10/11 disarankan.

---

<a id="fitur"></a>

## ✨ Fitur dalam sekilas

| 🎨 **5 Tema** | 🤖 **AI Dock** | 🧩 **10 Provider** | ⌨️ **Shortcut** |
|:---:|:---:|:---:|:---:|
| Ember · Graphite · Moss · Paper · **Purple Moon** | Chat kanan + upload file/gambar | GGUF · Ollama · OpenAI · Gemini · dll | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> · <kbd>F5</kbd> |

| Ikon | Fitur | Singkatnya |
|:---:|---|---|
| 🖋️ | **Editor pintar** | Syntax highlighting 15+ bahasa, autocomplete 1 karakter, penutup otomatis, snippet. |
| 🗂️ | **Multi-tab 1 klik** | Klik sekali langsung pindah. Indikator `●` untuk file belum disimpan. |
| 📂 | **Explorer adaptif** | Lazy-load, klik kanan (new/rename/delete/copy path/open terminal), tombol **🏠 Home** & **📂 Pilih Folder**. |
| 🔍 | **Find & Replace** | Case-sensitive, whole word, ganti satu/semua, navigasi naik/turun. |
| 💻 | **Terminal + diagnosa** | cmd/PowerShell, riwayat ↑/↓, **Clear**, scrollbar, Output & Problems berisi saran perbaikan otomatis. |
| 🤖 | **Asisten AI** | Dock kanan, bubble chat, typing dots, lampiran teks/gambar, salin/sisip jawaban ke editor. |
| 🎬 | **Animasi halus** | Splash fade, tab glow, explorer stagger, panel AI melebar, tombol menyala. |
| 💾 | **Session restore** | Folder terakhir + 3 file terakhir dibuka lagi saat restart. |
| 🌍 | **Portable & multi-user** | Path user diambil dari `~`, setting disimpan per-user di `%APPDATA%`. |

<details>
<summary><b>🗺️ Peta alur aplikasi (klik untuk buka diagram)</b></summary>

```mermaid
flowchart LR
    LNK["NovaCode.lnk / run.bat"] --> SPLASH["Splash 4,2 detik"]
    SPLASH --> MAIN["Jendela utama"]
    MAIN --> EX["📂 Explorer"]
    MAIN --> ED["🖋️ Editor + Tab<br/>1 klik pindah"]
    MAIN --> AI["🤖 Panel AI dock kanan"]
    MAIN --> BP["💻 Terminal / Output / Problems"]
    AI --> PROV{"Pilih provider"}
    PROV --> LLAMA["🧠 GGUF lokal"]
    PROV --> OLLAMA["🦙 Ollama / LM Studio"]
    PROV --> CLOUD["☁️ OpenAI-compatible / Gemini"]
```

</details>

---

<a id="tema"></a>

## 🎨 Palet tema

Klik ikon roda gigi di toolbar atau menu **Theme** untuk mengganti. Ganti tema = jendela dibuat ulang otomatis supaya **semua** warna ikut berubah.

<p align="center">
  <img src="https://img.shields.io/badge/Ember-%23F59E0B?style=for-the-badge" alt="Ember">
  <img src="https://img.shields.io/badge/Graphite-%236B7280?style=for-the-badge" alt="Graphite">
  <img src="https://img.shields.io/badge/Moss-%2322A55F?style=for-the-badge" alt="Moss">
  <img src="https://img.shields.io/badge/Paper-%23F8FAFC?style=for-the-badge" alt="Paper">
  <img src="https://img.shields.io/badge/Purple%20Moon-%238B5CF6?style=for-the-badge" alt="Purple Moon">
</p>

> [!NOTE]
> Nama lama **Midnight / Aurora / Ocean / Nord Light** dan **Ungu Moon** otomatis dipetakan ke tema baru. Default tetap **Ember**.

---

<a id="ai"></a>

## 🤖 Asisten AI

<div align="center">

<img src="assets/logo_horizontal.png" alt="NovaCode AI" width="300">

</div>

Panel chat **langsung muncul di sisi kanan** saat aplikasi dibuka. Sembunyikan/tampilkan lagi lewat tombol **Asisten**, menu **View → Toggle AI Panel**, atau <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd>.

| 🧠 **Lokal** | ☁️ **Cloud** | 📎 **Lampiran** |
|---|---|---|
| Local GGUF · Ollama · LM Studio | OpenRouter · OpenAI · Gemini · Grok · DeepSeek · OpenCode · 9Router | Teks dibaca isinya, gambar jadi image part, biner cuma nama |

<details>
<summary><b>🔄 Alur kirim file + teks ala ChatGPT/Claude</b></summary>

```mermaid
sequenceDiagram
    participant U as Kamu
    participant P as Panel AI
    participant F as File / Gambar
    participant A as Provider

    U->>P: Ketik teks + klik 📎
    P->>F: Baca isi / encode gambar
    F-->>P: teks ≤ 8000 char · gambar ≤ 6 MB
    P->>A: teks + lampiran + kode aktif (opsional)
    A-->>P: jawaban (typing dots berjalan)
    P-->>U: bubble + tombol 📋 salin / 📥 sisip
    Note over P: Lampiran hilang setelah kirim,<br/>biar history nggak keulang
```

</details>

> [!WARNING]
> API key tersimpan lokal di `%APPDATA%\<username>\NovaCode\novacode_settings.json` (`<username>` = nama akun Windows yang sedang login, jadi beda-beda tiap komputer — misal `YOKOTO`, `KENZO`, atau `User`). **Jangan bagikan file ini** kalau berisi key pribadi. Env var seperti `OPENROUTER_API_KEY` juga didukung.

---

<a id="shortcut"></a>

## ⌨️ Pintasan keyboard

> [!TIP]
> <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> membuka **command palette** — semua perintah bisa dijalankan tanpa menu.

| File | Edit | Navigasi | Panel & AI |
|---|---|---|---|
| <kbd>Ctrl</kbd>+<kbd>N</kbd> · baru | <kbd>Ctrl</kbd>+<kbd>Z</kbd> · undo | <kbd>Ctrl</kbd>+<kbd>Tab</kbd> · tab next | <kbd>Ctrl</kbd>+<kbd>`</kbd> · terminal |
| <kbd>Ctrl</kbd>+<kbd>O</kbd> · buka | <kbd>Ctrl</kbd>+<kbd>/</kbd> · comment | <kbd>Ctrl</kbd>+<kbd>G</kbd> · goto line | <kbd>Ctrl</kbd>+<kbd>B</kbd> · explorer |
| <kbd>Ctrl</kbd>+<kbd>S</kbd> · simpan | <kbd>Ctrl</kbd>+<kbd>D</kbd> · duplicate | <kbd>Ctrl</kbd>+<kbd>F</kbd> · cari | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd> · AI |
| <kbd>Ctrl</kbd>+<kbd>W</kbd> · tutup tab | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>K</kbd> · hapus baris | <kbd>Ctrl</kbd>+<kbd>Space</kbd> · autocomplete | <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> · palette |
| <kbd>F5</kbd> · jalankan Python | <kbd>Alt</kbd>+<kbd>↑</kbd>/<kbd>↓</kbd> · pindah baris | <kbd>Tab</kbd>/<kbd>Shift</kbd>+<kbd>Tab</kbd> · indent | <kbd>Esc</kbd> · tutup popup / skip splash |

---

<a id="panduan"></a>

## 📖 Panduan cepat

<details>
<summary><b>📂 Membuka proyek & file</b></summary>

1. <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>O</kbd> → pilih folder.
2. Klik **dua kali** file di explorer → tab baru.
3. Klik **sekali** tab untuk pindah — sudah tidak perlu dobel klik.
4. Klik kanan explorer untuk *new file / rename / delete / copy path / open terminal*.

</details>

<details>
<summary><b>🔍 Cari, ganti, dan autocomplete</b></summary>

- <kbd>Ctrl</kbd>+<kbd>F</kbd> → ketik → semua kecocokan langsung tersorot.
- **Aa** = case-sensitive, **ab|** = whole word, **▾** = baris Replace.
- Mulai ketik **1 karakter** → saran muncul. <kbd>↑</kbd>/<kbd>↓</kbd> pilih, <kbd>Tab</kbd>/<kbd>Enter</kbd> terima, <kbd>Esc</kbd> tutup.
- Snippet menempatkan kursor otomatis di titik isian (`def`, `try`, `html5`, `select`).

</details>

<details>
<summary><b>💻 Terminal, Output, dan Problems</b></summary>

- <kbd>Ctrl</kbd>+<kbd>`</kbd> → panel bawah. Pilih **cmd** / **powershell**.
- Tombol **Clear** menghapus layar; scrollbar bisa digeser atas/bawah; tarik gagang atas untuk ubah **tinggi** panel.
- **Output** khusus error + timestamp. **Problems** menampilkan semua error, lokasi, **cara perbaikan**, dan klik 2× untuk loncat ke baris.
- Semua baris error yang cocok diberi penanda merah di editor. Jumlah error tampil sebagai badge tanpa memindahkan fokus Terminal.

</details>

<details>
<summary><b>🤖 Mengatur AI</b></summary>

1. Klik **⚙** di header panel AI → pilih provider → isi API key / model → **Simpan**.
2. **GGUF lokal:** pilih *Local GGUF*, **Browse** file `.gguf` (perlu `llama-cpp-python`).
3. **Tanpa API key:** jalankan Ollama (`localhost:11434`) atau LM Studio (`localhost:1234`).
4. Centang **Sertakan file aktif** supaya AI membaca kode yang sedang dibuka (maks 8000 karakter).
5. Quick prompt: **Jelaskan**, **Perbaiki**, **Contoh**. Jawaban bisa **📋 disalin** atau **📥 disisipkan**.

</details>

---

<a id="logo"></a>

## 🖼️ Logo kit

| Aset | Preview | Kegunaan |
|---|:---:|---|
| `assets/logo.png` | <img src="assets/logo.png" alt="Logo utama" width="56"> | Splash, dialog **Help → Tentang** |
| `assets/logo_horizontal.png` | <img src="assets/logo_horizontal.png" alt="Logo horizontal" width="130"> | README, website, banner |
| `assets/mark_dark.png` | <img src="assets/mark_dark.png" alt="Mark gelap" width="48"> | Tema terang |
| `assets/mark_light.png` | <img src="assets/mark_light.png" alt="Mark terang" width="48"> | Tema gelap |
| `assets/icon.ico` | <img src="assets/icon.ico" alt="Ikon aplikasi" width="48"> | `.exe`, jendela, shortcut desktop |
| `assets/logo.svg` / `logo_mark.svg` | 🧩 | Versi vektor untuk resize tanpa blur |

> Logo = huruf **N** geometris: batang kiri & diagonal berwarna kertas, batang kanan amber (aksen Ember). Edit di `tools/make_logo.py`, lalu jalankan `python tools/make_logo.py`.

---

<a id="struktur"></a>

## 🗂️ Struktur proyek

<details open>
<summary><b>Lihat pohon folder</b></summary>

```text
NovaCode/
├── main.py                  # Entry point, layout, menu, shortcut, session
├── requirements.txt         # customtkinter, pyinstaller, (opsional llama-cpp-python)
├── run.bat                  # Launcher Windows auto-install
├── build_exe.py             # PyInstaller -> dist/NovaCode.exe
├── README.md                # Dokumentasi ini
├── assets/                  # Logo & ikon
├── tools/
│   └── make_logo.py         # Generator logo
└── nova/
    ├── config.py            # 5 tema, warna, font, bahasa, path settings
    ├── animation.py         # Animasi ringan
    ├── splash.py            # Splash 4,2 detik (bisa di-skip)
    ├── completions.py       # Saran kode + snippet
    ├── diagnostics.py       # Pemindai error + saran perbaikan
    ├── icons.py             # Ikon garis (Pillow)
    ├── ai_chat.py           # Panel AI + upload + provider mapping
    ├── syntax.py            # Syntax highlighting
    ├── editor.py            # Widget editor
    ├── explorer.py          # File explorer
    ├── tabmanager.py        # Tab 1 klik
    ├── terminal.py          # Terminal + Clear + scrollbar
    ├── outputpanel.py       # Terminal / Output / Problems + resize tinggi
    ├── findreplace.py       # Find & Replace
    ├── palette.py           # Command palette
    └── widgets.py           # Tooltip
```

</details>

| Lapisan | File kunci | Badge |
|---|---|---|
| UI utama | `main.py` | <img src="https://img.shields.io/badge/entry-main.py-2F81F7?style=flat-square" alt="main.py"> |
| Tema & warna | `nova/config.py` | <img src="https://img.shields.io/badge/theme-5-8B5CF6?style=flat-square" alt="tema"> |
| AI | `nova/ai_chat.py` | <img src="https://img.shields.io/badge/providers-10-111827?style=flat-square" alt="provider"> |
| Build | `build_exe.py` | <img src="https://img.shields.io/badge/output-onefile-22c55e?style=flat-square" alt="onefile"> |

---

<a id="build"></a>

## 📦 Build `.exe`

```bat
python build_exe.py
```

Hasil: **`dist/NovaCode.exe`** — portable, tanpa perlu Python di komputer tujuan. `build_exe.py` otomatis memakai `assets/icon.ico` dan menyertakan folder `assets/`.

> [!NOTE]
> Ingin ukuran lebih kecil? Ganti `--onefile` dengan `--onedir` di `build_exe.py` (hasilnya folder berisi `.exe` + dependensi, tapi lebih cepat dibuka).

| Dependensi | Versi | Perlu? |
|---|---:|---|
| `customtkinter` | `>=5.2.0` | ✅ Runtime |
| `pyinstaller` | `>=6.0.0` | 🔨 Saat build saja |
| `llama-cpp-python` | `>=0.3.0` | ⚪ Opsional, GGUF lokal |

---

<a id="changelog"></a>

## ✅ Perubahan terbaru

- [x] Klik tab **sekali** langsung pindah (tidak perlu dobel klik).
- [x] Terminal punya tombol **Clear**, scrollbar vertikal, dan resize tinggi.
- [x] Panel AI **dock kanan**, muncul saat startup, toggle <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>A</kbd>.
- [x] Upload file/gambar ala ChatGPT/Claude: teks + lampiran dikirim bareng.
- [x] Shortcut desktop `NovaCode.lnk` siap pakai.
- [x] Splash diperlama jadi **4,2 detik**.
- [x] Tema **Purple Moon** + alias `Ungu Moon`.
- [x] README ini dibuat lebih visual: badge, diagram, kartu, dan collapsible.

---

<a id="troubleshoot"></a>

## 🛠️ Troubleshooting

<details>
<summary><b>Tabel bantuan (klik untuk buka)</b></summary>

| Gejala | Solusi cepat |
|---|---|
| `ModuleNotFoundError: customtkinter` | `python -m pip install customtkinter` atau jalankan `run.bat`. |
| Tampilan buram di high-DPI | Klik kanan `python.exe` → Properties → Compatibility → *Change high DPI settings* → centang override. |
| `.exe` langsung tertutup | Build ulang tanpa `--windowed` untuk melihat error, atau jalankan dari cmd. |
| File besar lambat highlight | Highlight dijalankan ulang setelah jeda 160 ms; untuk >1 MB sebaiknya dipecah. |
| Terminal tidak keluar output | Coba ganti shell ke **powershell** di header terminal. |
| AI gagal connect | Cek API key / base URL di **⚙**, atau nyalakan server Ollama / LM Studio. |

</details>

---

<a id="lisensi"></a>

## 📄 Lisensi & kredit

Proyek ini dibebaskan untuk **penggunaan pribadi dan pembelajaran**. Silakan dimodifikasi sesuai kebutuhan.

<p align="center">
  <img src="assets/mark_light.png" alt="NovaCode mark" width="36">
  <br>
  Dibuat dengan ❤️ memakai
  <br>
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/CustomTkinter-UI-2F81F7?style=flat-square" alt="CustomTkinter">
  <img src="https://img.shields.io/badge/PyInstaller-onefile-9FE6E0?style=flat-square" alt="PyInstaller">
</p>

> [!TIP]
> Masih ada ide lain? Simpan di sini, nanti kita bahas lagi bareng 🥳

<!-- novacode-fingerprint: novacode-fp-2026-6f4b8d2c9a1e47f0b3d5 -->
