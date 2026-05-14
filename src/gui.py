from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QFileDialog, QHBoxLayout, QVBoxLayout, QFrame, QScrollArea,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
import os
import yt_dlp
from urllib.parse import urlparse, parse_qs

from platform_utils import (
    abrir_archivo_sistema,
    cargar_directorio_guardado,
    guardar_directorio_config,
    nombre_sistema,
)

# Variables globales
url_original = ""
modo_descarga = "video"
formato_salida = "mp4"
descargar_lista = False
directorio_guardado = ""

class DownloadThread(QThread):
    progreso = pyqtSignal(str, int)  # nombre, porcentaje
    finalizado = pyqtSignal(str, str)  # nombre, ruta
    error = pyqtSignal(str)  # mensaje de error para mostrar en la interfaz

    def __init__(self, url, modo, formato, es_lista, carpeta):
        super().__init__()
        self.url = url
        self.modo = modo
        self.formato = formato
        self.es_lista = es_lista
        self.carpeta = carpeta
        self.detener = False

    def normalizar_url_youtube(self):
        """Valida la URL y devuelve una URL segura compatible con yt-dlp."""
        url = self.url.strip()
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        # yt-dlp bloquea file:// por seguridad; la aplicación solo debe aceptar YouTube.
        if parsed.scheme == "file":
            raise ValueError("La URL ingresada es una ruta local file://. Pega una URL de YouTube.")

        if parsed.scheme not in ("http", "https"):
            raise ValueError("La URL debe comenzar con http:// o https://.")

        dominios_validos = ("youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be")
        if host not in dominios_validos:
            raise ValueError("Solo se aceptan enlaces de YouTube o youtu.be.")

        query = parse_qs(parsed.query)

        # En modo lista se conserva la URL completa para que yt-dlp procese la playlist.
        if self.es_lista:
            if "list" not in query:
                raise ValueError("Marcaste lista completa, pero la URL no contiene una playlist.")
            return url

        # En enlaces cortos youtu.be, el ID viene en la ruta.
        if host == "youtu.be":
            video_id = parsed.path.strip("/")
        else:
            video_id = query.get("v", [""])[0]

        if not video_id:
            raise ValueError("No se pudo encontrar el ID del video en la URL.")

        return f"https://www.youtube.com/watch?v={video_id}"

    def formato_video_yt_dlp(self):
        """Devuelve una selección de formato flexible según el contenedor elegido."""
        if self.formato == "mp4":
            return "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/best"

        if self.formato == "webm":
            return "bv*[ext=webm]+ba[ext=webm]/bv*+ba/best"

        return "bv*+ba/best"

    def resolver_archivo_final(self, ruta_original):
        """Busca el archivo final real cuando FFmpeg cambia nombre o extensión."""
        if not ruta_original:
            return ""

        if os.path.isfile(ruta_original):
            return ruta_original

        base, _ = os.path.splitext(ruta_original)
        ruta_formato = f"{base}.{self.formato}"
        if os.path.isfile(ruta_formato):
            return ruta_formato

        carpeta = os.path.dirname(ruta_original)
        nombre_base = os.path.basename(base)
        if not os.path.isdir(carpeta):
            return ""

        # Se toma el archivo más reciente que coincide con el título base.
        candidatos = []
        for nombre in os.listdir(carpeta):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta) and os.path.splitext(nombre)[0] == nombre_base:
                candidatos.append(ruta)

        if candidatos:
            return max(candidatos, key=os.path.getmtime)

        return ""

    def run(self):
        ultimo_archivo = ""

        def hook(d):
            nonlocal ultimo_archivo

            if d["status"] == "downloading":
                percent = d.get("_percent_str", "0.0%").replace("%", "").strip()
                nombre = os.path.basename(d.get("filename", "Descargando..."))
                try:
                    porcentaje = int(float(percent))
                except ValueError:
                    porcentaje = 0
                self.progreso.emit(nombre, porcentaje)
            elif d["status"] == "finished":
                # Se guarda la ruta reportada por yt-dlp para habilitar el botón de abrir al final.
                ultimo_archivo = d.get("filename") or d.get("filepath", "")

        if self.es_lista:
            nombre_carpeta = "playlist_descargada"
            ruta_carpeta = os.path.join(self.carpeta, nombre_carpeta)
            os.makedirs(ruta_carpeta, exist_ok=True)
        else:
            ruta_carpeta = self.carpeta

        try:
            url = self.normalizar_url_youtube()
            output_template = os.path.join(ruta_carpeta, "%(title)s.%(ext)s")

            if self.modo == "audio":
                opts = {
                    "format": "bestaudio/best",
                    "outtmpl": output_template,
                    "progress_hooks": [hook],
                    "quiet": True,
                    "no_color": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": self.formato,
                        "preferredquality": "192",
                    }],
                }
            else:
                opts = {
                    # Selección flexible: evita fallos cuando YouTube no ofrece MP4 exacto.
                    "format": self.formato_video_yt_dlp(),
                    "outtmpl": output_template,
                    "progress_hooks": [hook],
                    "quiet": True,
                    "no_color": True,
                    "merge_output_format": self.formato,
                }

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            # FFmpeg puede cambiar la extensión final al extraer audio o fusionar video.
            ultimo_archivo = self.resolver_archivo_final(ultimo_archivo)

            nombre_final = os.path.basename(ultimo_archivo) if ultimo_archivo else "Descarga completada"
            self.finalizado.emit(nombre_final, ultimo_archivo)
        except Exception as e:
            print(f"\n[ERROR] No se pudo descargar: {e}")
            self.error.emit(str(e))

class DownloaderUI(QWidget):
    count = 0
    def __init__(self):
        super().__init__()
        # El título muestra el sistema detectado para confirmar la ruta usada.
        self.setWindowTitle(f"YouTube Downloader - {nombre_sistema()}")
        self.setMinimumSize(700, 500)
        self.thread = None
        self.directorio_guardado = cargar_directorio_guardado()
        self.init_ui()
        QTimer.singleShot(0, self.verificar_directorio_inicial)

    def guardar_directorio_config(self, ruta):
        """Guarda la carpeta elegida para reutilizarla al abrir la app."""
        guardar_directorio_config(ruta)

    def seleccionar_directorio_obligatorio(self, mensaje):
        """Pide una carpeta por explorador y devuelve True solo si la ruta existe."""
        QMessageBox.warning(self, "Carpeta requerida", mensaje)
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de descarga")

        if not path:
            return False

        if not os.path.isdir(path):
            QMessageBox.warning(self, "Error", "La carpeta seleccionada no existe.")
            return False

        self.actualizar_directorio_guardado(path)
        return True

    def verificar_directorio_inicial(self):
        """Al abrir, informa la carpeta por defecto y corrige rutas borradas."""
        if not os.path.isdir(self.directorio_guardado):
            self.seleccionar_directorio_obligatorio(
                "La carpeta de descarga guardada no existe. Selecciona una carpeta válida."
            )
            return

        QMessageBox.information(
            self,
            "Carpeta por defecto",
            f"Los videos y audios se descargarán por defecto en:\n{self.directorio_guardado}"
        )
        self.guardar_directorio_config(self.directorio_guardado)

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        top_bar = QHBoxLayout()
        self.save_dir_button = QPushButton("Guardar en...")
        self.save_dir_button.clicked.connect(self.select_directory)
        top_bar.addWidget(self.save_dir_button)
        self.save_dir_label = QLabel(f"Carpeta por defecto: {self.directorio_guardado}")
        self.save_dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        top_bar.addWidget(self.save_dir_label)
        top_bar.addStretch()
        self.layout.addLayout(top_bar)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(separator)

        url_layout = QHBoxLayout()
        url_label = QLabel("Pegar URL aquí →")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        self.layout.addLayout(url_layout)

        options_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Audio", "Video"])
        self.format_combo.currentIndexChanged.connect(self.update_tipo_combo)
        self.tipo_combo = QComboBox()
        self.update_tipo_combo()
        self.toggle_lista = QCheckBox("Descargar lista completa")
        options_layout.addWidget(QLabel("Formato:"))
        options_layout.addWidget(self.format_combo)
        options_layout.addWidget(QLabel("Tipo:"))
        options_layout.addWidget(self.tipo_combo)
        options_layout.addWidget(self.toggle_lista)
        self.layout.addLayout(options_layout)

        self.download_button = QPushButton("Descargar")
        self.download_button.clicked.connect(self.descargar)
        self.layout.addWidget(self.download_button, alignment=Qt.AlignRight)

        # Área de descargas en scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.downloads_widget = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_widget)
        self.downloads_layout.setAlignment(Qt.AlignTop)
        self.scroll_area.setWidget(self.downloads_widget)
        self.layout.addWidget(self.scroll_area)

    def select_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta")
        if path:
            self.actualizar_directorio_guardado(path)

    def actualizar_directorio_guardado(self, path):
        """Actualiza la ruta en memoria, en la etiqueta y en config.json."""
        global directorio_guardado
        directorio_guardado = path
        self.directorio_guardado = path
        self.save_dir_label.setText(f"Carpeta por defecto: {path}")
        self.guardar_directorio_config(path)

    def update_tipo_combo(self):
        tipo = self.format_combo.currentText().lower()
        self.tipo_combo.clear()
        if tipo == "audio":
            self.tipo_combo.addItems(["mp3", "m4a", "wav", "aac"])
        else:
            self.tipo_combo.addItems(["mp4", "mkv", "webm"])

    def descargar(self):
        global url_original, modo_descarga, formato_salida, descargar_lista
        url_original = self.url_input.text().strip()
        if not url_original:
            QMessageBox.warning(self, "Error", "Debes ingresar una URL")
            return

        if not os.path.isdir(self.directorio_guardado):
            seleccionado = self.seleccionar_directorio_obligatorio(
                "La carpeta de descarga no existe o fue borrada. Selecciona una carpeta válida."
            )
            if not seleccionado:
                return

        self.download_button.setEnabled(False)
        self.url_input.clear()
        modo_descarga = self.format_combo.currentText().lower()
        formato_salida = self.tipo_combo.currentText()
        descargar_lista = self.toggle_lista.isChecked()

        # Crear item de descarga
        container = QWidget()
        container.setObjectName("downloadItem")
        layout = QHBoxLayout(container)
        title_label = QLabel("Descargando...")
        title_label.setMinimumWidth(220)
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        open_btn = QPushButton("Abrir")
        open_btn.setEnabled(False)
        layout.addWidget(title_label)
        layout.addWidget(progress_bar)
        layout.addWidget(open_btn)
        self.downloads_layout.addWidget(container)
        self.aplicar_estado_descarga(container, title_label, progress_bar, "descargando")

        # Crear y conectar hilo de descarga
        self.thread = DownloadThread(url_original, modo_descarga, formato_salida, descargar_lista, self.directorio_guardado)
        self.thread.progreso.connect(lambda nombre, p: self.on_progreso(title_label, progress_bar, nombre, p))
        self.thread.finalizado.connect(lambda nombre, path: self.on_descarga_finalizada(container, title_label, open_btn, progress_bar, nombre, path))
        self.thread.error.connect(lambda mensaje: self.on_descarga_error(container, title_label, open_btn, progress_bar, mensaje))
        self.thread.start()

        #si el hilo se terminó es porque terminó la descarga

    def on_progreso(self, label, progress_bar, nombre, porcentaje):
        """Actualiza el nombre visible y el porcentaje de la descarga activa."""
        label.setText(nombre)
        progress_bar.setValue(porcentaje)

    def aplicar_estado_descarga(self, container, label, progress_bar, estado):
        """Aplica colores de estado a la fila y a la barra de progreso."""
        estilos = {
            "descargando": {
                "borde": "#4b5563",
                "fondo": "#e5e7eb",
                "texto": "#1f2937",
                "barra": "#64748b",
            },
            "ok": {
                "borde": "#22c55e",
                "fondo": "#ecfdf5",
                "texto": "#15803d",
                "barra": "#22c55e",
            },
            "error": {
                "borde": "#ef4444",
                "fondo": "#fef2f2",
                "texto": "#b91c1c",
                "barra": "#ef4444",
            },
        }
        color = estilos[estado]

        container.setStyleSheet(
            f"QWidget#downloadItem {{"
            f"background-color: {color['fondo']};"
            f"border: 1px solid {color['borde']};"
            f"border-radius: 6px;"
            f"}}"
        )
        label.setStyleSheet(f"color: {color['texto']}; font-weight: 600;")
        progress_bar.setStyleSheet(
            "QProgressBar {"
            "border: 1px solid #cbd5e1;"
            "border-radius: 5px;"
            "height: 16px;"
            "text-align: center;"
            "background-color: #d1d5db;"
            "}"
            f"QProgressBar::chunk {{ background-color: {color['barra']}; border-radius: 4px; }}"
        )

    def abrir_archivo_descargado(self, ruta):
        """Abre el archivo descargado con la aplicación predeterminada del sistema."""
        if not ruta or not os.path.isfile(ruta):
            QMessageBox.warning(self, "Archivo no encontrado", "No se encontró el archivo descargado.")
            return

        abierto = abrir_archivo_sistema(ruta)
        if not abierto:
            QMessageBox.warning(self, "Error", "No se pudo abrir el archivo con la aplicación predeterminada.")

    def on_descarga_finalizada(self, container, label, button, progress_bar, nombre, ruta):
        """Marca una descarga como terminada y habilita el botón para abrir el archivo."""
        label.setText(nombre)
        progress_bar.setValue(100)
        self.aplicar_estado_descarga(container, label, progress_bar, "ok")
        button.setEnabled(bool(ruta))
        button.setText("▶")
        button.clicked.connect(lambda: self.abrir_archivo_descargado(ruta))
        self.download_button.setEnabled(True)
        print(f"Descarga finalizada: {self.count}\n")
        self.count += 1
        # No es la finaliza la descarga sino que termina de descargar el archivo poco a poco
        # os.path.basename(ruta) no funciona

    def on_descarga_error(self, container, label, button, progress_bar, mensaje):
        """Muestra errores de yt-dlp sin dejar bloqueado el botón principal."""
        label.setText("Error en la descarga")
        progress_bar.setValue(0)
        self.aplicar_estado_descarga(container, label, progress_bar, "error")
        button.setEnabled(False)
        self.download_button.setEnabled(True)
        QMessageBox.critical(self, "Error de descarga", mensaje)
