

from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), "assets")

INK = "#181715"      
PAPER = "#efebe3"    
AMBER = "#e5a24b"    
GRID = 1024
SS = 4               


X0, X1 = 262, 762
Y0, Y1 = 250, 774
W = 120              
CUT = 120            

LEFT = [(X0, Y0), (X0 + W, Y0), (X0 + W, Y1), (X0, Y1)]
DIAG = [(X0, Y0), (X0 + W + 8, Y0), (X1, Y1), (X1 - W - 8, Y1)]
RIGHT = [(X1 - W, Y0 + CUT), (X1, Y0), (X1, Y1), (X1 - W, Y1)]


def hex_rgb(h: str, a: int = 255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def squircle_points(n: float = 5.0, steps: int = 720):
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        pts.append((GRID / 2 + GRID / 2 * math.copysign(abs(c) ** (2 / n), c),
                    GRID / 2 + GRID / 2 * math.copysign(abs(s) ** (2 / n), s)))
    return pts


def _poly(draw, pts, k, fill):
    draw.polygon([(x * k, y * k) for x, y in pts], fill=fill)


def render(size: int, *, background: bool = True, paper=PAPER, amber=AMBER,
           bg=INK, glyph_scale: float = 1.0) -> Image.Image:
    big = size * SS
    k = big / GRID
    layer = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    if background:
        _poly(d, squircle_points(), k, hex_rgb(bg))

    glyph = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    g = ImageDraw.Draw(glyph)
    _poly(g, LEFT, k, hex_rgb(paper))
    _poly(g, DIAG, k, hex_rgb(paper))
    _poly(g, RIGHT, k, hex_rgb(amber))
    if glyph_scale != 1.0:
        ns = int(big * glyph_scale)
        glyph = glyph.resize((ns, ns), Image.LANCZOS)
        canvas = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        canvas.alpha_composite(glyph, ((big - ns) // 2, (big - ns) // 2))
        glyph = canvas
    layer.alpha_composite(glyph)
    return layer.resize((size, size), Image.LANCZOS)


def tight_mark(size: int, paper=PAPER, amber=AMBER) -> Image.Image:
    
    img = render(1024, background=False, paper=paper, amber=amber)
    box = img.getbbox()
    img = img.crop(box)
    side = max(img.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(img, ((side - img.width) // 2, (side - img.height) // 2))
    return sq.resize((size, size), Image.LANCZOS)


def svg(background=True, paper=PAPER, amber=AMBER, bg=INK) -> str:
    def pts(p):
        return " ".join(f"{x},{y}" for x, y in p)
    sq = " ".join(f"{x:.1f},{y:.1f}" for x, y in squircle_points(steps=180))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {GRID} {GRID}" '
             f'width="512" height="512">']
    if background:
        parts.append(f'  <polygon fill="{bg}" points="{sq}"/>')
    parts.append(f'  <polygon fill="{paper}" points="{pts(LEFT)}"/>')
    parts.append(f'  <polygon fill="{paper}" points="{pts(DIAG)}"/>')
    parts.append(f'  <polygon fill="{amber}" points="{pts(RIGHT)}"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def find_font(size: int):
    for name in ("segoeuib.ttf", "Inter-Bold.otf", "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
                 "arialbd.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def horizontal(paper=PAPER, amber=AMBER, bg=None, height=160) -> Image.Image:
    
    mark = render(height, background=True)
    font = find_font(int(height * 0.50))
    text_w = int(font.getlength("NovaCode"))
    pad = int(height * 0.28)
    img = Image.new("RGBA", (height + pad + text_w + 8, height), (0, 0, 0, 0) if bg is None else hex_rgb(bg))
    img.alpha_composite(mark, (0, 0))
    d = ImageDraw.Draw(img)
    asc, desc = font.getmetrics()
    y = (height - (asc + desc)) // 2
    d.text((height + pad, y), "Nova", font=font, fill=hex_rgb(paper))
    nw = int(font.getlength("Nova"))
    d.text((height + pad + nw, y), "Code", font=font, fill=hex_rgb(amber))
    return img


def main():
    os.makedirs(OUT, exist_ok=True)

    full = render(1024)
    full.resize((512, 512), Image.LANCZOS).save(os.path.join(OUT, "logo.png"))

    sizes = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]
    frames = [render(s) for s in sizes]
    frames[-1].save(os.path.join(OUT, "icon.ico"), format="ICO",
                    sizes=[(s, s) for s in sizes], append_images=frames[:-1])

    
    render(64).save(os.path.join(OUT, "icon_64.png"))

    
    tight_mark(256).save(os.path.join(OUT, "mark_dark.png"))
    tight_mark(256, paper="#1d1c1a", amber="#c9822a").save(os.path.join(OUT, "mark_light.png"))

    with open(os.path.join(OUT, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(svg())
    with open(os.path.join(OUT, "logo_mark.svg"), "w", encoding="utf-8") as f:
        f.write(svg(background=False))

    horizontal().save(os.path.join(OUT, "logo_horizontal.png"))
    print("Selesai ->", OUT)


if __name__ == "__main__":
    main()
