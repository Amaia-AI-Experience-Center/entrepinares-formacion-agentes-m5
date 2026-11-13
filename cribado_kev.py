
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from fuente_kev import obtener_catalogo
from inventario import leer_inventario


BASE = Path(__file__).resolve().parent
SALIDA = BASE / "datos" / "cribado_kev.json"


def normalizar(texto):
    """Normaliza nombres para facilitar comparaciones."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )
    return re.sub(
        r"[^a-z0-9]+", " ", texto.lower()
    ).strip()


# Equivalencias de fabricantes del inventario.
FABRICANTES = {
    "PaperCut": ["papercut"],
    "Palo Alto Networks": [
        "palo alto networks", "palo alto"
    ],
    "Siemens": ["siemens"],
    "Microsoft": ["microsoft"],
}


# Equivalencias iniciales de productos.
# "producto" = nombre concreto identificado.
# "familia" = producto o familia que requiere revisión.
PRODUCTOS = {

    "PaperCut MF": {
        "mf": "producto",
        "papercut mf": "producto",
        "mf ng": "familia",
        "ng mf": "familia",
        "papercut mf ng": "familia",
        "papercut ng mf": "familia",
    },
    "PaperCut NG": {
        "ng": "producto",
        "papercut ng": "producto",
        "mf ng": "familia",
        "ng mf": "familia",
        "papercut mf ng": "familia",
        "papercut ng mf": "familia",
    },
    "PAN-OS": {
        "pan os": "producto",
    },
    "SIMATIC CP 1543-1": {
        "simatic cp 1543 1": "producto",
        "cp 1543 1": "producto",
        "simatic cp": "familia",
    },
    "SIMATIC S7-1500": {
        "simatic s7 1500": "producto",
        "s7 1500": "producto",
        "simatic s7": "familia",
    },
    "Windows Server 2022": {
        "windows server 2022": "producto",
        "windows server": "familia",
        "windows": "familia",
    },
}


def fabricante_coincide(activo, cve):
    fabricante = activo["fabricante"]
    opciones = FABRICANTES.get(
        fabricante, [fabricante]
    )

    fabricante_cisa = normalizar(
        cve.get("vendorProject", "")
    )

    return fabricante_cisa in {
        normalizar(opcion) for opcion in opciones
    }


def clasificar_producto(activo, cve):
    producto = activo["producto"]
    producto_cisa = normalizar(
        cve.get("product", "")
    )

    equivalencias = PRODUCTOS.get(producto, {})

    if producto_cisa in equivalencias:
        return equivalencias[producto_cisa]

    if producto_cisa == normalizar(producto):
        return "producto"

    return "solo_fabricante"


def realizar_cribado():
    catalogo, info_cisa = obtener_catalogo()
    activos = leer_inventario()

    candidatos = []
    pendientes_fabricante = []

    for cve in catalogo["vulnerabilities"]:
        for activo in activos:

            if not fabricante_coincide(activo, cve):
                continue

            categoria = clasificar_producto(
                activo, cve
            )

            resultado = {
                "asset_id": activo["asset_id"],
                "producto_inventario": activo["producto"],
                "version_inventario": activo["version"],
                "criticidad": activo["criticidad"],
                "cve": cve["cveID"],
                "fabricante_cisa": cve["vendorProject"],
                "producto_cisa": cve["product"],
                "descripcion": cve.get(
                    "shortDescription", ""
                ),
                "categoria": categoria,
                "fecha_cisa": cve.get("dateAdded"),
            }

            if categoria == "solo_fabricante":
                pendientes_fabricante.append(resultado)
            else:
                candidatos.append(resultado)

    orden = {"producto": 0, "familia": 1}

    candidatos.sort(
        key=lambda r: (
            orden[r["categoria"]],
            r["cve"],
            r["asset_id"],
        )
    )

    resumen = {
        "total_cves_cisa": len(
            catalogo["vulnerabilities"]
        ),
        "total_activos": len(activos),
        "cves_candidatas": len({
            r["cve"] for r in candidatos
        }),
        "pares_activo_cve_candidatos": len(candidatos),
        "categorias_candidatos": dict(
            Counter(r["categoria"] for r in candidatos)
        ),
        "cves_pendientes_por_fabricante": len({
            r["cve"] for r in pendientes_fabricante
        }),
        "pares_pendientes_por_fabricante": len(
            pendientes_fabricante
        ),
    }

    salida = {
        "fuente": info_cisa,
        "resumen": resumen,
        "candidatos": candidatos,
        "pendientes_fabricante": pendientes_fabricante,
        "advertencia": (
            "El cribado identifica coincidencias textuales "
            "de fabricante y producto. No determina "
            "versiones afectadas ni confirma vulnerabilidades. "
            "Las coincidencias no identificadas pueden "
            "requerir equivalencias adicionales."
        ),
    }

    SALIDA.parent.mkdir(
        parents=True, exist_ok=True
    )

    SALIDA.write_text(
        json.dumps(
            salida, indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )

    return salida


if __name__ == "__main__":
    resultado = realizar_cribado()
    resumen = resultado["resumen"]

    print("CRIBADO COMPLETO CISA KEV")
    print(f"CVE revisadas: {resumen['total_cves_cisa']}")
    print(f"Activos: {resumen['total_activos']}")
    print(f"CVE candidatas: {resumen['cves_candidatas']}")
    print(
        "Pares activo-CVE candidatos: "
        f"{resumen['pares_activo_cve_candidatos']}"
    )
    print(
        "CVE pendientes por fabricante: "
        f"{resumen['cves_pendientes_por_fabricante']}"
    )

    print("\nNUESTRAS TRES CVE DE REFERENCIA:")

    for identificador in [
        "CVE-2023-27350",
        "CVE-2024-3400",
        "CVE-2016-8562",
    ]:
        encontrados = [
            r for r in resultado["candidatos"]
            if r["cve"] == identificador
        ]

        print(
            f"\n{identificador}: "
            f"{len(encontrados)} candidatos"
        )

        for r in encontrados:
            print(
                f"  {r['asset_id']} | "
                f"{r['categoria']} | "
                f"{r['producto_cisa']}"
            )

    print(f"\nResultado guardado: {SALIDA}")