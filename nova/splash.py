

from __future__ import annotations

import math
import time
import tkinter as tk

from PIL import Image, ImageTk

from .animation import mix
from .config import APP_NAME, APP_VERSION, COLORS, asset_path, user_name

_W, _H = 520, 310
_CX = _W // 2

_STEPS = (
    (0.00, "Menyiapkan tema..."),
    (0.28, "Memuat editor..."),
    (0.55, "Menyiapkan explorer & terminal..."),
    (0.80, "Menghubungkan asisten AI..."),
    (0.97, "Siap!"),
)


class SplashScreen(tk.Toplevel):
    

    def __init__(self, parent, on_done=None, duration: float = 4.2):
        super().__init__(parent)
        self._parent = parent
        self._on_done = on_done
        self._duration = max(0.6, duration)
        self._finished = False
        self._after_id = None
        self._start = 0.0
        self._logo_src = None
        self._logo_photo = None

        bg = COLORS["bg_deep"]
        self.configure(bg=bg)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.resizable(False, False)
        self.title(f"{APP_NAME} — memuat")
        self._center()

        self.canvas = tk.Canvas(self, width=_W, height=_H, bg=bg,
                                highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self._draw(bg)

        try:
            self._logo_src = Image.open(asset_path("logo.png")).convert("RGBA")
        except Exception:
            self._logo_src = None

        for key in ("<Escape>", "<space>", "<Button-1>"):
            self.bind(key, lambda _e: self.skip())
        self.withdraw()
        self.update_idletasks()

    
    def _center(self):
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{_W}x{_H}+{(sw - _W) // 2}+{(sh - _H) // 2}")

    def _draw(self, bg: str):
        c = self.canvas
        accent = COLORS["accent"]

        c.create_rectangle(0, 0, _W, 3, fill=accent, outline="")
        c.create_rectangle(0, _H - 1, _W, _H, fill=COLORS["border"], outline="")

        self._halo = c.create_oval(0, 0, 0, 0, outline=mix(bg, accent, 0.12), width=1)
        self._glow = c.create_oval(0, 0, 0, 0, outline=accent, width=2)
        self._logo = c.create_image(_CX, 84)

        c.create_text(_CX, 158, text=APP_NAME, fill=COLORS["text_bright"],
                      font=("Segoe UI", 23, "bold"))
        c.create_text(_CX, 184, text="EDITOR KODE MODERN", fill=COLORS["muted"],
                      font=("Segoe UI", 9))

        y = 222
        c.create_line(80, y, _W - 80, y, fill=COLORS["bg_light"], width=6,
                      capstyle=tk.ROUND)
        self._bar = c.create_line(80, y, 80, y, fill=accent, width=6,
                                  capstyle=tk.ROUND)

        self._status = c.create_text(_CX, 253, text=_STEPS[0][1],
                                     fill=COLORS["muted"], font=("Segoe UI", 11))
        c.create_text(_CX, 286,
                      text=f"{user_name()}  ·  v{APP_VERSION}     •     klik untuk lewati",
                      fill=COLORS["muted"], font=("Segoe UI", 9))

    
    def start(self):
        self.deiconify()
        self.lift()
        self.attributes("-alpha", 0.0)
        self._start = time.monotonic()
        self._tick()

    def skip(self):
        
        if not self._finished:
            self._start = time.monotonic() - (self._duration - 0.30)
            self._tick()

    def _tick(self):
        if self._finished:
            return
        elapsed = time.monotonic() - self._start
        p = min(1.0, elapsed / self._duration)
        ease = 1 - (1 - p) ** 3

        
        fade_in = min(1.0, elapsed / 0.28)
        fade_out = (1.0 if elapsed < self._duration - 0.34
                    else max(0.0, (self._duration - elapsed) / 0.34))
        try:
            self.attributes("-alpha", max(0.0, min(fade_in, fade_out)))
        except Exception:
            pass

        
        grow = 1 - (1 - min(1.0, p * 1.6)) ** 3
        size = int(60 + 42 * grow + 1.6 * math.sin(elapsed * 6))
        if self._logo_src is not None:
            try:
                photo = ImageTk.PhotoImage(
                    self._logo_src.resize((size, size), Image.LANCZOS))
                self.canvas.itemconfigure(self._logo, image=photo)
                
                self._logo_photo = photo
                self.canvas.coords(self._logo, _CX, 84)
            except Exception:
                pass

        
        beat = 0.5 + 0.5 * math.sin(elapsed * 4.2)
        r = 60 + 5 * math.sin(elapsed * 4.2)
        self.canvas.coords(self._glow, _CX - r, 84 - r, _CX + r, 84 + r)
        self.canvas.itemconfigure(
            self._glow, outline=mix(COLORS["bg_deep"], COLORS["accent"], 0.30 + 0.35 * beat))
        r2 = r + 9
        self.canvas.coords(self._halo, _CX - r2, 84 - r2, _CX + r2, 84 + r2)

        
        self.canvas.coords(self._bar, 80, 222, 80 + 360 * ease, 222)
        label = _STEPS[0][1]
        for threshold, text in _STEPS:
            if ease >= threshold:
                label = text
        if self.canvas.itemcget(self._status, "text") != label:
            self.canvas.itemconfigure(self._status, text=label)

        if elapsed >= self._duration:
            self._finish()
        else:
            self._after_id = self.after(24, self._tick)

    def _finish(self):
        if self._finished:
            return
        self._finished = True
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        callback = self._on_done
        self._on_done = None
        try:
            self.destroy()
        except Exception:
            pass
        if callback:
            callback()
