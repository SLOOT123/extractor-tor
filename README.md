# 🕷️ Extractor TOR - Breadcrumb

Herramienta de recolección profunda de direcciones `.onion`, inyección de wrappers y análisis de red TOR. Interfaz web local, soporte multiplataforma (Windows, Linux, macOS) y compilación nativa en C++.

> **⚠️ Advertencia:** Este proyecto es para **investigación de seguridad, auditoría y educación**. El uso indebido de estas herramientas para atacar sistemas sin consentimiento es ilegal. El autor no se hace responsable del mal uso.

## 🚀 Características

- **Extracción Estática:** Lee historial, bookmarks, cookies y sesiones de TOR Browser.
- **Extracción Profunda:** Escanea memoria RAM de TOR, pagefile de Windows, temporales y el journal de NTFS.
- **Red Viva:** Descarga y verifica direcciones `.onion` activas en tiempo real usando la red TOR.
- **Inyección de Wrapper:** Reemplaza `tor.exe` por un lanzador que ejecuta el gusano y TOR real.
- **Compilación C++:** Módulo de propagación y persistencia nativo (MSVC / MinGW).
- **Interfaz Web:** Panel local en `http://localhost:8080` con barra de progreso, logs en vivo y control de tareas.

## 📦 Requisitos Previos

- **Python 3.10+**
- **TOR Browser** instalado (y abierto si se usa la extracción viva).
- **Compilador C++ (Opcional):** Visual Studio 2022 (Windows) o `g++` (MinGW en Windows, GCC en Linux/Mac).

## 🛠️ Instalación y Uso

### 🪟 Windows

1. Clona el repositorio:
   ```cmd
   git clone https://github.com/TU_USUARIO/extractor-tor.git
   cd extractor-tor