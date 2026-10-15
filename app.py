#!/usr/bin/env python3
"""Inicia o Auto Reschedule: sobe o servidor local e abre a janela do aplicativo.

Uso:
    python app.py                 # abre em uma janela própria
    python app.py --tab           # abre como aba comum do navegador
    python app.py --no-browser    # só inicia o servidor
    python app.py --port 9000     # usa outra porta
    python app.py --data C:/caminho/dados.json
    python app.py --criar-atalho  # cria atalho com ícone na Área de Trabalho (Windows)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

from autoreschedule import __author__, __version__
from autoreschedule.server import APP_ID, create_server
from autoreschedule.storage import Store

# No executável (.exe do PyInstaller) os dados ficam ao lado do próprio .exe.
FROZEN = getattr(sys, "frozen", False)
ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
DEFAULT_PORT = 8765
DEFAULT_DATA = ROOT / "data" / "dados.json"


def _fix_console() -> None:
    # Com pythonw (sem console) stdout/stderr não existem.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass


def already_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1) as resp:
            return json.load(resp).get("app") == APP_ID
    except Exception:
        return False


def find_app_browser() -> str | None:
    """Procura Edge/Chrome/Chromium, que conseguem abrir o app em janela própria."""
    candidates: list[Path] = []
    if sys.platform == "win32":
        for env in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                candidates += [
                    Path(base, "Microsoft", "Edge", "Application", "msedge.exe"),
                    Path(base, "Google", "Chrome", "Application", "chrome.exe"),
                ]
    elif sys.platform == "darwin":
        candidates += [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
        ]
    for path in candidates:
        if path.exists():
            return str(path)
    for name in ("google-chrome", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def open_window(url: str, as_tab: bool) -> None:
    if not as_tab:
        exe = find_app_browser()
        if exe:
            try:
                subprocess.Popen(
                    [exe, f"--app={url}", "--window-size=1240,860"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except OSError:
                pass
    webbrowser.open(url)


def create_shortcuts(folders: list[str] | None = None) -> int:
    """Cria o atalho "Auto Reschedule" (com o ícone do app) na Área de Trabalho e no Menu Iniciar."""
    if sys.platform != "win32":
        print("A criação de atalho só está disponível no Windows.")
        return 1
    if FROZEN:
        target, arguments, icon = sys.executable, "", sys.executable
    else:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        target = str(pythonw if pythonw.exists() else Path(sys.executable))
        arguments = f'"{ROOT / "app.py"}"'
        icon = str(ROOT / "web" / "icon.ico")
    # Os valores vão por variáveis de ambiente para não ter problema com aspas/espaços nos caminhos.
    script = (
        "$ErrorActionPreference = 'Stop';"
        "$shell = New-Object -ComObject WScript.Shell;"
        "$dirs = if ($env:AR_DIRS) { $env:AR_DIRS -split '[|]' } else "
        "{ @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs')) };"
        "foreach ($d in $dirs) {"
        "  $lnk = $shell.CreateShortcut((Join-Path $d 'Auto Reschedule.lnk'));"
        "  $lnk.TargetPath = $env:AR_TARGET; $lnk.Arguments = $env:AR_ARGS;"
        "  $lnk.WorkingDirectory = $env:AR_WORKDIR; $lnk.IconLocation = $env:AR_ICON;"
        "  $lnk.Description = 'Auto Reschedule - lista de tarefas que acumula o que ficou para trás';"
        "  $lnk.Save(); Write-Output (Join-Path $d 'Auto Reschedule.lnk') }"
    )
    env = {
        **os.environ,
        "AR_TARGET": target,
        "AR_ARGS": arguments,
        "AR_WORKDIR": str(ROOT),
        "AR_ICON": icon,
        "AR_DIRS": "|".join(folders or []),
    }
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Não foi possível criar o atalho:", result.stderr.strip())
        return 1
    for line in result.stdout.splitlines():
        print("Atalho criado:", line)
    return 0


def main() -> int:
    _fix_console()
    parser = argparse.ArgumentParser(description="Auto Reschedule — lista de tarefas que acumula o que ficou para trás.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("AUTO_RESCHEDULE_PORT", DEFAULT_PORT)),
                        help=f"porta do servidor local (padrão: {DEFAULT_PORT})")
    parser.add_argument("--data", default=os.environ.get("AUTO_RESCHEDULE_DATA", str(DEFAULT_DATA)),
                        help="arquivo JSON onde os dados ficam salvos")
    parser.add_argument("--no-browser", action="store_true", help="não abre a janela automaticamente")
    parser.add_argument("--tab", action="store_true", help="abre como aba comum em vez de janela própria")
    parser.add_argument("--criar-atalho", action="store_true",
                        help="cria um atalho com o ícone do app na Área de Trabalho e no Menu Iniciar (Windows)")
    args = parser.parse_args()

    if args.criar_atalho:
        return create_shortcuts()

    url = f"http://127.0.0.1:{args.port}/"

    if already_running(args.port):
        print(f"O Auto Reschedule já está rodando em {url} — abrindo a janela.")
        if not args.no_browser:
            open_window(url, args.tab)
        return 0

    store = Store(args.data)
    try:
        server = create_server(store, args.port)
    except OSError as exc:
        print(f"Não foi possível usar a porta {args.port} ({exc}).")
        print("Tente outra porta, por exemplo:  python app.py --port 8800")
        return 1

    print(f"Auto Reschedule v{__version__} — por {__author__}")
    print(f"  Endereço : {url}")
    print(f"  Dados    : {Path(args.data).resolve()}")
    print("  Para encerrar: feche esta janela, pressione Ctrl+C ou use o menu '⋯ > Encerrar' no app.")

    if not args.no_browser:
        threading.Timer(0.4, open_window, args=(url, args.tab)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        print("Servidor encerrado. Até mais!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
