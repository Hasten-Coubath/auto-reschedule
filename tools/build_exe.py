#!/usr/bin/env python3
"""Empacota o Auto Reschedule em um executável único com o PyInstaller.

    pip install -r requirements-build.txt
    python tools/build_exe.py

Resultado: ``dist/AutoReschedule.exe`` (ou ``dist/AutoReschedule`` no
Linux/macOS). O executável já leva o Python e a interface dentro dele; os
dados são gravados na pasta ``data/`` ao lado do executável.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        import PyInstaller.__main__ as pyinstaller
    except ImportError:
        print("PyInstaller não está instalado. Rode:  python -m pip install -r requirements-build.txt")
        return 1

    build = ROOT / "build"
    args = [
        str(ROOT / "app.py"),
        "--name=AutoReschedule",
        "--onefile",
        "--windowed",  # sem janela de console; encerre pelo menu "⋯ > Encerrar aplicativo"
        "--noconfirm",
        "--clean",
        f"--icon={ROOT / 'web' / 'icon.ico'}",
        f"--add-data={ROOT / 'web'}{os.pathsep}web",
        f"--distpath={ROOT / 'dist'}",
        f"--workpath={build}",
        f"--specpath={build}",
    ]
    pyinstaller.run(args)
    exe = ROOT / "dist" / ("AutoReschedule.exe" if sys.platform == "win32" else "AutoReschedule")
    print(f"\nPronto: {exe}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
