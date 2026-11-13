
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen


BASE = Path(__file__).resolve().parent

URL_CISA = (
    "https://raw.githubusercontent.com/cisagov/kev-data/"
    "refs/heads/develop/known_exploited_vulnerabilities.json"
)

RUTA_CACHE = BASE / "datos" / "cisa_kev_cache.json"
DURACION_CACHE = timedelta(hours=24)


def validar_catalogo(catalogo):
    """Comprueba la estructura básica del catálogo CISA."""

    if not isinstance(catalogo, dict):
        raise ValueError("El catálogo no es un objeto JSON.")

    cves = catalogo.get("vulnerabilities")

    if not isinstance(cves, list) or not cves:
        raise ValueError("El catálogo no contiene CVE válidas.")

    if catalogo.get("count") != len(cves):
        raise ValueError("El número de CVE no coincide.")

    if not isinstance(catalogo.get("catalogVersion"), str):
        raise ValueError("Falta la versión del catálogo.")

    if not all(
        isinstance(cve, dict)
        and isinstance(cve.get("cveID"), str)
        for cve in cves
    ):
        raise ValueError("Hay entradas CVE inválidas.")


def leer_cache():
    """Recupera una copia local previamente validada."""

    if not RUTA_CACHE.exists():
        return None

    try:
        datos = json.loads(
            RUTA_CACHE.read_text(encoding="utf-8")
        )

        catalogo = datos["catalogo"]
        fecha = datetime.fromisoformat(
            datos["obtenido_en_utc"]
        )

        validar_catalogo(catalogo)

        if fecha.tzinfo is None:
            raise ValueError("Fecha sin zona horaria.")

        return catalogo, fecha

    except (OSError, ValueError, KeyError, TypeError):
        return None


def descargar_catalogo():
    """Descarga el catálogo completo desde CISA GitHub."""

    peticion = Request(
        URL_CISA,
        headers={
            "User-Agent": "MAF-Entrepinares-Demo/1.0",
            "Accept": "application/json",
        },
    )

    with urlopen(peticion, timeout=25) as respuesta:
        catalogo = json.loads(respuesta.read())

    validar_catalogo(catalogo)

    return catalogo


def guardar_cache(catalogo, fecha):
    """Guarda una copia validada usando reemplazo atómico."""

    RUTA_CACHE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    contenido = {
        "obtenido_en_utc": fecha.isoformat(),
        "fuente": URL_CISA,
        "catalogo": catalogo,
    }

    temporal = RUTA_CACHE.with_suffix(".tmp")

    temporal.write_text(
        json.dumps(contenido, ensure_ascii=False),
        encoding="utf-8",
    )

    temporal.replace(RUTA_CACHE)


def obtener_catalogo(forzar=False):
    """
    Devuelve (catalogo, informacion).

    - Usa la caché durante 24 horas.
    - Descarga si caduca o se fuerza la actualización.
    - Si falla la descarga, usa la última copia válida.
    """

    ahora = datetime.now(timezone.utc)
    cache = leer_cache()

    if cache is not None:
        catalogo, fecha = cache

        antiguedad = ahora - fecha

        if (
            not forzar
            and timedelta(0) <= antiguedad < DURACION_CACHE
        ):
            return catalogo, {
                "modo": "cache",
                "ultima_descarga": fecha.isoformat(),
                "catalog_version": catalogo["catalogVersion"],
                "total_cves": catalogo["count"],
                "aviso": None,
            }

    try:
        catalogo = descargar_catalogo()
        fecha = datetime.now(timezone.utc)

        guardar_cache(catalogo, fecha)

        return catalogo, {
            "modo": "descarga",
            "ultima_descarga": fecha.isoformat(),
            "catalog_version": catalogo["catalogVersion"],
            "total_cves": catalogo["count"],
            "aviso": None,
        }

    except Exception as error:
        if cache is None:
            raise RuntimeError(
                "No se pudo descargar CISA KEV y "
                "no existe una caché válida."
            ) from error

        catalogo, fecha = cache

        return catalogo, {
            "modo": "cache_desactualizada",
            "ultima_descarga": fecha.isoformat(),
            "catalog_version": catalogo["catalogVersion"],
            "total_cves": catalogo["count"],
            "aviso": (
                "La actualización ha fallado. "
                f"Se utiliza la última copia válida. "
                f"Motivo: {error}"
            ),
        }


if __name__ == "__main__":
    forzar = "--forzar" in sys.argv[1:]

    catalogo, info = obtener_catalogo(forzar=forzar)

    print("CONSULTA DE CISA KEV")
    print(f"Modo: {info['modo']}")
    print(f"Versión: {info['catalog_version']}")
    print(f"Total de CVE: {info['total_cves']}")
    print(f"Última descarga: {info['ultima_descarga']}")

    if info["aviso"]:
        print(f"AVISO: {info['aviso']}")
