
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from fuente_kev import obtener_catalogo
from inventario import leer_inventario
from cribado_kev import fabricante_coincide, clasificar_producto


BASE = Path(__file__).resolve().parent

RUTA_REFERENCIA = (
    BASE / "datos" / "historial_kev"
    / "catalogo_referencia.json"
)

RUTA_NOVEDADES = BASE / "datos" / "novedades_kev.json"


def indexar(catalogo):
    """Organiza las CVE por identificador."""
    registros = catalogo["vulnerabilities"]

    indice = {
        registro["cveID"]: registro
        for registro in registros
    }

    if len(indice) != len(registros):
        raise ValueError("Existen identificadores CVE duplicados.")

    return indice


def resumir_cve(registro):
    return {
        "cve": registro["cveID"],
        "fabricante": registro.get("vendorProject"),
        "producto": registro.get("product"),
        "fecha_inclusion": registro.get("dateAdded"),
        "descripcion": registro.get("shortDescription"),
    }


def cruzar_novedades_con_inventario(cves_nuevas):
    """Cruza las nuevas CVE con el inventario existente."""

    activos = leer_inventario()

    candidatos = []
    pendientes_fabricante = []

    for cve in cves_nuevas:
        for activo in activos:

            if not fabricante_coincide(activo, cve):
                continue

            categoria = clasificar_producto(activo, cve)

            resultado = {
                "cve": cve["cveID"],
                "asset_id": activo["asset_id"],
                "producto_inventario": activo["producto"],
                "version_inventario": activo["version"],
                "producto_cisa": cve["product"],
                "categoria": categoria,
            }

            if categoria == "solo_fabricante":
                pendientes_fabricante.append(resultado)
            else:
                candidatos.append(resultado)

    return candidatos, pendientes_fabricante

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Forzar una nueva descarga de CISA",
    )
    args = parser.parse_args()

    print("COMPARACIÓN DE CATÁLOGOS CISA KEV")

    if not RUTA_REFERENCIA.exists():
        print("ERROR: No existe el catálogo de referencia.")
        return

    anterior = json.loads(
        RUTA_REFERENCIA.read_text(encoding="utf-8")
    )

    actual, info = obtener_catalogo(
        forzar=args.forzar
    )

    if info.get("aviso"):
        print(f"ADVERTENCIA: {info['aviso']}")
        print("Comparación cancelada por problemas con la fuente.")
        raise SystemExit(1)

    antes = indexar(anterior)
    ahora = indexar(actual)

    ids_antes = set(antes)
    ids_ahora = set(ahora)

    nuevas = sorted(ids_ahora - ids_antes)
    retiradas = sorted(ids_antes - ids_ahora)

    modificadas = sorted(
        cve for cve in ids_antes & ids_ahora
        if antes[cve] != ahora[cve]
    )

    
    # Analizar únicamente las CVE nuevas.
    candidatos, pendientes_fabricante = (
        cruzar_novedades_con_inventario(
            [ahora[cve] for cve in nuevas]
        )
    )


    resultado = {
        "fecha_comparacion": datetime.now(
            timezone.utc
        ).isoformat(),
        "version_referencia": anterior["catalogVersion"],
        "version_actual": actual["catalogVersion"],
        "modo_fuente": info["modo"],
        "total_anterior": len(antes),
        "total_actual": len(ahora),
        "resumen": {
            "nuevas": len(nuevas),
            "modificadas": len(modificadas),
            "retiradas": len(retiradas),
        },
        
        "coincidencias_inventario": {
            "cves_candidatas": len({
                r["cve"] for r in candidatos
            }),
            "pares_candidatos": len(candidatos),
            "cves_solo_fabricante": len({
                r["cve"] for r in pendientes_fabricante
            }),
            "pares_solo_fabricante": len(
                pendientes_fabricante
            ),
            "candidatos": candidatos,
            "pendientes_fabricante": pendientes_fabricante,
        },
        "nuevas": [
            resumir_cve(ahora[cve])
            for cve in nuevas
        ],
        "modificadas": [
            {
                "cve": cve,
                "campos_modificados": sorted(
                    campo
                    for campo in (
                        set(antes[cve]) | set(ahora[cve])
                    )
                    if antes[cve].get(campo)
                    != ahora[cve].get(campo)
                ),
            }
            for cve in modificadas
        ],
        "retiradas": [
            resumir_cve(antes[cve])
            for cve in retiradas
        ],
        "advertencia": (
            "Son cambios del catálogo CISA. "
            "No confirman afectación de los activos."
        ),
    }

    RUTA_NOVEDADES.write_text(
        json.dumps(
            resultado,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nReferencia: {anterior['catalogVersion']}")
    print(f"Actual: {actual['catalogVersion']}")
    print(f"Origen: {info['modo']}")

    print(f"\nCVE anteriores: {len(antes)}")
    print(f"CVE actuales: {len(ahora)}")
    print(f"Nuevas: {len(nuevas)}")
    print(f"Modificadas: {len(modificadas)}")
    print(f"Retiradas: {len(retiradas)}")

    for cve in nuevas[:10]:
        registro = ahora[cve]
        print(
            f"  NUEVA: {cve} | "
            f"{registro.get('vendorProject')} | "
            f"{registro.get('product')}"
        )

    print("\nCOINCIDENCIAS CON EL INVENTARIO")
    print(f"Pares candidatos: {len(candidatos)}")
    print(
        "Pares solo fabricante: "
        f"{len(pendientes_fabricante)}"
    )

    for r in candidatos + pendientes_fabricante:
        print(
            f"  {r['asset_id']} | {r['cve']} "
            f"| {r['categoria']}"
        )
    print(f"\nResultado guardado: {RUTA_NOVEDADES}")
    print("La referencia original no se ha modificado.")


if __name__ == "__main__":
    main()