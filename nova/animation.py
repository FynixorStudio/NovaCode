

from __future__ import annotations

from .config import COLORS


def _rgb(value) -> tuple[int, int, int]:
    if isinstance(value, (tuple, list)):
        value = value[0] if value else "#808080"
    if not isinstance(value, str) or not value.startswith("#"):
        value = "#808080"
    s = value[1:]
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        return (128, 128, 128)
    try:
        return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (128, 128, 128)


def mix(color_a, color_b, t: float) -> str:
    a, b = _rgb(color_a), _rgb(color_b)
    t = max(0.0, min(1.0, t))
    return "#%02x%02x%02x" % tuple(
        int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _solid(color):
    
    if isinstance(color, (tuple, list)):
        color = color[0] if color else None
    if not isinstance(color, str) or not color.startswith("#"):
        return COLORS["bg"]
    return color


def animate(widget, setter, start: float, end: float, duration: int = 220,
            steps: int = 12, on_done=None, channel: str = "default"):
    
    attr = f"_nova_anim_{channel}"
    token = getattr(widget, attr, 0) + 1
    setattr(widget, attr, token)

    def step(i: int):
        if getattr(widget, attr, 0) != token:
            return
        t = i / steps
        eased = 1 - (1 - t) ** 3          
        value = start + (end - start) * eased
        try:
            setter(value)
        except Exception:
            pass
        if i < steps:
            widget.after(max(1, duration // steps), lambda: step(i + 1))
        elif on_done:
            on_done()

    step(0)


def animate_color(widget, start, end, duration: int = 180, on_done=None,
                  key: str = "fg_color"):
    a, b = _solid(start), _solid(end)

    def setter(value):
        
        widget.configure(**{key: mix(a, b, value)})

    return animate(widget, setter, 0.0, 1.0, duration=duration,
                   on_done=on_done, channel=key)


def add_hover(widget, normal=None, hover=None, duration: int = 150,
              glow: bool = True):
    
    try:
        current = widget.cget("fg_color")
    except Exception:
        current = None
    normal = _solid(normal if normal is not None else current)
    hover = _solid(hover if hover is not None else COLORS["accent"])

    try:
        widget.configure(cursor="hand2")
    except Exception:
        pass

    def on_enter(_event=None):
        animate_color(widget, normal, hover, duration)
        if glow:
            try:
                widget.configure(border_width=1, border_color=hover)
            except Exception:
                pass

    def on_leave(_event=None):
        animate_color(widget, hover, normal, duration)
        if glow:
            try:
                widget.configure(border_width=0)
            except Exception:
                pass

    widget.bind("<Enter>", on_enter, add="+")
    widget.bind("<Leave>", on_leave, add="+")
    widget._nova_hover_normal = normal
    widget._nova_hover_color = hover


def pulse(widget, color_a, color_b, duration: int = 900):
    
    token = getattr(widget, "_nova_pulse", 0) + 1
    widget._nova_pulse = token
    a, b = _solid(color_a), _solid(color_b)

    def cycle(forward: bool):
        if getattr(widget, "_nova_pulse", 0) != token:
            return
        animate_color(
            widget, a if forward else b, b if forward else a,
            duration=duration // 2,
            on_done=lambda: cycle(not forward),
        )

    cycle(True)


def stop_pulse(widget):
    widget._nova_pulse = getattr(widget, "_nova_pulse", 0) + 1


def cancel(widget, *channels: str):
    
    for channel in channels:
        attr = f"_nova_anim_{channel}"
        setattr(widget, attr, getattr(widget, attr, 0) + 1)


def fade_window(window, start: float = 0.0, end: float = 1.0,
                duration: int = 240):
    try:
        window.attributes("-alpha", start)
    except Exception:
        return

    def setter(value):
        window.attributes("-alpha", value)

    animate(window, setter, start, end, duration=duration)


def slide(widget, setter, start: float, end: float, duration: int = 280):
    
    return animate(widget, setter, start, end, duration=duration)
