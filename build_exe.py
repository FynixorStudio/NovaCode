#!/usr/bin/env python3
"""Build NovaCode menjadi file .exe Windows menggunakan PyInstaller.

Cara pakai:
    python build_exe.py

Output:
    dist/NovaCode.exe
"""

from __future__ import annotations

import os
import subprocess
import sys


def cleanup_old(here: str) -> None:
    """Hentikan instance lama & hapus exe lama agar rebuild tidak gagal."""
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/F", "/IM", "NovaCode.exe"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    old = os.path.join(here, "dist", "NovaCode.exe")
    if os.path.isfile(old):
        try:
            os.remove(old)
        except OSError as exc:
            print(f"Peringatan: gagal menghapus exe lama ({exc}).")


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller belum terpasang. Menginstall...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def main() -> None:
    ensure_pyinstaller()
    here = os.path.dirname(os.path.abspath(__file__))
    cleanup_old(here)
    icon = os.path.join(here, "assets", "icon.ico")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",          # tanpa console hitam
        "--onefile",           # satu file .exe
        "--name", "NovaCode",
        "--collect-data", "customtkinter",
        "--collect-submodules", "customtkinter",
        "--hidden-import", "customtkinter",
    ]
    assets = os.path.join(here, "assets")
    if os.path.isdir(assets):
        # logo & ikon dibaca saat runtime (nova.config.asset_path)
        cmd += ["--add-data", f"{assets}{os.pathsep}assets"]
    if os.path.isfile(icon):
        cmd += ["--icon", icon]

    cmd.append(os.path.join(here, "main.py"))

    print("Building:", " ".join(cmd))
    subprocess.check_call(cmd, cwd=here)
    print("\nSelesai! File ada di folder: dist/NovaCode.exe")


if __name__ == "__main__":
    main()
