#!/bin/bash
# run.sh — Lanzador para Linux y macOS

echo "============================================================"
echo "   EXTRACTOR TOR - Breadcrumb (Linux/macOS)"
echo "============================================================"

# 1. Verificar Python
if command -v python3 &> /dev/null; then
    PY=python3
elif command -v python &> /dev/null; then
    PY=python
else
    echo "[!] Python no encontrado. Instálalo: sudo apt install python3 (Linux) o brew install python (Mac)."
    exit 1
fi

# 2. Instalar dependencias de Python
echo "[*] Instalando dependencias de Python..."
$PY -m pip install --upgrade requests pysocks

# 3. Compilar binarios (si hay g++)
if command -v g++ &> /dev/null; then
    echo "[*] Compilando binarios C++..."
    # En Linux/Mac los binarios C++ se compilan distinto que en Windows
    g++ -std=c++20 -O2 -pthread worm_core.cpp -o worm_core 2>/dev/null
    g++ -std=c++20 -O2 tor_wrapper.cpp -o tor_wrapper 2>/dev/null
    echo "[+] Compilación finalizada."
else
    echo "[!] g++ no encontrado. El proyecto funcionará en modo Python."
fi

# 4. Buscar TOR Browser
echo "[*] Buscando TOR Browser..."
$PY -c "from tor_locator import find_tor_install; p=find_tor_install(); open('tor_path.txt','w').write(p or ''); print('[+] TOR: ' + (p or 'NO ENCONTRADO'))"

# 5. Lanzar la interfaz
echo "[*] Abriendo interfaz en http://localhost:8080"
$PY extractor_gui.py