
import json
import re
from pathlib import Path

from inventario import leer_inventario


BASE = Path(__file__).resolve().parent
RUTA_CVES = BASE / "datos" / "kev_demo.json"

CVE_PAPERCUT = "CVE-2023-27350"
FUENTE_FABRICANTE = (
    "https://www.papercut.com/kb/Main/PO-1216-and-PO-1219"
)


def convertir_version(version):
    """Convierte versiones numéricas simples a tuplas."""
    if not re.fullmatch(r"\d+(?:\.\d+){1,2}", version):
        return None

    partes = tuple(int(p) for p in version.split("."))
    return partes + (0,) * (3 - len(partes))


def evaluar_papercut(activo):
    """Evalúa CVE-2023-27350 para PaperCut MF/NG."""

    fabricante = activo["fabricante"].strip().lower()
    producto = activo["producto"].strip().lower()

    if fabricante != "papercut":
        return None

    if producto not in {"papercut mf", "papercut ng"}:
        return None

    version = convertir_version(activo["version"])

    resultado = {
        "asset_id": activo["asset_id"],
        "producto": activo["producto"],
        "version": activo["version"],
        "cve": CVE_PAPERCUT,
        "estado": "posible",
        "justificacion": "",
        "fuente": FUENTE_FABRICANTE,
    }

    if version is None:
        resultado["justificacion"] = (
            "Versión desconocida o no interpretable."
        )

    elif version >= (22, 0, 9):
        resultado["estado"] = "no_aplicable"
        resultado["justificacion"] = (
            "Versión 22.0.9 o posterior: corregida "
            "según el fabricante."
        )

    elif (22, 0, 0) <= version <= (22, 0, 8):
        if activo["configuracion"] == "servidor_aplicacion":
            resultado["estado"] = "confirmada"
            resultado["justificacion"] = (
                "Producto, versión y componente afectados "
                "según el aviso del fabricante."
            )
        else:
            resultado["justificacion"] = (
                "Versión afectada, pero es necesario "
                "comprobar el componente instalado."
            )

    else:
        resultado["justificacion"] = (
            "Versión fuera del rango implementado "
            "en esta primera regla. Requiere revisión."
        )

    return resultado


CVE_PALOALTO = "CVE-2024-3400"
FUENTE_PALOALTO = (
    "https://security.paloaltonetworks.com/CVE-2024-3400"
)


def evaluar_paloalto(activo):
    """Evalúa CVE-2024-3400 para PAN-OS 11.1.2."""

    fabricante = activo["fabricante"].strip().lower()
    producto = activo["producto"].strip().lower()

    if fabricante != "palo alto networks":
        return None

    if producto != "pan-os":
        return None

    version = activo["version"].strip().lower()
    configuracion = activo["configuracion"].strip().lower()

    resultado = {
        "asset_id": activo["asset_id"],
        "producto": activo["producto"],
        "version": activo["version"],
        "cve": CVE_PALOALTO,
        "estado": "posible",
        "justificacion": "",
        "fuente": FUENTE_PALOALTO,
    }

    # Primera implementación: solo rama 11.1.2.
    # 11.1.2 equivale a no tener hotfix.
    match = re.fullmatch(r"11\.1\.2(?:-h(\d+))?", version)

    if match is None:
        resultado["justificacion"] = (
            "Versión fuera del subconjunto implementado. "
            "Requiere comprobar el aviso del fabricante."
        )
        return resultado

    hotfix = int(match.group(1) or 0)

    if hotfix >= 3:
        resultado["estado"] = "no_aplicable"
        resultado["justificacion"] = (
            "Versión 11.1.2-h3 o hotfix posterior "
            "de esta rama: vulnerabilidad corregida."
        )

    elif configuracion == "globalprotect_si":
        resultado["estado"] = "confirmada"
        resultado["justificacion"] = (
            "Versión afectada y GlobalProtect "
            "Gateway o Portal configurado."
        )

    elif configuracion == "globalprotect_no":
        resultado["estado"] = "no_aplicable"
        resultado["justificacion"] = (
            "Versión afectada, pero sin Gateway "
            "ni Portal GlobalProtect configurado."
        )

    else:
        resultado["justificacion"] = (
            "Versión afectada, pero se desconoce "
            "si GlobalProtect Gateway o Portal está configurado."
        )

    return resultado



CVE_SIEMENS = "CVE-2016-8562"
FUENTE_SIEMENS = (
    "https://nvd.nist.gov/vuln/detail/CVE-2016-8562"
)


def evaluar_siemens(activo):
    """Evalúa CVE-2016-8562 para SIMATIC CP 1543-1."""

    fabricante = activo["fabricante"].strip().lower()
    producto = activo["producto"].strip().lower()

    if fabricante != "siemens":
        return None

    if producto != "simatic cp 1543-1":
        return None

    version = convertir_version(activo["version"])

    resultado = {
        "asset_id": activo["asset_id"],
        "producto": activo["producto"],
        "version": activo["version"],
        "cve": CVE_SIEMENS,
        "estado": "posible",
        "justificacion": "",
        "fuente": FUENTE_SIEMENS,
    }

    if version is None:
        resultado["justificacion"] = (
            "Firmware desconocido o no interpretable. "
            "Se necesita comprobar la versión instalada."
        )

    elif version < (2, 0, 28):
        resultado["estado"] = "confirmada"
        resultado["justificacion"] = (
            "Producto y firmware dentro del rango afectado "
            "(anterior a 2.0.28). "
            "La posibilidad de explotación depende de "
            "condiciones adicionales relacionadas con SNMP "
            "que deben verificarse en el equipo."
        )

    else:
        resultado["estado"] = "no_aplicable"
        resultado["justificacion"] = (
            "Firmware 2.0.28 o posterior: fuera del rango "
            "afectado documentado para esta CVE."
        )

    return resultado




def analizar():
    activos = leer_inventario()

    catalogo = json.loads(
        RUTA_CVES.read_text(encoding="utf-8")
    )

    cves = {
        v["cveID"]
        for v in catalogo["vulnerabilities"]
    }

    
    faltantes = {
        CVE_PAPERCUT,
        CVE_PALOALTO,
        CVE_SIEMENS,
    } - cves

    if faltantes:
        raise ValueError(
            f"CVE no encontradas en kev_demo.json: {faltantes}"
        )


    resultados = []

    evaluadores = (
        evaluar_papercut,
        evaluar_paloalto,
        evaluar_siemens,
    )

    for activo in activos:
        for evaluador in evaluadores:
            resultado = evaluador(activo)

            if resultado is not None:
                resultados.append(resultado)

    return resultados


if __name__ == "__main__":
    resultados = analizar()

    print("CORRELACIÓN DE VULNERABILIDADES")
    print(f"Coincidencias evaluadas: {len(resultados)}")

    for r in resultados:
        print(
            f"\n{r['asset_id']} | "
            f"{r['producto']} {r['version']}"
        )
        print(f"CVE: {r['cve']}")
        print(f"Estado: {r['estado']}")
        print(f"Motivo: {r['justificacion']}")
        print(f"Fuente: {r['fuente']}")

