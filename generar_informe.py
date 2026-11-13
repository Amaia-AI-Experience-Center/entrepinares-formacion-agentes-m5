
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from inventario import leer_inventario
from priorizacion import priorizar_resultados
from fuente_kev import obtener_catalogo


BASE = Path(__file__).resolve().parent
RUTA_CVES = BASE / "datos" / "kev_demo.json"
RUTA_INFORME = BASE / "informes" / "informe_vulnerabilidades.md"

RUTA_CRIBADO = BASE / "datos" / "cribado_kev.json"
RUTA_NVD = BASE / "datos" / "evaluacion_nvd_piloto.json"


def limpiar(valor):
    """Prepara un valor para una tabla Markdown."""
    return str(valor).replace("|", "\\|").replace("\n", " ")


def anadir_analisis_ampliado(lineas):
    """Añade el cribado KEV y el piloto NVD al informe."""

    # NIVEL 1: Cribado completo de CISA KEV
    lineas.extend([
        "## 6. Cribado completo de CISA KEV",
        "",
        "Este apartado refleja las coincidencias iniciales "
        "de fabricante, producto y familia. "
        "No confirma que las versiones estén afectadas.",
        "",
    ])

    if RUTA_CRIBADO.exists():
        datos = json.loads(
            RUTA_CRIBADO.read_text(encoding="utf-8")
        )

        candidatos = datos.get("candidatos", [])
        pendientes = datos.get(
            "pendientes_fabricante", []
        )

        cves_candidatas = {
            r["cve"] for r in candidatos
        }
        cves_pendientes = {
            r["cve"] for r in pendientes
        }

        categorias = Counter(
            r.get("categoria") for r in candidatos
        )

        lineas.extend([
            f"- CVE candidatas distintas: "
            f"**{len(cves_candidatas)}**",
            f"- Pares activo-CVE candidatos: "
            f"**{len(candidatos)}**",
            f"- Coincidencias de producto: "
            f"**{categorias['producto']}**",
            f"- Coincidencias de familia: "
            f"**{categorias['familia']}**",
            f"- CVE pendientes por fabricante: "
            f"**{len(cves_pendientes)}**",
            f"- Pares pendientes por fabricante: "
            f"**{len(pendientes)}**",
            "",
            "Las CVE de ambos grupos pueden solaparse. "
            "No deben sumarse como conjuntos independientes.",
            "",
            "**Cobertura:** Este cribado utiliza el archivo "
            "JSON generado anteriormente. No se recalcula "
            "automáticamente al elaborar el informe.",
            "",
        ])
    else:
        lineas.extend([
            "**Cribado no disponible.** "
            "No se encuentra `datos/cribado_kev.json`.",
            "",
        ])

    # NIVEL 2: Evaluación técnica mediante NVD
    lineas.extend([
        "## 7. Evaluación técnica NVD - Piloto PAN-OS",
        "",
        "Evaluación automatizada de criterios CPE "
        "y determinados rangos de versiones publicados "
        "por NVD. La cobertura es parcial.",
        "",
    ])

    if RUTA_NVD.exists():
        datos = json.loads(
            RUTA_NVD.read_text(encoding="utf-8")
        )

        resultados = datos.get("resultados", [])
        estados = Counter(
            r.get("estado") for r in resultados
        )
        cves = {
            r["cve"] for r in resultados
        }

        lineas.extend([
            f"- CVE investigadas: **{len(cves)}**",
            f"- Evaluaciones activo-CVE: "
            f"**{len(resultados)}**",
            f"- Coincidencias CPE: "
            f"**{estados['coincidencia_cpe']}**",
            f"- Fuera de criterios NVD evaluados: "
            f"**{estados['fuera_criterios_nvd']}**",
            f"- Pendientes de revisión: "
            f"**{estados['pendiente_revision']}**",
            "",
            "**Detalle de evaluaciones:**",
            "",
            "| Activo | Versión | CVE | Estado | Motivo |",
            "|---|---|---|---|---|",
        ])

        for r in sorted(
            resultados,
            key=lambda x: (
                x.get("asset_id", ""),
                x.get("cve", ""),
            ),
        ):
            lineas.append(
                f"| {limpiar(r.get('asset_id', ''))} "
                f"| {limpiar(r.get('version', ''))} "
                f"| {limpiar(r.get('cve', ''))} "
                f"| {limpiar(r.get('estado', ''))} "
                f"| {limpiar(r.get('motivo', ''))} |"
            )

        lineas.extend([
            "",
            "**Advertencia:** La coincidencia CPE no "
            "demuestra explotación ni que se cumplan "
            "todas las condiciones necesarias. "
            "Una versión fuera de los criterios evaluados "
            "no implica que el activo esté libre "
            "de otras vulnerabilidades.",
            "",
            "Los resultados corresponden a la última "
            "ejecución guardada del piloto NVD. "
            "No representan un análisis completo "
            "de las CVE candidatas.",
            "",
        ])
    else:
        lineas.extend([
            "**Evaluación NVD no disponible.** "
            "No se encuentra el archivo del piloto.",
            "",
        ])



def generar_informe():
    activos = leer_inventario()
    hallazgos = priorizar_resultados()

    catalogo = json.loads(
        RUTA_CVES.read_text(encoding="utf-8")
    )

    # Consultar CISA utilizando la caché de 24 horas
    _, info_cisa = obtener_catalogo(forzar=False)

    estados = Counter(h["estado"] for h in hallazgos)
    prioridades = Counter(h["prioridad"] for h in hallazgos)

    ids_evaluados = {h["asset_id"] for h in hallazgos}
    sin_coincidencia = [
        a for a in activos
        if a["asset_id"] not in ids_evaluados
    ]

    fecha = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    lineas = [
        "# Informe de vulnerabilidades IT/OT",
        "",
        "**Entrepinares - Demostración formativa**",
        "",
        f"**Fecha de generación:** {fecha}",
        "**Modo:** Análisis bajo demanda con catálogo guardado",
        "**Inventario:** Completamente ficticio",
        "",
        "## 1. Alcance y fuentes",
        "",
        
        f"- Activos inventariados: {len(activos)}",
        f"- CVE con reglas de correlación: {catalogo['count']}",
        f"- Versión de la selección fija: "
        f"{catalogo['catalogVersion']}",
        f"- Fecha del catálogo de referencia: "
        f"{catalogo['dateReleased']}",
        "",
        "**Catálogo CISA completo:**",
        "",
        f"- CVE disponibles: {info_cisa['total_cves']}",
        f"- Versión: {info_cisa['catalog_version']}",
        f"- Última descarga: {info_cisa['ultima_descarga']}",
        f"- Modo de obtención: {info_cisa['modo']}",
        f"- Aviso: {info_cisa['aviso'] or 'Ninguno'}",
        "",
        "**Importante:** El análisis distingue tres niveles: "
        "cribado inicial del catálogo completo CISA KEV, "
        "evaluación parcial de versiones mediante NVD "
        "y correlación detallada de tres CVE mediante "
        "reglas específicas. Los resultados de cada nivel "
        "no son directamente equivalentes.",
        "",
        "## 2. Resumen ejecutivo - Reglas específicas",
        "",
        f"- Evaluaciones realizadas: **{len(hallazgos)}**",
        f"- Afectaciones confirmadas según inventario: "
        f"**{estados['confirmada']}**",
        f"- Posibles afectaciones: **{estados['posible']}**",
        f"- No aplicables: **{estados['no_aplicable']}**",
        f"- Prioridad alta: **{prioridades['alta']}**",
        f"- Prioridad media: **{prioridades['media']}**",
        f"- Sin prioridad para estas CVE: "
        f"**{prioridades['sin_prioridad']}**",
        "",
        "La inclusión en CISA KEV indica explotación conocida "
        "de una CVE, pero no demuestra explotación en un activo.",
        "",
        "## 3. Hallazgos priorizados",
        "",
        "| Activo | Tipo | Producto | Versión | CVE | "
        "Afectación | Prioridad |",
        "|---|---|---|---|---|---|---|",
    ]

    for h in hallazgos:
        lineas.append(
            f"| {limpiar(h['asset_id'])} "
            f"| {limpiar(h['tipo'])} "
            f"| {limpiar(h['producto'])} "
            f"| {limpiar(h['version'])} "
            f"| {limpiar(h['cve'])} "
            f"| {limpiar(h['estado'])} "
            f"| {limpiar(h['prioridad'])} |"
        )

    lineas.extend([
        "",
        "## 4. Evidencias y justificaciones",
        "",
    ])

    for h in hallazgos:
        lineas.extend([
            f"### {h['asset_id']} - {h['cve']}",
            "",
            f"- **Producto:** {h['producto']} {h['version']}",
            f"- **Centro:** {h['centro']}",
            f"- **Criticidad:** {h['criticidad']}",
            f"- **Afectación:** {h['estado']}",
            f"- **Prioridad:** {h['prioridad']}",
            f"- **Justificación:** {h['justificacion']}",
            f"- **Fuente:** {h['fuente']}",
            "",
        ])

    lineas.extend([
        "## 5. Activos sin coincidencias",
        "",
        "Los siguientes activos no coinciden con las "
        "tres CVE seleccionadas:",
        "",
    ])

    for a in sin_coincidencia:
        lineas.append(
            f"- **{a['asset_id']}**: "
            f"{a['producto']} {a['version']}"
        )

    lineas.extend([
        "",
        "Esto no significa que estén libres "
        "de otras vulnerabilidades.",
        "",
    ])

    anadir_analisis_ampliado(lineas)

    lineas.extend([
        "## 8. Recomendaciones",
        "",
        "1. Validar las versiones y configuraciones "
        "de los activos con afectación confirmada.",
        "2. Resolver las incertidumbres de los activos "
        "clasificados como posibles.",
        "3. Consultar los avisos oficiales de los "
        "fabricantes antes de planificar actualizaciones.",
        "4. Coordinar cualquier intervención en equipos OT "
        "con los responsables de operaciones.",
        "5. Actualizar la información del inventario "
        "y repetir el análisis cuando sea necesario.",
        "",
        "## 9. Limitaciones",
        "",
        "- Inventario ficticio: no representa sistemas reales.",
        "- Se utiliza una copia local de CISA KEV.",
        "- Solo tres CVE disponen de reglas específicas; el cribado CISA y el piloto NVD tienen alcances diferentes.",
        "- Las reglas implementadas cubren los escenarios "
        "de versión previstos en esta demostración.",
        "- La prioridad es orientativa, no una "
        "evaluación corporativa de riesgo.",
        "- No se realizan escaneos ni cambios en sistemas.",
        "- La afectación confirmada según inventario "
        "no demuestra explotación efectiva.",
        "",
    ])

    RUTA_INFORME.parent.mkdir(
        parents=True, exist_ok=True
    )

    RUTA_INFORME.write_text(
        "\n".join(lineas),
        encoding="utf-8",
    )

    return RUTA_INFORME


if __name__ == "__main__":
    ruta = generar_informe()

    print("INFORME GENERADO CORRECTAMENTE")
    print(f"Archivo: {ruta}")
