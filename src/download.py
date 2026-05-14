# download.py

import os
import yt_dlp
from urllib.parse import urlparse, parse_qs

def limpiar_url_youtube(url):
    """Valida y normaliza una URL individual de YouTube."""
    url = url.strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    # No se permiten rutas locales porque yt-dlp bloquea file:// por seguridad.
    if parsed.scheme == "file":
        raise ValueError("La URL ingresada es una ruta local file://. Pega una URL de YouTube.")

    if parsed.scheme not in ("http", "https"):
        raise ValueError("La URL debe comenzar con http:// o https://.")

    dominios_validos = ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be")
    if host not in dominios_validos:
        raise ValueError("Solo se aceptan enlaces de YouTube o youtu.be.")

    query = parse_qs(parsed.query)

    # En enlaces cortos youtu.be, el ID del video está en la ruta.
    if host == "youtu.be":
        video_id = parsed.path.strip("/")
    else:
        video_id = query.get("v", [""])[0]

    if not video_id:
        raise ValueError("No se pudo extraer el ID del video.")

    return f"https://www.youtube.com/watch?v={video_id}"

def validar_url_playlist(url):
    """Valida una URL de YouTube que debe contener una playlist."""
    url = url.strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if parsed.scheme == "file":
        raise ValueError("La URL ingresada es una ruta local file://. Pega una URL de YouTube.")

    if parsed.scheme not in ("http", "https"):
        raise ValueError("La URL debe comenzar con http:// o https://.")

    dominios_validos = ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com")
    if host not in dominios_validos:
        raise ValueError("Solo se aceptan playlists de YouTube.")

    query = parse_qs(parsed.query)
    if "list" not in query:
        raise ValueError("Marcaste lista completa, pero la URL no contiene una playlist.")

    return url

def formato_video_yt_dlp(formato_salida):
    """Devuelve una selección flexible para evitar errores por formatos exactos no disponibles."""
    if formato_salida == "mp4":
        return "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/best"

    if formato_salida == "webm":
        return "bv*[ext=webm]+ba[ext=webm]/bv*+ba/best"

    return "bv*+ba/best"

def descargar_con_yt_dlp(url_original, modo_descarga, formato_salida, descargar_lista, directorio_guardado):
    """
    Descarga un video o audio desde YouTube usando yt-dlp.
    
    Parámetros:
    - url_original: str
    - modo_descarga: "audio" o "video"
    - formato_salida: "mp3", "mp4", etc.
    - descargar_lista: bool
    - directorio_guardado: str (ruta absoluta del directorio de destino)
    """

    if descargar_lista:
        url = validar_url_playlist(url_original)
        nombre_carpeta = "playlist_descargada"
        ruta_carpeta = os.path.join(directorio_guardado, nombre_carpeta)
        os.makedirs(ruta_carpeta, exist_ok=True)
    else:
        url = limpiar_url_youtube(url_original)
        ruta_carpeta = directorio_guardado

    output_template = os.path.join(ruta_carpeta, "%(title)s.%(ext)s")

    if modo_descarga == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'quiet': False,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': formato_salida,
                'preferredquality': '192',
            }],
        }
    elif modo_descarga == "video":
        ydl_opts = {
            'format': formato_video_yt_dlp(formato_salida),
            'outtmpl': output_template,
            'quiet': False,
            'merge_output_format': formato_salida,
        }
    else:
        raise ValueError("Modo de descarga inválido. Usa 'audio' o 'video'.")

    # Ejecutar la descarga
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[INFO] Descargando desde: {url}")
            ydl.download([url])
            print("✅ Descarga completada.")
    except Exception as e:
        print(f"[ERROR] Error en la descarga: {e}")
        raise
