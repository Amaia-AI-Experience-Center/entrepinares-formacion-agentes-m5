
import json
from collections import Counter
from pathlib import Path

from inventario import leer_inventario
from correlacion import analizar


BASE = Path(__file__).resolve().parent
RUTA_CVES = BASE / "datos" / "kev_demo.json"


def calcular_prioridad(estado, criticidad, tipo, en_kev):
    """
    Calcula una prioridad orientativa para el MVP.

    - No aplicable: sin prioridad para esta CVE.
    - CVE explotada + activo critico u OT: alta.
    - CVE explotada + otros activos: media.
    - Resto de casos: media o baja segun criticidad.
    """

    if estado == "no_aplicable":
        return "sin_prioridad"

    if en_kev:
        if criticidad == "alta" or tipo == "OT":
            return "alta"
        return "media"

    if criticidad == "alta" or tipo == "OT":
        return "media"

    return "baja"


def priorizar_resultados():
    """Enriquece y prioriza los hallazgos existentes."""

    activos = {
        a["asset_id"]: a
        for a in leer_inventario()
    }

    catalogo = json.loads(
        RUTA_CVES.read_text(encoding="utf-8")
    )

    cves_kev = {
        v["cveID"]
        for v in catalogo["vulnerabilities"]
    }

    resultados = analizar()
    hallazgos = []

    for resultado in resultados:
        activo = activos[resultado["asset_id"]]
        hallazgo = resultado.copy()

        hallazgo["centro"] = activo["centro"]
        hallazgo["tipo"] = activo["tipo"]
        hallazgo["criticidad"] = activo["criticidad"]
        hallazgo["en_kev"] = resultado["cve"] in cves_kev

        hallazgo["prioridad"] = calcular_prioridad(
            estado=resultado["estado"],
            criticidad=activo["criticidad"],
            tipo=activo["tipo"],
            en_kev=hallazgo["en_kev"],
        )

        hallazgos.append(hallazgo)

    orden = {
        "alta": 0,
        "media": 1,
        "baja": 2,
        "sin_prioridad": 3,
    }

    return sorted(
        hallazgos,
        key=lambda h: (
            orden[h["prioridad"]],
            h["asset_id"],
        ),
    )


if __name__ == "__main__":
    hallazgos = priorizar_resultados()

    conteo = Counter(
        h["prioridad"] for h in hallazgos
    )

    print("PRIORIZACION DE VULNERABILIDADES")
    print(f"Evaluaciones: {len(hallazgos)}")
    print(f"Prioridad alta: {conteo['alta']}")
    print(f"Prioridad media: {conteo['media']}")
    print(f"Prioridad baja: {conteo['baja']}")
    print(f"Sin prioridad: {conteo['sin_prioridad']}")

    print("\nHALLAZGOS ORDENADOS:")

    for h in hallazgos:
        print(
            f"{h['asset_id']} | "
            f"{h['cve']} | "
            f"{h['estado']} | "
            f"Prioridad: {h['prioridad'].upper()} | "
            f"{h['tipo']}"
        )
