# onion_harvester.py — Extrae .onion de los archivos estáticos de TOR
import os
import re
import sqlite3
import shutil
import tempfile

ONION_RE = re.compile(r"\b([a-z2-7]{16}|[a-z2-7]{56})\.onion\b", re.IGNORECASE)

def extract_from_file(path):
    onions = set()
    try:
        with open(path, "rb") as f:
            data = f.read()
        for m in ONION_RE.finditer(data):
            onions.add(m.group(1).lower() + ".onion")
        # Soporte para UTF-16 (prefs.js)
        try:
            text = data.decode("utf-16", errors="ignore")
            for m in ONION_RE.finditer(text):
                onions.add(m.group(1).lower() + ".onion")
        except Exception:
            pass
    except Exception:
        pass
    return onions

def extract_from_sqlite(path):
    onions = set()
    if not os.path.exists(path):
        return onions
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite")
    tmp.close()
    try:
        shutil.copy2(path, tmp.name)
        conn = sqlite3.connect(tmp.name)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in [r[0] for r in cur.fetchall()]:
            try:
                cur.execute(f"SELECT * FROM {table}")
                for row in cur.fetchall():
                    for val in row:
                        if isinstance(val, str):
                            for m in ONION_RE.finditer(val):
                                onions.add(m.group(1).lower() + ".onion")
            except Exception:
                continue
        conn.close()
    except Exception:
        pass
    finally:
        try: os.unlink(tmp.name)
        except: pass
    return onions

def harvest_all(tor_root):
    results = {"onions": set(), "sources": {}, "sqlite_files": []}
    
    key_files = [
        "Browser/TorBrowser/Data/Browser/profile.default/places.sqlite",
        "Browser/TorBrowser/Data/Browser/profile.default/prefs.js",
        "Browser/TorBrowser/Data/Browser/profile.default/bookmarkbackups",
        "Browser/TorBrowser/Data/Browser/profile.default/sessionstore-backups",
        "Browser/TorBrowser/Data/Browser/profile.default/cookies.sqlite",
        "Browser/TorBrowser/Data/Tor/cached-microdescs",
        "Browser/TorBrowser/Data/Tor/onion_auth",
        "Browser/TorBrowser/Data/Tor/hidden_service",
    ]

    for rel in key_files:
        full = os.path.join(tor_root, rel)
        if not os.path.exists(full): continue
        
        if os.path.isdir(full):
            for root, _, files in os.walk(full):
                for f in files:
                    fp = os.path.join(root, f)
                    found = extract_from_file(fp)
                    if found:
                        results["sources"][fp] = len(found)
                        results["onions"].update(found)
        elif full.endswith(".sqlite"):
            found = extract_from_sqlite(full)
            results["sqlite_files"].append(full)
            if found:
                results["sources"][full] = len(found)
                results["onions"].update(found)
        else:
            found = extract_from_file(full)
            if found:
                results["sources"][full] = len(found)
                results["onions"].update(found)

    # Barrido profundo
    for root, _, files in os.walk(tor_root):
        for f in files:
            fp = os.path.join(root, f)
            if fp in results["sources"]: continue
            if f.endswith((".sqlite", ".db", ".json", ".js", ".txt", ".log", ".onion")):
                found = extract_from_file(fp)
                if found:
                    results["sources"][fp] = len(found)
                    results["onions"].update(found)
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        r = harvest_all(sys.argv[1])
        print(f"[+] {len(r['onions'])} onions encontrados.")