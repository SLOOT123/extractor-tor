# onion_comm.py — Extrae y verifica onions usando curl (soporte SOCKS5 nativo)
import socket
import re
import subprocess
import os
import concurrent.futures

# --- 1. Detección automática del proxy TOR ---
TOR_PROXY = None
for port in [9050, 9150]:
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1)
        s.close()
        TOR_PROXY = port
        print(f"[*] TOR detectado en el puerto {port}")
        break
    except Exception:
        pass

if not TOR_PROXY:
    print("[!] TOR no está corriendo. Abre TOR Browser e intenta de nuevo.")
    exit(1)

ONION_RE = re.compile(r"\b[a-z2-7]{56}\.onion\b", re.IGNORECASE)

SOURCES = [
    "http://tor.taxi/",
    "http://dark.fail/",
    "http://onionland.com/api/onions"
]

def harvest_onions() -> set:
    import requests
    try:
        import socks
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", TOR_PROXY)
        socket.socket = socks.socksocket
    except ImportError:
        pass
        
    requests.packages.urllib3.util.connection.HAS_IPV6 = False
    
    onions = set()
    for url in SOURCES:
        print(f"  [*] Consultando {url}...")
        try:
            r = requests.get(url, timeout=20)
            encontrados = ONION_RE.findall(r.text)
            if encontrados:
                print(f"      -> {len(encontrados)} encontrados")
                onions.update([o.lower() for o in encontrados])
        except Exception as e:
            print(f"      [!] Error: {e}")
    return onions

def check_onion_curl(onion: str) -> tuple:
    """Verifica un onion usando curl.exe."""
    url = f"http://{onion}"
    
    cmd = [
        "curl.exe", "-s", "-L", "-o", "NUL", 
        "-w", "%{http_code}", 
        "--socks5-hostname", f"127.0.0.1:{TOR_PROXY}",
        "--connect-timeout", "15", 
        "--max-time", "20", 
        url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25, creationflags=0x08000000)
        code = result.stdout.strip()
        
        # CORRECCIÓN AQUÍ: Convertir a entero para evitar error de comparación
        if code.isdigit():
            status_code = int(code)
            if status_code > 0 and status_code < 500:
                return (onion, status_code, "curl")
    except Exception:
        pass
    return (onion, 0, "")

def verify_onions_parallel(onions: set):
    live = []
    print(f"\n[*] Verificando {len(onions)} onions usando curl (esto puede tardar)...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(check_onion_curl, o): o for o in onions}
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res[1] > 0: # Ahora res[1] es un entero (int)
                live.append(res)
                print(f"[+] VIVO: {res[0]} (Code: {res[1]})")
                
    return live

if __name__ == "__main__":
    print("[*] Iniciando extracción desde red viva...")
    onions = harvest_onions()
    
    if not onions:
        print("[!] No se encontraron onions.")
        exit(1)
        
    live_onions = verify_onions_parallel(onions)
    
    with open("live_onions.txt", "w", encoding="utf-8") as f:
        for o in live_onions:
            f.write(f"{o[0]} | Status: {o[1]}\n")
            
    print(f"\n[+] Verificación completa. {len(live_onions)} onions vivos guardados en 'live_onions.txt'.")