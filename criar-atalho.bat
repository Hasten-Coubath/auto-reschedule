@echo off
rem Auto Reschedule - cria atalhos com o icone do app na Area de Trabalho e no Menu Iniciar.
chcp 65001 >nul
cd /d "%~dp0"

where py >/dev/null 2>nul
if %errorlevel%==0 (
    py -3 app.py --criar-atalho
) else (
    python app.py --criar-atalho
)
pause
