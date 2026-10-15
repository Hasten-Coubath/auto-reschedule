#!/usr/bin/env python3
"""Gera os ícones do aplicativo a partir de ``web/icon.svg``.

Saídas (todas em ``web/``):

* ``icon.ico``      – ícone do Windows (atalho e executável), com 16 a 256 px;
* ``icon-192.png`` e ``icon-512.png`` – usados pelo manifesto da janela do app.

O SVG é desenhado pelo próprio Edge/Chrome em modo invisível (headless), então
o resultado fica idêntico ao ícone da interface. Rode de novo sempre que mudar
o ``icon.svg``:

    python tools/gerar_icones.py
"""

from __future__ import annotations

import struct
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import find_app_browser  # noqa: E402

WEB = ROOT / "web"
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
PNG_SIZES = (192, 512)

PAGE = """<!doctype html><html><head><style>
html, body {{ margin: 0; background: transparent; overflow: hidden; }}
img {{ position: fixed; left: 0; top: 0; width: {n}px; height: {n}px; }}
</style></head><body><img src="{svg}"></body></html>"""


def render(browser: str, svg: Path, size: int, workdir: Path) -> bytes:
    page = workdir / f"icon-{size}.html"
    out = workdir / f"icon-{size}.png"
    page.write_text(PAGE.format(n=size, svg=svg.as_uri()), encoding="utf-8")
    subprocess.run(
        [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            "--default-background-color=00000000",
            f"--window-size={size},{size}",
            f"--screenshot={out}",
            page.as_uri(),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=60,
        check=False,
    )
    data = out.read_bytes() if out.exists() else b""
    if data[:8] != b"\x89PNG\r\n\x1a\n" or struct.unpack(">II", data[16:24]) != (size, size):
        raise RuntimeError(f"Não foi possível gerar a imagem de {size}px.")
    return data


def build_ico(images: dict[int, bytes]) -> bytes:
    """Monta um .ico com as imagens PNG (formato aceito desde o Windows Vista)."""
    header = struct.pack("<HHH", 0, 1, len(images))
    entries = b""
    blobs = b""
    offset = 6 + 16 * len(images)
    for size, png in sorted(images.items()):
        dim = 0 if size >= 256 else size  # 0 significa 256
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset + len(blobs))
        blobs += png
    return header + entries + blobs


def main() -> int:
    browser = find_app_browser()
    if not browser:
        print("Edge ou Chrome não encontrado — eles são usados para desenhar o SVG.")
        return 1
    svg = WEB / "icon.svg"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        images = {size: render(browser, svg, size, work) for size in ICO_SIZES}
        (WEB / "icon.ico").write_bytes(build_ico(images))
        for size in PNG_SIZES:
            (WEB / f"icon-{size}.png").write_bytes(render(browser, svg, size, work))
    print("Ícones gerados em web/: icon.ico, " + ", ".join(f"icon-{s}.png" for s in PNG_SIZES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
