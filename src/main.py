# main.py
import sys
from PyQt5.QtWidgets import QApplication
from gui import DownloaderUI
from platform_utils import es_linux, hay_sesion_grafica

if __name__ == "__main__":
  # En Linux sin sesión gráfica, PyQt no puede crear ventanas.
  if es_linux() and not hay_sesion_grafica():
    print("Error: no se detectó una sesión gráfica. Ejecuta la app desde un escritorio Linux o configura DISPLAY/Wayland.")
    sys.exit(1)

  app = QApplication(sys.argv)
  ventana = DownloaderUI()
  ventana.show()
  sys.exit(app.exec_())
