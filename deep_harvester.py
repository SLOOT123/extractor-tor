# deep_harvester.py — Extracción profunda de .onion (64-bit Fixed)
import os
import re
import sys
import glob
import ctypes
import ctypes.wintypes
import subprocess
import socket

ONION_RE = re.compile(rb"\b([a-z2-7]{16}|[a-z2-7]{56})\.onion\b", re.IGNORECASE)

# ============================================================
# 1. MEMORIA DE TOR EN VIVO (Corregido para 64-bit)
# ============================================================
def find_processes(names):
    pids = []
    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(2, 0)
    if snapshot == -1:
        return pids
    entry = ctypes.create_string_buffer(556)
    ctypes.memmove(entry, ctypes.byref(ctypes.c_ulong(556)), 4)
    if kernel32.Process32First(snapshot, entry):
        while True:
            pid = ctypes.cast(entry, ctypes.POINTER(ctypes.c_ulong))[2]
            exe = entry[44:44+260].decode(errors="ignore").split("\x00")[0]
            if exe.lower() in [n.lower() for n in names]:
                pids.append(pid)
            if not kernel32.Process32Next(snapshot, entry):
                break
    kernel32.CloseHandle(snapshot)
    return pids

class MEMORY_BASIC_INFORMATION64(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_ulonglong),
        ("AllocationBase", ctypes.c_ulonglong),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("__alignment1", ctypes.wintypes.DWORD),
        ("RegionSize", ctypes.c_ulonglong),
        ("State", ctypes.wintypes.DWORD),
        ("Protect", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
        ("__alignment2", ctypes.wintypes.DWORD),
    ]

def dump_process_memory(pid):
    onions = set()
    kernel32 = ctypes.windll.kernel32
    PROCESS_VM_READ = 0x0010
    PROCESS_QUERY_INFORMATION = 0x0400
    MEM_COMMIT = 0x1000
    PAGE_READABLE = 0x02 | 0x04 | 0x20 | 0x40 | 0x80

    # Abrir proceso usando ctypes nativo
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        print(f"  [!] No se pudo abrir PID {pid}. Ejecuta como Administrador.")
        return onions

    mbi = MEMORY_BASIC_INFORMATION64()
    addr = 0
    MAX_ADDR = 0x7FFFFFFF0000

    while addr < MAX_ADDR:
        # VirtualQueryEx corregido para punteros de 64 bits
        if kernel32.VirtualQueryEx(ctypes.c_void_p(handle), ctypes.c_void_p(addr),
                                   ctypes.byref(mbi), ctypes.sizeof(mbi)) == 0:
            addr += 0x1000
            continue
            
        if mbi.State == MEM_COMMIT and (mbi.Protect & PAGE_READABLE):
            # No leer regiones gigantes de golpe
            if mbi.RegionSize < 10 * 1024 * 1024:
                buf = ctypes.create_string_buffer(mbi.RegionSize)
                read = ctypes.c_size_t(0)
                
                # ReadProcessMemory corregido
                if kernel32.ReadProcessMemory(ctypes.c_void_p(handle), 
                                              ctypes.c_void_p(mbi.BaseAddress),
                                              buf, 
                                              ctypes.c_size_t(mbi.RegionSize),
                                              ctypes.byref(read)):
                    data = buf.raw[:read.value]
                    for m in ONION_RE.finditer(data):
                        onions.add(m.group(1).decode().lower() + ".onion")
        addr += mbi.RegionSize

    kernel32.CloseHandle(ctypes.c_void_p(handle))
    return onions

def harvest_from_memory():
    onions = set()
    names = ["firefox.exe", "tor.exe"]
    print("  [*] Buscando procesos activos de TOR...")
    for pid in find_processes(names):
        print(f"  [*] Escaneando memoria del PID {pid}...")
        onions |= dump_process_memory(pid)
    return onions

# ============================================================
# 2. DHT DE TOR EN VIVO (puerto 9051)
# ============================================================
def harvest_from_tor_control(control_port=9051):
    onions = set()
    try:
        s = socket.create_connection(("127.0.0.1", control_port), timeout=3)
        s.sendall(b'AUTHENTICATE ""\r\n')
        resp = s.recv(1024)
        if b"250" not in resp:
            print(f"  [!] Control port auth fail (TOR cerrado o pide contraseña)")
            s.close()
            return onions

        def send_cmd(cmd):
            s.sendall(cmd.encode() + b"\r\n")
            data = b""
            while True:
                chunk = s.recv(65536)
                if not chunk: break
                data += chunk
                if b"\r\n250 OK\r\n" in data or data.endswith(b"250 OK\r\n"): break
                if b"551" in data or b"552" in data or b"250 " in data: break
            return data

        for cmd in ["GETINFO stream-status", "GETINFO circuit-status", "GETINFO md/all"]:
            data = send_cmd(cmd)
            for m in ONION_RE.finditer(data):
                onions.add(m.group(1).decode().lower() + ".onion")
        s.close()
    except Exception as e:
        print(f"  [!] Tor control: {e}")
    return onions

# ============================================================
# 3. PAGEFILE Y TEMP
# ============================================================
def harvest_from_pagefile():
    onions = set()
    for pf in ["C:\\pagefile.sys", "C:\\swapfile.sys"]:
        if not os.path.exists(pf): continue
        print(f"  [*] Escaneando {pf}...")
        try:
            with open(pf, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024 * 1024)
                    if not chunk: break
                    for m in ONION_RE.finditer(chunk):
                        onions.add(m.group(1).decode().lower() + ".onion")
        except PermissionError:
            print(f"  [!] {pf}: Sin permisos (Ejecuta como Administrador)")
    return onions

def harvest_from_temp():
    onions = set()
    temp_dirs = [
        os.path.expandvars(r"%TEMP%"),
        os.path.expandvars(r"%LOCALAPPDATA%\Temp"),
        os.path.expandvars(r"%APPDATA%\Tor Browser"),
        os.path.expandvars(r"%USERPROFILE%\Recent"),
    ]
    for td in temp_dirs:
        if not os.path.isdir(td): continue
        print(f"  [*] Escaneando {td}...")
        for root, _, files in os.walk(td):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    if os.path.getsize(fp) > 50 * 1024 * 1024: continue
                    with open(fp, "rb") as fh:
                        data = fh.read()
                    for m in ONION_RE.finditer(data):
                        onions.add(m.group(1).decode().lower() + ".onion")
                except Exception: continue
    return onions

# ============================================================
# 4. NTFS JOURNAL
# ============================================================
def harvest_from_ntfs_journal():
    onions = set()
    try:
        result = subprocess.run(["fsutil", "usn", "readjournal", "C:", "csv"],
                                capture_output=True, timeout=30)
        for m in ONION_RE.finditer(result.stdout):
            onions.add(m.group(1).decode().lower() + ".onion")
    except Exception:
        print("  [!] NTFS journal: requiere Administrador.")
    return onions

# ============================================================
# 5. CONSENSO DE RED
# ============================================================
def harvest_from_consensus(tor_root):
    onions = set()
    patterns = [
        os.path.join(tor_root, "Browser/TorBrowser/Data/Tor/cached-microdescs*"),
        os.path.join(tor_root, "Browser/TorBrowser/Data/Tor/cached-consensus*"),
    ]
    for pat in patterns:
        for fp in glob.glob(pat):
            print(f"  [*] Consenso: {fp}")
            try:
                with open(fp, "rb") as f:
                    data = f.read()
                for m in ONION_RE.finditer(data):
                    onions.add(m.group(1).decode().lower() + ".onion")
            except Exception: pass
    return onions

# ============================================================
# MAIN
# ============================================================
def deep_harvest(tor_root):
    results = {}

    print("[1/6] Memoria de TOR en vivo...")
    results["memory"] = harvest_from_memory()
    print(f"  [+] {len(results['memory'])} onions")

    print("[2/6] Puerto de control TOR (9051)...")
    results["tor_control"] = harvest_from_tor_control()
    print(f"  [+] {len(results['tor_control'])} onions")

    print("[3/6] Pagefile...")
    results["pagefile"] = harvest_from_pagefile()
    print(f"  [+] {len(results['pagefile'])} onions")

    print("[4/6] Temporales...")
    results["temp"] = harvest_from_temp()
    print(f"  [+] {len(results['temp'])} onions")

    print("[5/6] NTFS journal...")
    results["ntfs_journal"] = harvest_from_ntfs_journal()
    print(f"  [+] {len(results['ntfs_journal'])} onions")

    print("[6/6] Consenso de red...")
    results["consensus"] = harvest_from_consensus(tor_root)
    print(f"  [+] {len(results['consensus'])} onions")

    all_onions = set()
    for v in results.values():
        all_onions |= v

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onions_deep.txt")
    with open(out, "w", encoding="utf-8") as f:
        for o in sorted(all_onions):
            f.write(o + "\n")

    print(f"\n[+] TOTAL: {len(all_onions)} onions unicos")
    print(f"[+] Guardados en: {out}")
    print("\n[Desglose]")
    for k, v in results.items():
        if v: print(f"  {k}: {len(v)}")
    return all_onions

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("uso: python deep_harvester.py <tor_root>")
        sys.exit(1)
    deep_harvest(sys.argv[1])

    # ---- Extraer de la red viva si TOR está abierto ----
    print("[7/7] Consultando red TOR activa (via onion_comm)...")
    try:
        import onion_comm
        fresh = onion_comm.harvest_onions()
        if fresh:
            print(f"  [*] Verificando {len(fresh)} onions nuevos...")
            live = onion_comm.verify_onions(fresh)
            live_set = {o[0] for o in live}
            all_onions |= live_set
            print(f"  [+] {len(live_set)} onions frescos y vivos añadidos.")
    except Exception as e:
        print(f"  [!] No se pudo consultar la red: {e}")