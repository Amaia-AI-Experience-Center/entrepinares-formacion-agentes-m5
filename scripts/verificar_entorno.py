"""Comprobacion de SOLO LECTURA del entorno local (sin red ni llamadas a Azure).

Uso (raiz del repositorio, con el venv activado):
    python scripts/verificar_entorno.py

Comprueba Python 3.13, que estas en un entorno virtual, que cada paquete de
requirements.lock.txt tiene la version EXACTA, `pip check`, los archivos del
proyecto y, de forma informativa, la configuracion para Foundry y Azure CLI.
"""

import importlib.metadata as md
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOCK = "requirements.lock.txt"
ARCHIVOS = [
    "orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py",
    "agente_multiherramienta.py",
    "notebooks/entrepinares_utils.py",
    "notebooks/entrepinares_01_fundamentos_offline.ipynb",
    "notebooks/entrepinares_02_workflow_foundry.ipynb",
    "scripts/probar_hosted_v5.py",
    "datos/inventario_demo.csv",
    "datos/cisa_kev_cache.json",
    "datos/cribado_kev.json",
]
fallos = 0


def resultado(ok: bool, texto: str) -> None:
    global fallos
    print(("[OK]    " if ok else "[FALLO] ") + texto)
    fallos += not ok


def normalizar(nombre: str) -> str:
    return re.sub(r"[-_.]+", "-", nombre).lower()


def main() -> int:
    v = sys.version_info
    resultado((v.major, v.minor) == (3, 13), f"Python {v.major}.{v.minor}.{v.micro} (se necesita 3.13.x)")
    resultado(sys.prefix != sys.base_prefix, "Estás dentro de un entorno virtual (venv activado)")

    instalados = {normalizar(d.metadata["Name"]): d.version for d in md.distributions() if d.metadata["Name"]}
    total = faltan = distintos = 0
    for linea in (RAIZ / LOCK).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([A-Za-z0-9_.-]+)==([^\s#]+)", linea)
        if not m:
            continue
        total += 1
        nombre, version = normalizar(m.group(1)), m.group(2)
        if nombre not in instalados:
            faltan += 1
            print(f"        falta: {nombre}=={version}")
        elif instalados[nombre] != version:
            distintos += 1
            print(f"        version distinta: {nombre} (instalada {instalados[nombre]}, esperada {version})")
    resultado(faltan == 0 and distintos == 0, f"Paquetes del lock: {total} comprobados, {faltan} faltan, {distintos} con version distinta")

    salida = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True).stdout.strip()
    resultado("No broken requirements" in salida, f"pip check: {salida.splitlines()[0] if salida else 'sin salida'}")

    for archivo in ARCHIVOS:
        resultado((RAIZ / archivo).is_file(), archivo)

    print("\n--- Para el Cuaderno 2, DevUI y Hosted (informativo; el Cuaderno 1 no lo necesita) ---")
    print(f"        Azure CLI (az) en el PATH : {'sí' if shutil.which('az') else 'NO (instálala y reabre la terminal)'}")
    print(f"        archivo .env              : {'existe' if (RAIZ / '.env').is_file() else 'no existe (copia .env.example a .env)'}")
    for nombre in ("FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_MODEL_DEPLOYMENT_NAME"):
        print(f"        {nombre:32}: {'definida en el entorno' if os.environ.get(nombre, '').strip() else 'se leerá de .env'}")

    if fallos:
        print(f"\n{fallos} comprobacion(es) fallida(s).")
        return 1
    print("\nEntorno coherente. Puedes abrir el Cuaderno 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
