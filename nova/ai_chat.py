"""Asisten AI di panel kanan: model GGUF lokal atau provider API cloud.

Semua request memakai urllib (stdlib), jadi tidak perlu install requests.
Model GGUF lokal dijalankan lewat llama-cpp-python bila tersedia, atau
pengguna bisa mengarahkan ke server LM Studio / llama.cpp / Ollama.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import queue
import threading
import urllib.error
import urllib.parse
import urllib.request
from tkinter import filedialog

import customtkinter as ctk

from . import animation, icons
from .config import COLORS, FONT_UI_TUPLE

PROVIDERS = {
    "OpenRouter": {
        "type": "openai", "base": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini", "key_env": "OPENROUTER_API_KEY",
    },
    "OpenAI": {
        "type": "openai", "base": "https://api.openai.com/v1",
        "model": "gpt-4o-mini", "key_env": "OPENAI_API_KEY",
    },
    "Gemini": {
        "type": "gemini", "base": "https://generativelanguage.googleapis.com/v1beta",
        "model": "gemini-2.0-flash", "key_env": "GEMINI_API_KEY",
    },
    "Grok (xAI)": {
        "type": "openai", "base": "https://api.x.ai/v1",
        "model": "grok-3-mini", "key_env": "XAI_API_KEY",
    },
    "DeepSeek": {
        "type": "openai", "base": "https://api.deepseek.com/v1",
        "model": "deepseek-chat", "key_env": "DEEPSEEK_API_KEY",
    },
    "OpenCode / Custom": {
        "type": "openai", "base": "https://api.opencode.ai/v1",
        "model": "opencode-mini", "key_env": "OPENCODE_API_KEY",
    },
    "9Router / Custom OpenAI": {
        "type": "openai", "base": "http://localhost:3310/v1",
        "model": "custom-model", "key_env": "CUSTOM_API_KEY",
    },
    "Ollama (lokal)": {
        "type": "openai", "base": "http://localhost:11434/v1",
        "model": "llama3.2", "key_env": "",
    },
    "LM Studio / llama.cpp server": {
        "type": "openai", "base": "http://localhost:1234/v1",
        "model": "local-model", "key_env": "",
    },
    "Local GGUF (llama.cpp)": {
        "type": "gguf", "base": "", "model": "", "key_env": "",
    },
}

DEFAULT_AI = {
    "provider": "OpenRouter",
    "api_key": "",
    "base_url": "",
    "model": "",
    "gguf_path": "",
    "include_file": True,
    "temperature": 0.7,
    "max_tokens": 1024,
}

SYSTEM_PROMPT = (
    "Kamu adalah asisten coding di dalam NovaCode. Jawab dalam Bahasa Indonesia "
    "yang singkat, jelas, dan praktis. Gunakan Markdown bila perlu."
)


class AIAssistant:
    """Mengelola panel chat yang nempel di sisi kanan editor."""

    def __init__(self, root, app, settings: dict, on_settings_saved=None, master=None):
        self.root = root
        self.app = app
        self.master = master or root
        self.settings = settings
        self.on_settings_saved = on_settings_saved
        self.visible = False
        self.history: list[dict] = []
        self._llm = None
        self._llm_path = ""
        self.queue: queue.Queue = queue.Queue()
        self._typing = False
        self._typing_idx = 0
        self._dots: list[ctk.CTkLabel] = []
        self._attach: dict | None = None
        self._panel_width = 380

        self._build_panel()
        self.root.after(80, self._drain)

    # ------------------------------------------------------------------
    def _ai(self) -> dict:
        cfg = dict(DEFAULT_AI)
        cfg.update(self.settings.get("ai", {}))
        return cfg

    # ------------------------------------------------------------------
    def _build_panel(self):
        # Panel ini jadi bagian layout (bukan overlay), jadi warnanya ikut tema.
        self.panel = ctk.CTkFrame(
            self.master, width=self._panel_width, corner_radius=0,
            fg_color=COLORS["bg"], border_width=1, border_color=COLORS["border"],
        )
        self.panel.pack_propagate(False)

        header = ctk.CTkFrame(self.panel, height=42, fg_color=COLORS["bg_light"],
                              corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="Asisten", font=("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_bright"], anchor="w").pack(side="left", padx=(12, 6))
        self.badge = ctk.CTkLabel(header, text="", font=("Segoe UI", 9),
                                  text_color=COLORS["muted"])
        self.badge.pack(side="left", padx=4)
        ctk.CTkButton(header, text="", image=icons.ctk_icon("close", COLORS["muted"], 12),
                      width=26, height=26, corner_radius=6,
                      fg_color="transparent", hover_color=COLORS["bg_lighter"],
                      command=self.hide).pack(side="right", padx=(0, 6))
        ctk.CTkButton(header, text="", image=icons.ctk_icon("gear", COLORS["muted"], 15),
                      width=26, height=26, corner_radius=6,
                      fg_color="transparent", hover_color=COLORS["bg_lighter"],
                      command=self.open_settings).pack(side="right", padx=(2, 0))

        ctx = ctk.CTkFrame(self.panel, fg_color="transparent", height=26)
        ctx.pack(fill="x", side="top", padx=10, pady=(4, 0))
        self.include_var = ctk.StringVar(
            value="on" if self._ai()["include_file"] else "off")
        ctk.CTkCheckBox(
            ctx, text="Sertakan file aktif", variable=self.include_var,
            onvalue="on", offvalue="off", width=150, height=20,
            font=("Segoe UI", 10), text_color=COLORS["muted"],
            command=self._save_include,
        ).pack(side="left")
        ctk.CTkLabel(ctx, text="GGUF / API", font=("Segoe UI", 9),
                     text_color=COLORS["muted"]).pack(side="right")

        chip_row = ctk.CTkFrame(self.panel, fg_color="transparent", height=22)
        chip_row.pack(fill="x", padx=10)
        chip_row.pack_propagate(False)
        self.attach_chip = ctk.CTkLabel(
            chip_row, text="", font=("Segoe UI", 10),
            text_color=COLORS["accent"], anchor="w",
        )
        self.attach_chip.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            chip_row, text="×", width=20, height=18, corner_radius=4,
            fg_color="transparent", hover_color=COLORS["bg_lighter"],
            text_color=COLORS["muted"], font=("Segoe UI", 12),
            command=self.clear_attach,
        ).pack(side="right")

        self.messages = ctk.CTkScrollableFrame(
            self.panel, fg_color=COLORS["bg_deep"], corner_radius=8)
        self.messages.pack(fill="both", expand=True, padx=10, pady=8)

        self.typing_frame = ctk.CTkFrame(self.panel, fg_color="transparent", height=20)
        for i in range(3):
            dot = ctk.CTkLabel(self.typing_frame, text="●", font=("Segoe UI", 11),
                               text_color=COLORS["muted"])
            dot.pack(side="left", padx=2)
            self._dots.append(dot)
        self.typing_frame.pack(fill="x", padx=16)
        self.typing_frame.pack_forget()

        quick = ctk.CTkFrame(self.panel, fg_color="transparent")
        quick.pack(fill="x", padx=10, pady=(0, 4))
        for label, prompt in (
            ("Jelaskan", "Jelaskan kode yang sedang saya buka."),
            ("Perbaiki", "Temukan bug pada kode ini dan berikan perbaikannya."),
            ("Contoh", "Buatkan contoh penggunaan kode ini."),
        ):
            ctk.CTkButton(
                quick, text=label, height=24, corner_radius=12, font=("Segoe UI", 10),
                fg_color=COLORS["bg_light"], hover_color=COLORS["accent_soft"],
                command=lambda p=prompt: self._quick(p),
            ).pack(side="left", padx=(0, 4))

        inp = ctk.CTkFrame(self.panel, fg_color=COLORS["bg_light"], corner_radius=10)
        inp.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(
            inp, text="", image=icons.ctk_icon("attach", COLORS["muted"], 16),
            width=30, height=54, corner_radius=8,
            fg_color="transparent", hover_color=COLORS["bg_lighter"],
            command=self.attach_file,
        ).pack(side="left", padx=(6, 2), pady=6)

        self.entry = ctk.CTkTextbox(
            inp, height=58, font=FONT_UI_TUPLE, fg_color=COLORS["bg_deep"],
            border_width=0, text_color=COLORS["text"],
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(2, 2), pady=6)
        self.entry.bind("<Return>", self._on_return)
        ctk.CTkButton(
            inp, text="", image=icons.ctk_icon("send", COLORS["white"], 18),
            width=38, height=54, corner_radius=8,
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self.send,
        ).pack(side="right", padx=(2, 6), pady=6)

        self._add_message(
            "assistant",
            "Pilih provider dan model lewat ikon roda gigi di atas, "
            "lalu tanyakan sesuatu tentang kode Anda.",
        )
        self._refresh_badge()

    # ------------------------------------------------------------------
    def _refresh_badge(self):
        cfg = self._ai()
        provider = cfg["provider"]
        model = cfg["model"] or PROVIDERS.get(provider, {}).get("model", "")
        self.badge.configure(text=f"{provider}" + (f" · {model[:18]}" if model else ""))

    def _save_include(self):
        self.settings.setdefault("ai", {})["include_file"] = self.include_var.get() == "on"
        if self.on_settings_saved:
            self.on_settings_saved()

    def _on_return(self, event):
        if event.state & 0x0001:  # Shift+Enter -> baris baru
            return
        self.send()
        return "break"

    def _quick(self, prompt: str):
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", prompt)
        self.send()

    # ------------------------------------------------------------------
    def attach_file(self):
        """Lampiran ala chat AI: teks dibaca isinya, gambar dikirim sebagai gambar."""
        path = filedialog.askopenfilename(
            title="Lampirkan file ke asisten",
            filetypes=[
                ("Gambar", "*.png *.jpg *.jpeg *.gif *.webp *.bmp"),
                ("Teks / kode", "*.txt *.py *.js *.ts *.json *.md *.html *.css "
                               "*.csv *.xml *.yml *.yaml"),
                ("Semua file", "*.*"),
            ],
        )
        if not path:
            return
        try:
            ext = os.path.splitext(path)[1].lower()
            if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}:
                with open(path, "rb") as handle:
                    raw = handle.read()
                if len(raw) > 6 * 1024 * 1024:
                    raise ValueError("Gambar terlalu besar (maks 6 MB).")
                mime = mimetypes.guess_type(path)[0] or "image/png"
                self._attach = {
                    "path": path, "kind": "image", "mime": mime,
                    "b64": base64.b64encode(raw).decode("ascii"),
                }
            else:
                with open(path, "rb") as handle:
                    raw = handle.read(20000)
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    self._attach = {
                        "path": path, "kind": "binary",
                        "size": os.path.getsize(path),
                    }
                else:
                    self._attach = {
                        "path": path, "kind": "text", "text": text[:8000],
                    }
        except Exception as exc:
            self._add_message("assistant", f"Gagal melampirkan file: {exc}")
            return
        self._update_attach_chip()

    def clear_attach(self):
        self._attach = None
        self._update_attach_chip()

    def _update_attach_chip(self):
        if not self._attach:
            self.attach_chip.configure(text="")
            return
        name = os.path.basename(self._attach["path"])
        if self._attach["kind"] == "image":
            label = f"🖼️ {name} (gambar)"
        elif self._attach["kind"] == "binary":
            label = f"📎 {name} (biner, cuma nama)"
        else:
            label = f"📎 {name} (teks)"
        self.attach_chip.configure(text=label)

    def _request_pieces(self, text: str):
        """Ubah lampiran jadi bagian request, tanpa nyimpan file di history."""
        if not self._attach:
            return text, []
        name = os.path.basename(self._attach["path"])
        if self._attach["kind"] == "image":
            url = f"data:{self._attach['mime']};base64,{self._attach['b64']}"
            return [
                {"type": "text", "text": text},
                {"type": "image_url", "image_url": {"url": url}},
            ], []
        if self._attach["kind"] == "text":
            note = f"File dilampirkan: {name}\n```\n{self._attach['text']}\n```"
            return text, [note]
        note = f"File dilampirkan: {name} ({self._attach['size']} byte, biner)."
        return text, [note]

    @staticmethod
    def _plain_content(content):
        """GGUF cuma baca teks, jadi gambar diterjemahkan jadi catatan."""
        if isinstance(content, str):
            return content
        chunks = []
        for part in content:
            if part.get("type") == "text":
                chunks.append(part.get("text", ""))
            elif part.get("type") == "image_url":
                chunks.append("[gambar dilampirkan: model GGUF tidak membaca gambar]")
        return "\n".join(chunks)

    @staticmethod
    def _gemini_parts(content):
        """Gemini pakai inline_data buat gambar, OpenAI pakai image_url."""
        if isinstance(content, str):
            return [{"text": content}]
        parts = []
        for part in content:
            if part.get("type") == "text":
                parts.append({"text": part.get("text", "")})
            elif part.get("type") == "image_url":
                url = part.get("image_url", {}).get("url", "")
                if url.startswith("data:"):
                    header, b64 = url.split(",", 1)
                    mime = header[5:].split(";")[0] or "image/png"
                    parts.append({"inline_data": {"mime_type": mime, "data": b64}})
                else:
                    parts.append({"text": f"[gambar: {url}]"})
        return parts

    # ------------------------------------------------------------------
    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()

    def show(self):
        if self.visible:
            return
        self.visible = True
        animation.cancel(self.panel, "dock")

        opts = {"side": "right", "fill": "y"}
        center = getattr(self.app, "center", None)
        if center is not None:
            try:
                if center.winfo_manager() == "pack":
                    opts["before"] = center
            except Exception:
                pass
        self.panel.pack(**opts)

        def setter(value):
            self.panel.configure(width=int(self._panel_width * value))

        self.panel.configure(width=int(self._panel_width * 0.2))
        animation.animate(self.panel, setter, 0.2, 1.0, duration=180, channel="dock")
        self._refresh_badge()

    def hide(self):
        if not self.visible:
            return
        self.visible = False
        animation.cancel(self.panel, "dock")
        self.panel.pack_forget()

    # ------------------------------------------------------------------
    def _add_message(self, role: str, text: str):
        row = ctk.CTkFrame(self.messages, fg_color="transparent")
        row.pack(fill="x", pady=3, padx=2)
        is_user = role == "user"
        bubble = ctk.CTkFrame(
            row, corner_radius=12,
            fg_color=COLORS["accent_soft"] if is_user else COLORS["bg_light"],
        )
        bubble.pack(side="right" if is_user else "left")
        ctk.CTkLabel(
            bubble, text=text, wraplength=296, justify="left",
            font=FONT_UI_TUPLE,
            text_color=COLORS["text_bright"] if is_user else COLORS["text"],
        ).pack(padx=10, pady=8)
        if not is_user:
            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="left", anchor="n", padx=(4, 0))
            ctk.CTkButton(actions, text="", image=icons.ctk_icon("copy", COLORS["muted"], 13),
                          width=24, height=24, corner_radius=6,
                          fg_color="transparent", hover_color=COLORS["bg_lighter"],
                          command=lambda: self._copy(text)).pack()
            ctk.CTkButton(actions, text="", image=icons.ctk_icon("insert", COLORS["muted"], 13),
                          width=24, height=24, corner_radius=6,
                          fg_color="transparent", hover_color=COLORS["bg_lighter"],
                          command=lambda: self._insert(text)).pack()
        self.messages.update_idletasks()
        try:
            self.messages._parent_canvas.yview_moveto(1.0)
        except Exception:
            pass

    def _copy(self, text: str):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def _insert(self, text: str):
        editor = self.app.tabman.active_editor
        if editor:
            editor.text.insert("insert", text)
            editor.focus_editor()

    # ------------------------------------------------------------------
    def _show_typing(self, value: bool):
        self._typing = value
        if value:
            self.typing_frame.pack(fill="x", padx=16)
            self._animate_dots()
        else:
            self.typing_frame.pack_forget()

    def _animate_dots(self):
        if not self._typing:
            return
        self._typing_idx = (self._typing_idx + 1) % 3
        for i, dot in enumerate(self._dots):
            dot.configure(text_color=COLORS["accent"] if i == self._typing_idx
                          else COLORS["muted"])
        self.root.after(220, self._animate_dots)

    # ------------------------------------------------------------------
    def send(self):
        text = self.entry.get("1.0", "end").strip()
        if not text or self._typing:
            return
        attach_name = os.path.basename(self._attach["path"]) if self._attach else ""
        display = text + (f"\n📎 {attach_name}" if attach_name else "")
        self.entry.delete("1.0", "end")
        self._add_message("user", display)
        self.history.append({"role": "user", "content": text})
        self.history = self.history[-10:]

        user_content, notes = self._request_pieces(text)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if self.include_var.get() == "on" and self.app.tabman.active_editor:
            content = self.app.tabman.active_editor.get_content()
            messages.append({
                "role": "system",
                "content": "Kode aktif (potongan):\n```\n" + content[:8000] + "\n```",
            })
        for note in notes:
            messages.append({"role": "system", "content": note})

        request_history = list(self.history)
        if isinstance(user_content, list) and request_history:
            request_history[-1] = {"role": "user", "content": user_content}
        messages.extend(request_history)

        self.clear_attach()
        self._show_typing(True)
        threading.Thread(target=self._worker, args=(messages,), daemon=True).start()

    def _worker(self, messages):
        try:
            reply = self._call_api(messages)
        except Exception as exc:
            reply = f"Gagal menghubungi AI: {exc}"
        self.queue.put(("reply", reply))

    def _drain(self):
        try:
            while True:
                kind, value = self.queue.get_nowait()
                if kind == "reply":
                    self._show_typing(False)
                    self._add_message("assistant", value)
                    self.history.append({"role": "assistant", "content": value})
                    self.history = self.history[-10:]
        except queue.Empty:
            pass
        self.root.after(80, self._drain)

    # ------------------------------------------------------------------
    def _call_api(self, messages: list[dict]) -> str:
        cfg = self._ai()
        provider = cfg["provider"]
        preset = PROVIDERS.get(provider, PROVIDERS["OpenRouter"])
        ptype = preset["type"]
        max_tokens = int(cfg.get("max_tokens") or 1024)
        temperature = float(cfg.get("temperature") or 0.7)

        if ptype == "gguf":
            return self._call_gguf(messages, cfg, max_tokens, temperature)

        base = (cfg.get("base_url") or preset["base"]).rstrip("/")
        model = cfg.get("model") or preset["model"]
        key = cfg.get("api_key") or os.environ.get(preset["key_env"], "")

        if ptype == "gemini":
            return self._call_gemini(base, model, key, messages, max_tokens, temperature)

        if not base:
            raise ValueError("Base URL belum diisi.")
        url = base + "/chat/completions"
        payload = {
            "model": model, "messages": messages,
            "max_tokens": max_tokens, "temperature": temperature,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}" if key else "",
        }
        if provider == "OpenRouter":
            headers["HTTP-Referer"] = "https://novacode.local"
            headers["X-Title"] = "NovaCode AI Assistant"
        data = self._request(url, payload, headers)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ValueError(str(data)[:400])

    def _call_gemini(self, base, model, key, messages, max_tokens, temperature):
        if not key:
            raise ValueError("API key Gemini belum diisi.")
        url = (f"{base}/models/{urllib.parse.quote(model)}:generateContent"
               f"?key={urllib.parse.quote(key)}")
        contents = []
        for msg in messages:
            parts = self._gemini_parts(msg["content"])
            if msg["role"] == "system":
                contents.append({"role": "user", "parts": parts})
            else:
                contents.append({
                    "role": "model" if msg["role"] == "assistant" else "user",
                    "parts": parts,
                })
        payload = {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": max_tokens,
                                 "temperature": temperature},
        }
        data = self._request(url, payload, {"Content-Type": "application/json"})
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            raise ValueError(str(data)[:400])

    def _call_gguf(self, messages, cfg, max_tokens, temperature):
        path = cfg.get("gguf_path", "")
        if not path or not os.path.isfile(path):
            raise ValueError("Pilih file model .gguf terlebih dahulu di Pengaturan AI.")
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ValueError(
                "llama-cpp-python belum terpasang. Jalankan: "
                "pip install llama-cpp-python")
        if self._llm is None or self._llm_path != path:
            self._llm = Llama(model_path=path, n_ctx=2048, verbose=False)
            self._llm_path = path
        # GGUF lokal belum ngerti gambar, jadi content-list diagu jadi teks dulu.
        messages = [
            {"role": msg["role"], "content": self._plain_content(msg["content"])}
            for msg in messages
        ]
        out = self._llm.create_chat_completion(
            messages=messages, max_tokens=max_tokens, temperature=temperature)
        return out["choices"][0]["message"]["content"]

    @staticmethod
    def _request(url: str, payload: dict, headers: dict) -> dict:
        req = urllib.request.Request(
            url, data=json.dumps(payload).encode("utf-8"),
            headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            raise ValueError(f"HTTP {exc.code}: {body[:300]}")

    # ------------------------------------------------------------------
    def open_settings(self):
        AISettingsDialog(
            self.root, self.settings,
            on_save=lambda: (self._refresh_badge(),
                             self.on_settings_saved() if self.on_settings_saved else None),
        )


class AISettingsDialog(ctk.CTkToplevel):
    def __init__(self, master, settings: dict, on_save=None):
        super().__init__(master)
        self.settings = settings
        self.on_save = on_save
        self.title("Pengaturan AI — NovaCode")
        self.geometry("520x580")
        self.resizable(False, False)
        self.transient(master)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORS["bg"])
        animation.fade_window(self)

        cfg = dict(DEFAULT_AI)
        cfg.update(settings.get("ai", {}))
        self.provider = ctk.StringVar(value=cfg["provider"])
        self.api_key = ctk.StringVar(value=cfg["api_key"])
        self.base_url = ctk.StringVar(value=cfg["base_url"])
        self.model = ctk.StringVar(value=cfg["model"])
        self.gguf_path = ctk.StringVar(value=cfg["gguf_path"])
        self.temperature = ctk.StringVar(value=str(cfg["temperature"]))
        self.max_tokens = ctk.StringVar(value=str(cfg["max_tokens"]))
        self.status = ctk.StringVar(value="")

        pad = dict(padx=16, pady=4)
        ctk.CTkLabel(self, text="PENGATURAN ASISTEN AI",
                     font=("Segoe UI", 15, "bold"),
                     text_color=COLORS["text_bright"]).pack(anchor="w", padx=16, pady=(16, 4))
        ctk.CTkLabel(self, text="Pilih provider cloud atau model GGUF lokal.",
                     font=("Segoe UI", 11), text_color=COLORS["muted"]).pack(
                         anchor="w", padx=16, pady=(0, 10))

        ctk.CTkLabel(self, text="Provider", font=("Segoe UI", 11)).pack(anchor="w", **pad)
        ctk.CTkOptionMenu(
            self, values=list(PROVIDERS), variable=self.provider, width=480,
            command=self._preset, fg_color=COLORS["bg_light"],
            button_color=COLORS["accent"], text_color=COLORS["text"],
        ).pack(**pad)

        ctk.CTkLabel(self, text="API Key (kosongkan untuk lokal / pakai env var)",
                     font=("Segoe UI", 11)).pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.api_key, show="*", width=480,
                     fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
                     text_color=COLORS["text"]).pack(**pad)

        ctk.CTkLabel(self, text="Base URL (OpenAI-compatible)",
                     font=("Segoe UI", 11)).pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.base_url, width=480,
                     fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
                     text_color=COLORS["text"]).pack(**pad)

        ctk.CTkLabel(self, text="Model", font=("Segoe UI", 11)).pack(anchor="w", **pad)
        ctk.CTkEntry(self, textvariable=self.model, width=480,
                     fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
                     text_color=COLORS["text"]).pack(**pad)

        ctk.CTkLabel(self, text="File model .gguf (khusus Local GGUF)",
                     font=("Segoe UI", 11)).pack(anchor="w", **pad)
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=4)
        ctk.CTkEntry(row, textvariable=self.gguf_path, width=380,
                     fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
                     text_color=COLORS["text"]).pack(side="left")
        ctk.CTkButton(row, text="Browse", width=86, command=self._browse,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["accent"],
                      text_color=COLORS["text"]).pack(side="left", padx=6)

        row2 = ctk.CTkFrame(self, fg_color="transparent")
        row2.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(row2, text="Temperature", font=("Segoe UI", 11)).pack(side="left")
        ctk.CTkEntry(row2, textvariable=self.temperature, width=60,
                     fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
                     text_color=COLORS["text"]).pack(side="left", padx=6)
        ctk.CTkLabel(row2, text="Max tokens", font=("Segoe UI", 11)).pack(side="left", padx=10)
        ctk.CTkEntry(row2, textvariable=self.max_tokens, width=70,
                     fg_color=COLORS["bg_deep"], border_color=COLORS["border"],
                     text_color=COLORS["text"]).pack(side="left", padx=6)

        ctk.CTkLabel(self, textvariable=self.status, font=("Segoe UI", 10),
                     text_color=COLORS["yellow"], wraplength=480).pack(
                         anchor="w", padx=16, pady=6)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=16, pady=(6, 16))
        ctk.CTkButton(actions, text="Simpan", width=120, fg_color=COLORS["accent"],
                      command=self._save).pack(side="left")
        ctk.CTkButton(actions, text="Batal", width=100, fg_color=COLORS["bg_light"],
                      text_color=COLORS["text"], command=self.destroy).pack(
                          side="left", padx=8)
        ctk.CTkLabel(actions,
                     text="API key disimpan lokal di novacode_settings.json",
                     font=("Segoe UI", 9), text_color=COLORS["muted"]).pack(side="right")

    def _preset(self, name: str):
        preset = PROVIDERS.get(name, {})
        if preset.get("base"):
            self.base_url.set(preset["base"])
        if preset.get("model"):
            self.model.set(preset["model"])
        self.status.set("Preset diterapkan. Sesuaikan model/key bila perlu.")

    def _browse(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Pilih model GGUF",
            filetypes=[("Model GGUF", "*.gguf"), ("Semua file", "*")])
        if path:
            self.gguf_path.set(path)
            self.provider.set("Local GGUF (llama.cpp)")
            self.status.set("Model GGUF dipilih.")

    def _save(self):
        self.settings["ai"] = {
            "provider": self.provider.get(),
            "api_key": self.api_key.get().strip(),
            "base_url": self.base_url.get().strip(),
            "model": self.model.get().strip(),
            "gguf_path": self.gguf_path.get().strip(),
            "include_file": self.settings.get("ai", {}).get("include_file", True),
            "temperature": float(self.temperature.get() or 0.7),
            "max_tokens": int(self.max_tokens.get() or 1024),
        }
        if self.on_save:
            self.on_save()
        self.destroy()
