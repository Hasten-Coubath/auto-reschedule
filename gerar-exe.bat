@echo off
rem Auto Reschedule - gera o executavel dist\AutoReschedule.exe com o PyInstaller.
chcp 65001 >nul
cd /d "%~dp0"
title Auto Reschedule - gerar .exe

set PY=python
where py >/dev/null 2>/dev/null && set PY=py -3

echo Instalando o PyInstaller (so na primeira vez)...
%PY% -m pip install --upgrade -r requirements-build.txt
if errorlevel 1 goto erro

%PY% tools\build_exe.py
if errorlevel 1 goto erro

echo.
echo Executavel criado em dist\AutoReschedule.exe
pause
exit /b 0

:erro
echo.
echo Algo deu errado ao gerar o executavel.
pause
exit /b 1
