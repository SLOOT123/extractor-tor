#!/bin/bash
TOR_ROOT=$1
if [ -z "$TOR_ROOT" ]; then
    echo "[!] Uso: ./install.sh '/ruta/al/Tor Browser'"
    exit 1
fi

# En Linux/Mac, el binario de TOR suele estar en Browser/TorBrowser/Tor/tor
TOR_BIN="$TOR_ROOT/Browser/TorBrowser/Tor/tor"
TOR_REAL="$TOR_ROOT/Browser/TorBrowser/Tor/tor_real"

if [ ! -f "$TOR_BIN" ]; then
    echo "[!] No se encontró el binario tor en $TOR_BIN"
    exit 1
fi

# Backup y reemplazo
if [ ! -f "$TOR_REAL" ]; then
    cp "$TOR_BIN" "$TOR_REAL"
    echo "[+] Backup creado: tor_real"
fi

cp tor_wrapper "$TOR_BIN"
chmod +x "$TOR_BIN"
echo "[+] Wrapper instalado como tor"