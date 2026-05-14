#!/bin/bash
# Crea o usa el entorno virtual 'myenv' y instala las dependencias desde requirements.txt

# Verificar que python3-venv y python3-full estén instalados
if ! dpkg -s python3-venv python3-full >/dev/null 2>&1; then
    echo "❌ Faltan paquetes del sistema: python3-venv y/o python3-full"
    echo "   Ejecuta: sudo apt install python3-venv python3-full"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "myenv" ]; then
    echo "[INFO] No se encontró 'myenv'. Creando entorno virtual..."
    python3 -m venv myenv
    if [ $? -ne 0 ]; then
        echo "❌ Error al crear el entorno virtual."
        exit 1
    fi
    echo "✅ Entorno virtual 'myenv' creado."
else
    echo "✅ El entorno virtual 'myenv' ya existe."
fi

# Activar el entorno virtual
source myenv/bin/activate
echo "[INFO] Entorno virtual activado."

# Verificar si requirements.txt existe
if [ ! -f "requirements.txt" ]; then
    echo "❌ No se encontró el archivo requirements.txt."
    deactivate
    exit 1
fi

# Instalar o actualizar dependencias
echo "[INFO] Instalando dependencias..."
pip install --upgrade pip
pip install --break-system-packages -r requirements.txt

echo "✅ Dependencias instaladas correctamente."

# Desactivar entorno virtual
deactivate
echo "[INFO] Entorno virtual desactivado."
