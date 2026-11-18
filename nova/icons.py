

from __future__ import annotations

from PIL import Image, ImageDraw

_GRID = 24          
_SS = 8             
_scale = 1.0        
_keep: dict = {}    


ICONS: dict[str, list[tuple]] = {
    "plus": [("line", [(12, 5), (12, 19)]), ("line", [(5, 12), (19, 12)])],
    "close": [("line", [(6, 6), (18, 18)]), ("line", [(18, 6), (6, 18)])],
    "minus": [("line", [(5, 12), (19, 12)])],
    "folder": [("poly", [(3, 7), (9, 7), (11, 9), (21, 9), (21, 19), (3, 19)])],
    "folder_open": [
        ("line", [(3, 18), (3, 6), (9, 6), (11, 8), (19, 8), (19, 11)]),
        ("poly", [(3, 18), (6, 11), (22, 11), (19, 18)]),
    ],
    "file": [
        ("poly", [(6, 3), (14, 3), (19, 8), (19, 21), (6, 21)]),
        ("line", [(14, 3), (14, 8), (19, 8)]),
    ],
    "save": [
        ("poly", [(4, 4), (17, 4), (20, 7), (20, 20), (4, 20)]),
        ("line", [(8, 4), (8, 9), (15, 9), (15, 4)]),
        ("line", [(7, 20), (7, 14), (17, 14), (17, 20)]),
    ],
    "play": [("fill", [(8, 5), (19, 12), (8, 19)])],
    "stop": [("fill", [(7, 7), (17, 7), (17, 17), (7, 17)])],
    "refresh": [
        ("arc", 12, 12, 7, 40, 330),
        ("line", [(17.5, 3.5), (18.5, 8.5), (13.5, 8.5)]),
    ],
    "home": [
        ("line", [(3, 12), (12, 4), (21, 12)]),
        ("line", [(5.5, 10.5), (5.5, 20), (18.5, 20), (18.5, 10.5)]),
        ("line", [(10, 20), (10, 14), (14, 14), (14, 20)]),
    ],
    "gear": [
        ("circle", 12, 12, 3),
        ("circle", 12, 12, 7.5),
        ("line", [(12, 2.5), (12, 4.5)]), ("line", [(12, 19.5), (12, 21.5)]),
        ("line", [(2.5, 12), (4.5, 12)]), ("line", [(19.5, 12), (21.5, 12)]),
        ("line", [(5.3, 5.3), (6.7, 6.7)]), ("line", [(17.3, 17.3), (18.7, 18.7)]),
        ("line", [(18.7, 5.3), (17.3, 6.7)]), ("line", [(6.7, 17.3), (5.3, 18.7)]),
    ],
    "copy": [
        ("poly", [(9, 9), (20, 9), (20, 20), (9, 20)]),
        ("line", [(15, 9), (15, 4), (4, 4), (4, 15), (9, 15)]),
    ],
    "insert": [
        ("line", [(12, 4), (12, 15)]),
        ("line", [(7, 10.5), (12, 15.5), (17, 10.5)]),
        ("line", [(5, 20), (19, 20)]),
    ],
    "send": [
        ("line", [(12, 19), (12, 5)]),
        ("line", [(6, 11), (12, 5), (18, 11)]),
    ],
    "attach": [
        ("line", [(8, 16), (17, 7)]),
        ("line", [(5, 13), (14, 4), (20, 10), (11, 19), (7, 15)]),
    ],
    "trash": [
        ("line", [(4, 7), (20, 7)]),
        ("line", [(9, 7), (9, 4), (15, 4), (15, 7)]),
        ("line", [(6, 7), (7, 20), (17, 20), (18, 7)]),
        ("line", [(10.5, 11), (10.5, 16)]), ("line", [(13.5, 11), (13.5, 16)]),
    ],
    "chat": [
        ("poly", [(4, 5), (20, 5), (20, 16), (12, 16), (7.5, 20), (7.5, 16), (4, 16)]),
    ],
    "search": [
        ("circle", 10.5, 10.5, 6),
        ("line", [(15, 15), (20, 20)]),
    ],
    "chevron_up": [("line", [(6, 15), (12, 9), (18, 15)])],
    "chevron_down": [("line", [(6, 9), (12, 15), (18, 9)])],
}


def set_scale(root) -> None:
    
    global _scale
    try:
        _scale = max(1.0, float(root.winfo_fpixels("1i")) / 96.0)
    except Exception:
        _scale = 1.0


def _rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), alpha)
    except (ValueError, IndexError):
        return (128, 128, 128, alpha)


def render(name: str, size: int = 16, color: str = "#cccccc",
           stroke: float = 1.9) -> Image.Image:
    
    ops = ICONS.get(name) or ICONS["file"]
    big = max(8, int(size)) * _SS
    k = big / _GRID
    sw = max(2, int(round(stroke * k)))
    rgba = _rgba(color)
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    def P(pt):
        return (pt[0] * k, pt[1] * k)

    def polyline(points, closed=False):
        pts = [P(p) for p in points]
        if closed:
            pts = pts + [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            d.line([a, b], fill=rgba, width=sw)
        for x, y in pts:                      
            d.ellipse([x - sw / 2, y - sw / 2, x + sw / 2, y + sw / 2], fill=rgba)

    for op in ops:
        kind = op[0]
        if kind == "line":
            polyline(op[1])
        elif kind == "poly":
            polyline(op[1], closed=True)
        elif kind == "fill":
            d.polygon([P(p) for p in op[1]], fill=rgba)
        elif kind == "circle":
            _, cx, cy, r = op
            R = r * k + sw / 2
            d.ellipse([cx * k - R, cy * k - R, cx * k + R, cy * k + R],
                      outline=rgba, width=sw)
        elif kind == "dot":
            _, cx, cy, r = op
            R = r * k
            d.ellipse([cx * k - R, cy * k - R, cx * k + R, cy * k + R], fill=rgba)
        elif kind == "arc":
            _, cx, cy, r, a0, a1 = op
            R = r * k + sw / 2
            d.arc([cx * k - R, cy * k - R, cx * k + R, cy * k + R],
                  start=a0, end=a1, fill=rgba, width=sw)

    return img.resize((int(size), int(size)), Image.LANCZOS)


def ctk_icon(name: str, color: str, size: int = 16):
    
    import customtkinter as ctk
    key = ("ctk", name, color, size)
    if key not in _keep:
        img = render(name, int(size * 3), color)
        _keep[key] = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    return _keep[key]


def tk_icon(name: str, color: str, size: int = 16):
    
    from PIL import ImageTk
    px = max(8, int(round(size * _scale)))
    key = ("tk", name, color, px)
    if key not in _keep:
        _keep[key] = ImageTk.PhotoImage(render(name, px, color))
    return _keep[key]
