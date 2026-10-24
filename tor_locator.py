# tor_locator.py — Multiplataforma (Windows, Linux, macOS)
import os
import sys
import platform

def find_tor_install():
    system = platform.system()
    paths = []
    
    if system == "Windows":
        paths = [
            os.path.expandvars(r"%USERPROFILE%\Desktop\Tor Browser"),
            os.path.expandvars(r"%USERPROFILE%\Downloads\Tor Browser"),
            os.path.expandvars(r"%LOCALAPPDATA%\Tor Browser"),
            r"C:\Program Files\Tor Browser",
        ]
    elif system == "Linux":
        # Rutas típicas en Linux
        paths = [
            os.path.expanduser("~/tor-browser"),
            os.path.expanduser("~/Desktop/tor-browser"),
            "/opt/tor-browser",
            "/usr/bin/tor-browser",
        ]
    elif system == "Darwin": # macOS
        paths = [
            os.path.expanduser("~/Applications/Tor Browser.app"),
            "/Applications/Tor Browser.app",
        ]
    
    for p in paths:
        if os.path.exists(p):
            return p
            
    # Fallback: buscar el ejecutable en el PATH (si es un servicio en Linux/Mac)
    import shutil
    tor_exe = shutil.which("tor")
    if tor_exe:
        return tor_exe
        
    return None

if __name__ == "__main__":
    p = find_tor_install()
    print(p if p else "")