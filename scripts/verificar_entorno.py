"""Comprobacion de SOLO LECTURA del entorno (sin red, sin Azure, sin credenciales).

Uso (desde la raiz del repositorio):
    python scripts/verificar_entorno.py

Comprueba la version de Python, que cada paquete del lock tenga la version
EXACTA, `pip check`, que existan los archivos del proyecto y -solo de forma
informativa- si estan definidas las variables de Foundry. Nunca muestra
valores de variables.
"""

import importlib.metadata as md
import os
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LOCK = "requirements-codespaces.lock.txt" if sys.platform.startswith("linux") else "requirements-notebook.lock.txt"
ARCHIVOS = [
    "orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py",
    "agente_multiherramienta.py",
    "notebooks/entrepinares_utils.py",
    "notebooks/entrepinares_01_fundamentos_offline.ipynb",
    "notebooks/entrepinares_02_workflow_foundry.ipynb",
    "datos/inventario_demo.csv",
    "datos/cisa_kev_cache.json",
    "datos/cribado_kev.json",
]
VARIABLES = [
    "FOUNDRY_PROJECT_ENDPOINT", "AZURE_AI_MODEL_DEPLOYMENT_NAME",
    "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "AZURE_CLIENT_SECRET",
]

fallos = 0


def resultado(ok: bool, texto: str) -> None:
    global fallos
    print(("[OK]    " if ok else "[FALLO] ") + texto)
    if not ok:
        fallos += 1


def normalizar(nombre: str) -> str:
    return re.sub(r"[-_.]+", "-", nombre).lower()


def main() -> int:
    v = sys.version_info
    resultado((v.major, v.minor) == (3, 13), f"Python {v.major}.{v.minor}.{v.micro} (se necesita 3.13.x)")
    print(f"        Lock usado en esta plataforma: {LOCK}")

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
    resultado(faltan == 0 and distintos == 0,
              f"Paquetes del lock: {total} comprobados, {faltan} faltan, {distintos} con version distinta")

    salida = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True).stdout.strip()
    resultado("No broken requirements" in salida, f"pip check: {salida.splitlines()[0] if salida else 'sin salida'}")

    for archivo in ARCHIVOS:
        resultado((RAIZ / archivo).is_file(), archivo)

    print("\n--- Solo para el Cuaderno 2 / DevUI (informativo; el Cuaderno 1 no lo necesita) ---")
    for nombre in VARIABLES:
        print(f"        {nombre:32}: {'definida' if os.environ.get(nombre, '').strip() else 'NO definida'}")

    if fallos:
        print(f"\n{fallos} comprobacion(es) fallida(s).")
        return 1
    print("\nEntorno coherente. Puedes abrir el Cuaderno 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
