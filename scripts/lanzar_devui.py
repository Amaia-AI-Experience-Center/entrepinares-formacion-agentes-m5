"""Lanza DevUI (solo localhost) con el workflow didactico de Entrepinares.

Uso (desde la raiz del repositorio, con el entorno virtual activado):

    python scripts\\lanzar_devui.py --puerto 8091              # con autenticacion
    python scripts\\lanzar_devui.py --puerto 8091 --sin-auth   # sin autenticacion

Con autenticacion, define antes un token propio en esa terminal:
    $env:DEVUI_AUTH_TOKEN = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')

DevUI escucha SOLO en 127.0.0.1. Este script solo carga el archivo .env (para
que el endpoint de Foundry este disponible) y llama a la funcion
`ejecutar_devui` del workflow, sin modificarla. El workflow es de solo lectura.
"""

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "notebooks"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--puerto", type=int, default=8091)
    parser.add_argument(
        "--sin-auth", action="store_true",
        help="Desactiva la autenticacion de DevUI (solo para tu equipo, en localhost).",
    )
    args = parser.parse_args()

    import entrepinares_utils as u

    modulo = u.preparar_entorno()
    if not u.comprobar_configuracion()["endpoint_configurado"]:
        sys.exit("Falta FOUNDRY_PROJECT_ENDPOINT: copia .env.example a .env y rellénalo (ver la guía).")
    modulo.ejecutar_devui(args.puerto, args.sin_auth)


if __name__ == "__main__":
    main()
