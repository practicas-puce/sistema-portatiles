@echo off
title Sistema de Gestion LTIC - Prestamos
color 0a

echo ===================================================
echo     INICIANDO SISTEMA DE GESTION LTIC PRESTAMOS
echo ===================================================
echo.

:: Verificar si existe entorno virtual y activarlo
if exist venv\Scripts\activate.bat (
    echo [*] Activando entorno virtual (venv)...
    call venv\Scripts\activate.bat
) else if exist .venv\Scripts\activate.bat (
    echo [*] Activando entorno virtual (.venv)...
    call .venv\Scripts\activate.bat
)

echo [*] Iniciando servidor web de Flask...
echo.

:: Esperar 3 segundos antes de abrir el navegador en la URL local
start /b cmd /c "timeout /t 3 >nul && start http://localhost:5000"

:: Ejecutar el servidor Python
python app.py

pause
