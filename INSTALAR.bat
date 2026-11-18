@echo off
setlocal
cd /d "%~dp0"
title Instalacion automatica - Agentes Gemma
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\instalar.ps1"
set "EXITCODE=%ERRORLEVEL%"
echo.
if not "%EXITCODE%"=="0" (
  echo La instalacion no se completo. Revisa los mensajes anteriores.
) else (
  echo Instalacion terminada. Ahora ejecuta INICIAR.bat.
)
pause
exit /b %EXITCODE%
