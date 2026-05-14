"""Utilidades específicas del sistema operativo para PyTube."""

import json
import os
import platform
import shutil
import subprocess
from pathlib import Path

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices


# Carpeta raíz del proyecto y archivo local de configuración.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"


def nombre_sistema():
    """Devuelve el nombre normalizado del sistema operativo actual."""
    return platform.system().lower()


def es_windows():
    """Indica si la aplicación se está ejecutando en Windows."""
    return nombre_sistema() == "windows"


def es_linux():
    """Indica si la aplicación se está ejecutando en Linux."""
    return nombre_sistema() == "linux"


def hay_sesion_grafica():
    """Detecta si Linux tiene una sesión gráfica disponible para PyQt."""
    if not es_linux():
        return True

    display = os.environ.get("DISPLAY")
    wayland_display = os.environ.get("WAYLAND_DISPLAY")

    # xset confirma si X11 acepta conexiones; evita que Qt aborte por DISPLAY inválido.
    if display and shutil.which("xset"):
        resultado = subprocess.run(
            ["xset", "q"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if resultado.returncode == 0:
            return True

    if wayland_display:
        runtime_dir = os.environ.get("XDG_RUNTIME_DIR", "")
        socket_wayland = Path(runtime_dir) / wayland_display if runtime_dir else None
        return bool(socket_wayland and socket_wayland.exists())

    # En Linux de consola pura PyQt no puede abrir ventanas sin DISPLAY o Wayland.
    return False


def clave_directorio_sistema():
    """Devuelve la clave de config.json correspondiente al sistema actual."""
    if es_windows():
        return "directorio_guardado_windows"

    if es_linux():
        return "directorio_guardado_linux"

    return f"directorio_guardado_{nombre_sistema() or 'otro'}"


def carpeta_descargas_sistema():
    """Devuelve una carpeta de descargas probable según Windows o Linux."""
    home = Path.home()

    if es_windows():
        posibles_rutas = [
            Path(os.environ.get("USERPROFILE", str(home))) / "Downloads",
            home / "Downloads",
        ]
    else:
        xdg_download = os.environ.get("XDG_DOWNLOAD_DIR")
        posibles_rutas = [
            Path(xdg_download).expanduser() if xdg_download else None,
            home / "Descargas",
            home / "Downloads",
        ]

    # Se elige la primera ruta existente para evitar guardar carpetas inválidas.
    for ruta in posibles_rutas:
        if ruta and ruta.is_dir():
            return str(ruta)

    return str(home)


def cargar_configuracion():
    """Carga config.json y devuelve un diccionario válido aunque el archivo falle."""
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def cargar_directorio_guardado():
    """Carga la carpeta guardada para el sistema actual o usa una carpeta segura."""
    config = cargar_configuracion()
    clave_actual = clave_directorio_sistema()

    # Primero se respeta la ruta guardada para Windows o Linux.
    ruta = config.get(clave_actual, "")
    if ruta and Path(ruta).is_dir():
        return ruta

    # Compatibilidad con configuraciones antiguas que usaban una sola clave.
    ruta_legacy = config.get("directorio_guardado", "")
    if ruta_legacy and Path(ruta_legacy).is_dir():
        return ruta_legacy

    return carpeta_descargas_sistema()


def guardar_directorio_config(ruta):
    """Guarda la carpeta de descarga separada por sistema operativo."""
    config = cargar_configuracion()
    clave_actual = clave_directorio_sistema()

    # Se conserva la clave antigua para compatibilidad con versiones previas.
    config[clave_actual] = ruta
    config["directorio_guardado"] = ruta
    config["sistema_ultima_ejecucion"] = nombre_sistema()

    with CONFIG_FILE.open("w", encoding="utf-8") as archivo:
        json.dump(config, archivo, indent=2, ensure_ascii=False)


def abrir_archivo_sistema(ruta):
    """Abre un archivo con la aplicación predeterminada de Windows o Linux."""
    archivo = Path(ruta).expanduser().resolve()
    if not archivo.is_file():
        return False

    if es_windows():
        try:
            # os.startfile usa la asociación predeterminada registrada en Windows.
            os.startfile(str(archivo))  # type: ignore[attr-defined]
            return True
        except OSError:
            return False

    # En Linux y otros sistemas Qt delega en el entorno gráfico disponible.
    return QDesktopServices.openUrl(QUrl.fromLocalFile(str(archivo)))
