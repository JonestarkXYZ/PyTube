# PyTube

Aplicación de escritorio en Python para descargar videos y audios de YouTube usando `yt-dlp` y una interfaz gráfica hecha con PyQt5.

## Características

- Descarga videos de YouTube en formato `mp4`, `mkv` o `webm`.
- Extrae audio en formato `mp3`, `m4a`, `wav` o `aac`.
- Permite descargar playlists completas.
- Guarda una carpeta de descarga por defecto en `config.json`.
- Valida URLs para evitar rutas locales `file://` y enlaces que no sean de YouTube.
- Muestra el progreso de descarga en la interfaz.
- Marca visualmente cada descarga:
  - Gris: descarga en progreso.
  - Verde: descarga completada.
  - Rojo: error de descarga.
- Permite abrir el archivo descargado desde la interfaz.

## Requisitos

- Python 3.11 o superior.
- Entorno virtual de Python.
- `ffmpeg` instalado en el sistema para fusionar video/audio o convertir audio.
- En Linux, una aplicación predeterminada configurada para abrir archivos multimedia.
- En Windows, `ffmpeg` debe estar disponible en el `PATH`.

En Debian, Ubuntu o derivados:

```bash
sudo apt update
sudo apt install python3 python3-venv ffmpeg
```

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/TU_USUARIO/PyTube.git
cd PyTube
```

Crea el entorno virtual:

```bash
python3 -m venv myenv
```

Activa el entorno virtual:

```bash
source myenv/bin/activate
```

En Windows:

```powershell
python -m venv myenv
.\myenv\Scripts\Activate.ps1
```

Instala las dependencias:

```bash
pip install -r requirements.txt
```

También puedes usar el script incluido:

```bash
chmod +x install_deps.sh
./install_deps.sh
```

## Uso

Ejecuta la aplicación:

```bash
./myenv/bin/python src/main.py
```

En Windows:

```powershell
.\myenv\Scripts\python.exe src\main.py
```

Flujo básico:

1. Selecciona la carpeta de descarga con el botón `Guardar en...`.
2. Pega una URL de YouTube.
3. Elige `Audio` o `Video`.
4. Selecciona el formato de salida.
5. Presiona `Descargar`.
6. Cuando termine, usa el botón de abrir para ejecutar el archivo descargado con la aplicación predeterminada del sistema.

## Configuración

La aplicación guarda la carpeta de descarga en:

```text
config.json
```

Ese archivo no debe subirse al repositorio porque contiene una ruta local de la PC del usuario. Por eso está incluido en `.gitignore`.

Si la carpeta guardada no existe o fue borrada, la aplicación pedirá seleccionar una nueva carpeta desde el explorador de archivos.

## Estructura del proyecto

```text
PyTube/
├── src/
│   ├── main.py            # Punto de entrada de la aplicación
│   ├── gui.py             # Interfaz gráfica y descarga en segundo plano
│   ├── platform_utils.py  # Detección Windows/Linux, rutas y apertura de archivos
│   └── download.py        # Funciones auxiliares para descargas con yt-dlp
├── install_deps.sh   # Script para crear/usar el entorno virtual e instalar dependencias
├── requirements.txt  # Dependencias de Python
├── .gitignore
└── README.md
```

## Notas sobre YouTube y yt-dlp

YouTube cambia con frecuencia sus métodos de entrega de video. Si aparece un error de extracción, firma, `nsig`, SABR o formatos no disponibles, primero actualiza `yt-dlp`:

```bash
./myenv/bin/python -m pip install --upgrade "yt-dlp[default]"
```

Si aparece una advertencia como:

```text
No supported JavaScript runtime could be found
```

instala un runtime JavaScript como `deno` o `nodejs`. La descarga puede funcionar sin eso, pero algunos videos pueden requerirlo.

## Limitaciones actuales

- El botón de cancelar descarga todavía no está implementado.
- Las playlists se guardan en una carpeta llamada `playlist_descargada`.
- La interfaz no muestra todavía velocidad, tamaño descargado ni tiempo restante.

## Licencia y uso responsable

Esta es una aplicación libre de uso, creada como herramienta para uso personal y no profesional.

El usuario es responsable del uso que le dé a la aplicación. No nos hacemos responsables por usos delicados, indebidos o ilegales, incluyendo robo de contenido, descarga no autorizada, redistribución de material protegido por derechos de autor o cualquier uso que incumpla leyes, términos de servicio de plataformas externas o derechos de terceros.

Antes de descargar contenido, verifica que tienes permiso para hacerlo y que el uso cumple con la normativa aplicable.
