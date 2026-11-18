@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Agentes Gemma - Menu
set "PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo Falta el entorno virtual. Ejecuta INSTALAR.bat primero.
  pause
  exit /b 1
)
:menu
cls
echo ==========================================
echo       AGENTES GEMMA LOCAL - MENU
 echo ==========================================
echo  1. Demo: herramientas + RAG + traductor
 echo  2. Clima y multiplicaciones
 echo  3. Preguntar al RAG
 echo  4. Traducir texto
 echo  5. Memoria conversacional
 echo  6. Evaluar RAG en LangSmith (requiere API key)
 echo  7. Abrir .env para configurar LangSmith
 echo  8. Salir
 echo.
set /p "OP=Selecciona opcion [1-8]: "
if "%OP%"=="1" (
  "%PYTHON%" main.py demo
  goto fin
)
if "%OP%"=="2" goto herramientas
if "%OP%"=="3" goto rag
if "%OP%"=="4" goto traducir
if "%OP%"=="5" (
  "%PYTHON%" main.py memoria
  goto fin
)
if "%OP%"=="6" (
  "%PYTHON%" evaluar.py
  goto fin
)
if "%OP%"=="7" (
  notepad.exe ".env"
  goto menu
)
if "%OP%"=="8" exit /b 0
goto menu
:herramientas
set /p "PREG=Escribe la pregunta: "
"%PYTHON%" main.py herramientas --pregunta "%PREG%"
goto fin
:rag
set /p "PREG=Pregunta sobre politicas: "
"%PYTHON%" main.py rag --pregunta "%PREG%"
goto fin
:traducir
set /p "TEXTO=Texto: "
set /p "ORIGEN=Idioma origen (ej. espanol): "
set /p "DESTINO=Idioma destino (ej. ingles): "
"%PYTHON%" main.py traducir --texto "%TEXTO%" --origen "%ORIGEN%" --destino "%DESTINO%"
goto fin
:fin
echo.
pause
goto menu
