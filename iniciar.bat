@echo off
rem Auto Reschedule - inicia o app (Windows). Autor: Hasten-Coubath
rem Deixe esta janela aberta enquanto usa o app; fechar a janela encerra o servidor.
chcp 65001 >nul
cd /d "%~dp0"
title Auto Reschedule

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 app.py %*
) else (
    python app.py %*
)

if errorlevel 1 (
    echo.
    echo Algo deu errado. Verifique se o Python 3.9+ esta instalado: https://www.python.org/downloads/
    pause
)
