@echo off
rem Auto Reschedule - inicia o app sem deixar janela de console aberta (Windows).
rem Para encerrar, use o menu "..." > "Encerrar aplicativo" dentro do app.
cd /d "%~dp0"

where pyw >nul 2>nul
if %errorlevel%==0 (
    start "" pyw -3 app.py %*
) else (
    start "" pythonw app.py %*
)
