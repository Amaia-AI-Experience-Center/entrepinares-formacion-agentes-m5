from pathlib import Path
import asyncio
import json
import subprocess
import sys

from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

from fuente_kev import obtener_catalogo
from inventario import leer_inventario
from priorizacion import priorizar_resultados
from collections import Counter
from generar_informe import generar_informe
from generar_html import generar_html


@tool(approval_mode="never_require")
def consultar_cisa(
    forzar_actualizacion: bool = False,
) -> str:
    """
    Consulta el catálogo completo de vulnerabilidades CISA KEV.

    Utiliza una caché de 24 horas. Si el usuario solicita
    expresamente actualizar o descargar de nuevo,
    establece forzar_actualizacion=True.

    No analiza el inventario ni determina qué activos
    son vulnerables.
    """

    print(
        ">>> HERRAMIENTA CISA EJECUTADA "
        f"| Forzar: {forzar_actualizacion}"
    )

    catalogo, info = obtener_catalogo(
        forzar=forzar_actualizacion
    )

    resultado = {
        "modo": info["modo"],
        "version_catalogo": info["catalog_version"],
        "total_cves": info["total_cves"],
        "ultima_descarga": info["ultima_descarga"],
        "aviso": info["aviso"],
        "limitacion": (
            "Este es el catálogo CISA completo. "
            "El motor de correlación actual solo "
            "dispone de reglas para tres CVE."
        ),
    }

    return json.dumps(resultado, ensure_ascii=False)


@tool(approval_mode="never_require")
def consultar_activo(asset_id: str) -> str:
    """
    Busca un activo del inventario por su identificador,
    por ejemplo IT-005 u OT-001.

    Devuelve sus datos registrados.
    No realiza análisis de vulnerabilidades.
    """

    print(
        f">>> HERRAMIENTA INVENTARIO EJECUTADA "
        f"| Activo: {asset_id}"
    )

    activos = leer_inventario()

    for activo in activos:
        if activo["asset_id"].upper() == asset_id.strip().upper():
            return json.dumps(
                {"encontrado": True, "activo": activo},
                ensure_ascii=False,
            )

    return json.dumps(
        {
            "encontrado": False,
            "asset_id": asset_id,
            "mensaje": "No existe en el inventario.",
        },
        ensure_ascii=False,
    )


@tool(approval_mode="never_require")
def evaluar_activo(asset_id: str) -> str:
    """
    Evalúa las vulnerabilidades conocidas de un activo.

    Utiliza las reglas deterministas de correlación
    y priorización existentes.

    Úsala cuando el usuario pregunte si un activo
    está afectado, por qué, o qué prioridad tiene.
    """

    asset_id = asset_id.strip().upper()

    print(
        ">>> HERRAMIENTA EVALUACION EJECUTADA "
        f"| Activo: {asset_id}"
    )

    activos = {
        a["asset_id"]: a
        for a in leer_inventario()
    }

    if asset_id not in activos:
        return json.dumps({
            "encontrado": False,
            "mensaje": "Activo no encontrado."
        }, ensure_ascii=False)

    hallazgos = [
        h for h in priorizar_resultados()
        if h["asset_id"] == asset_id
    ]

    resultado = {
        "encontrado": True,
        "activo": activos[asset_id],
        "hallazgos": hallazgos,
        "total_evaluaciones": len(hallazgos),
        "alcance": (
            "Evaluación limitada a las tres CVE "
            "para las que existen reglas actualmente. "
            "El catálogo completo de CISA no está "
            "correlacionado automáticamente."
        ),
    }

    if not hallazgos:
        resultado["advertencia"] = (
            "Sin coincidencias entre las CVE evaluadas. "
            "Esto no demuestra ausencia de vulnerabilidades."
        )

    
    # Comprobar la vigencia de CISA antes de responder
    _, info_cisa = obtener_catalogo(forzar=False)

    resultado["estado_fuente_cisa"] = {
        "modo": info_cisa["modo"],
        "version": info_cisa["catalog_version"],
        "ultima_descarga": info_cisa["ultima_descarga"],
        "aviso": info_cisa["aviso"],
        "alcance": (
            "La vigencia del catálogo CISA se comprueba "
            "automáticamente, pero la evaluación utiliza "
            "las tres CVE con reglas implementadas."
        ),
    }

    print(
        f">>> CISA: {info_cisa['modo']} | "
        f"Versión: {info_cisa['catalog_version']}"
    )


    return json.dumps(
        resultado,
        ensure_ascii=False,
    )



@tool(approval_mode="never_require")
def analizar_inventario() -> str:
    """
    Analiza las vulnerabilidades del inventario completo.

    Devuelve estadísticas y hallazgos priorizados.
    No descarga CISA ni genera informes.

    Úsala para preguntas generales sobre el estado
    de vulnerabilidades del inventario IT/OT.
    """

    print(">>> HERRAMIENTA ANALISIS GLOBAL EJECUTADA")

    
    # Comprobar si hay que actualizar CISA.
    # La función utiliza caché si tiene menos de 24 horas.
    catalogo_actual, info_cisa = obtener_catalogo(
        forzar=False
    )

    print(
        f">>> CISA: {info_cisa['modo']} | "
        f"Versión: {info_cisa['catalog_version']}"
    )

    # Comprobar cuáles de nuestras CVE siguen en KEV.
    cves_actuales = {
        cve["cveID"]
        for cve in catalogo_actual["vulnerabilities"]
    }

    cves_evaluadas = [
        "CVE-2023-27350",
        "CVE-2024-3400",
        "CVE-2016-8562",
    ]

    estado_fuente = {
        "modo": info_cisa["modo"],
        "version": info_cisa["catalog_version"],
        "ultima_descarga": info_cisa["ultima_descarga"],
        "total_cves_cisa": info_cisa["total_cves"],
        "cves_evaluadas_presentes_en_kev": [
            cve for cve in cves_evaluadas
            if cve in cves_actuales
        ],
        "aviso": info_cisa["aviso"],
        "limitacion": (
            "El catálogo CISA completo está actualizado "
            "o se ha consultado su caché. "
            "La correlación sigue utilizando únicamente "
            "las tres CVE seleccionadas en kev_demo.json."
        ),
    }


    activos = leer_inventario()
    hallazgos = priorizar_resultados()

    estados = Counter(
        h["estado"] for h in hallazgos
    )

    prioridades = Counter(
        h["prioridad"] for h in hallazgos
    )

    ids_evaluados = {
        h["asset_id"] for h in hallazgos
    }

    sin_coincidencia = [
        a["asset_id"]
        for a in activos
        if a["asset_id"] not in ids_evaluados
    ]

    resultado = {
        "total_activos": len(activos),
        "total_evaluaciones": len(hallazgos),
        "estados": dict(estados),
        "prioridades": dict(prioridades),
        "hallazgos": hallazgos,
        "estado_fuente_cisa": estado_fuente,
        "activos_sin_coincidencia": sin_coincidencia,
        "alcance": (
            "Análisis basado en las tres CVE "
            "seleccionadas en datos/kev_demo.json. "
            "No evalúa todo el catálogo CISA KEV."
        ),
        "informes_generados": False,
    }

    return json.dumps(
        resultado,
        ensure_ascii=False,
    )




@tool(approval_mode="never_require")
def generar_informes() -> str:
    """
    Genera informes Markdown y HTML de vulnerabilidades IT/OT.

    Incluye tres niveles de análisis:
    - Correlación detallada de tres CVE con reglas específicas.
    - Cribado inicial del catálogo completo CISA KEV.
    - Evaluación técnica parcial NVD para PAN-OS.

    Utiliza los últimos resultados guardados del cribado
    y del piloto NVD. No vuelve a ejecutar esos análisis.

    Solo se ejecuta cuando el usuario solicita
    generar, crear o actualizar informes.
    """

    print(">>> HERRAMIENTA INFORMES EJECUTADA")

    try:
        ruta_md = generar_informe()
        print(f">>> MARKDOWN GENERADO: {ruta_md}")

        ruta_html = generar_html()
        print(f">>> HTML GENERADO: {ruta_html}")

        # Comprobar el contenido real de ambos archivos.
        texto_md = ruta_md.read_text(encoding="utf-8")
        texto_html = ruta_html.read_text(encoding="utf-8")

        verificacion = {
            "reglas_especificas": (
                "## 3. Hallazgos priorizados" in texto_md
                and "<h2>3. Hallazgos priorizados</h2>"
                in texto_html
            ),
            "cribado_cisa": (
                "- CVE candidatas distintas: **" in texto_md
                and "CVE candidatas distintas: <strong>"
                in texto_html
            ),
            "piloto_nvd": (
                "- CVE investigadas: **" in texto_md
                and "CVE investigadas: <strong>"
                in texto_html
            ),
        }

        contenido_completo = all(verificacion.values())

        resultado = {
            "exito": True,
            "markdown": str(ruta_md),
            "html": str(ruta_html),
            "contenido_completo": contenido_completo,
            "secciones_verificadas": verificacion,
            "mensaje": (
                "Ambos informes generados y los tres "
                "niveles de análisis verificados."
                if contenido_completo
                else
                "Ambos informes generados, pero falta "
                "algún nivel de análisis. Revisar los "
                "archivos de datos utilizados."
            ),
            "advertencia": (
                "El cribado CISA y el piloto NVD utilizan "
                "los resultados de sus últimas ejecuciones "
                "guardadas. No se recalculan al generar "
                "los informes."
            ),
        }

    except Exception as error:
        resultado = {
            "exito": False,
            "error": str(error),
            "mensaje": (
                "No se han podido generar o verificar "
                "correctamente ambos informes."
            ),
        }

    return json.dumps(
        resultado,
        ensure_ascii=False,
    )



@tool(approval_mode="never_require")
def consultar_cribado(
    asset_id: str = "",
    cve_id: str = "",
) -> str:
    """
    Consulta el cribado completo de CISA KEV.
    Permite consultar el resumen, un activo o una CVE.
    Las coincidencias NO confirman afectación.
    """

    print(
        ">>> HERRAMIENTA CRIBADO EJECUTADA | "
        f"Activo: {asset_id or 'todos'} | "
        f"CVE: {cve_id or 'todas'}"
    )

    ruta = (
        Path(__file__).resolve().parent
        / "datos"
        / "cribado_kev.json"
    )

    if not ruta.exists():
        return json.dumps({
            "error": (
                "No existe el cribado. "
                "Ejecutar primero cribado_kev.py"
            )
        }, ensure_ascii=False)

    datos = json.loads(
        ruta.read_text(encoding="utf-8")
    )

    aviso = (
        "Son coincidencias de fabricante o producto. "
        "No son vulnerabilidades confirmadas."
    )

    # Consulta global: devolver resumen, no cientos de filas.
    if not asset_id.strip() and not cve_id.strip():
        return json.dumps({
            "resumen": datos["resumen"],
            "fuente": datos["fuente"],
            "advertencia": aviso,
        }, ensure_ascii=False)

    activo = asset_id.strip().upper()
    cve = cve_id.strip().upper()

    def filtrar(registros):
        return [
            r for r in registros
            if (
                not activo
                or r["asset_id"].upper() == activo
            )
            and (
                not cve
                or r["cve"].upper() == cve
            )
        ]

    candidatos = filtrar(datos["candidatos"])
    pendientes = filtrar(
        datos["pendientes_fabricante"]
    )

    def resumir(registros, limite):
        return [
            {
                "activo": r["asset_id"],
                "cve": r["cve"],
                "producto": r["producto_inventario"],
                "version": r["version_inventario"],
                "producto_cisa": r["producto_cisa"],
                "categoria": r["categoria"],
            }
            for r in registros[:limite]
        ]

    return json.dumps({
        "filtros": {
            "asset_id": activo or None,
            "cve_id": cve or None,
        },
        "total_candidatos": len(candidatos),
        "candidatos_mostrados": resumir(
            candidatos, 20
        ),
        "total_solo_fabricante": len(pendientes),
        "pendientes_mostrados": resumir(
            pendientes, 5
        ),
        "resultados_recortados": (
            len(candidatos) > 20
            or len(pendientes) > 5
        ),
        "advertencia": aviso,
    }, ensure_ascii=False)



@tool(approval_mode="never_require")
def consultar_nvd_piloto(
    asset_id: str = "",
    cve_id: str = "",
) -> str:
    """
    Consulta los resultados del piloto NVD para PAN-OS.
    No confirma explotación ni cubre todo el inventario.
    """

    print(
        ">>> HERRAMIENTA NVD PILOTO EJECUTADA | "
        f"Activo: {asset_id or 'todos'} | "
        f"CVE: {cve_id or 'todas'}"
    )

    ruta = (
        Path(__file__).resolve().parent
        / "datos"
        / "evaluacion_nvd_piloto.json"
    )

    if not ruta.exists():
        return json.dumps({
            "error": "No existe la evaluación NVD piloto."
        }, ensure_ascii=False)

    datos = json.loads(
        ruta.read_text(encoding="utf-8")
    )

    resultados = datos.get("resultados", [])

    activo = asset_id.strip().upper()
    cve = cve_id.strip().upper()

    filtrados = [
        r for r in resultados
        if (not activo or r["asset_id"] == activo)
        and (not cve or r["cve"] == cve)
    ]

    def contar_estados(registros):
        return {
            estado: sum(
                r["estado"] == estado
                for r in registros
            )
            for estado in (
                "coincidencia_cpe",
                "fuera_criterios_nvd",
                "pendiente_revision",
            )
        }

    respuesta = {
        "alcance": "Piloto NVD exclusivo de PAN-OS",
        "cves_procesadas": datos.get("cves_procesadas", 0),
        "total_evaluaciones": len(resultados),
        "resumen_global": contar_estados(resultados),
        "filtro_activo": activo or None,
        "filtro_cve": cve or None,
        "evaluaciones_filtradas": len(filtrados),
        "resumen_filtrado": contar_estados(filtrados),
        "detalles": (
            filtrados[:20] if activo or cve else []
        ),
        "resultados_recortados": len(filtrados) > 20,
        "errores": datos.get("errores", []),
        "advertencia": (
            "Análisis NVD parcial. Una coincidencia CPE "
            "no confirma afectación explotable. "
            "Fuera de criterios NVD no significa "
            "que el equipo esté libre de vulnerabilidades. "
            "Las evaluaciones pendientes requieren revisión."
        ),
    }

    return json.dumps(
        respuesta, ensure_ascii=False
    )



@tool(approval_mode="never_require")
def consultar_novedades_kev() -> str:
    """
    Consulta las novedades de CISA KEV detectadas
    desde la versión de referencia guardada.

    Lee la última comparación almacenada.
    No descarga CISA ni actualiza la referencia.
    Las coincidencias con activos son preliminares.
    """

    print(">>> HERRAMIENTA NOVEDADES CISA EJECUTADA")

    ruta = (
        Path(__file__).resolve().parent
        / "datos"
        / "novedades_kev.json"
    )

    if not ruta.exists():
        return json.dumps({
            "error": (
                "No existe una comparación guardada. "
                "Ejecutar primero novedades_kev.py."
            )
        }, ensure_ascii=False)

    datos = json.loads(
        ruta.read_text(encoding="utf-8")
    )

    nuevas = datos.get("nuevas", [])

    respuesta = {
        "fecha_comparacion": datos.get("fecha_comparacion"),
        "version_referencia": datos.get("version_referencia"),
        "version_actual": datos.get("version_actual"),
        "modo_fuente": datos.get("modo_fuente"),
        "resumen": datos.get("resumen", {}),
        "nuevas": nuevas[:20],
        "nuevas_recortadas": len(nuevas) > 20,
        "modificadas": datos.get("modificadas", [])[:20],
        "retiradas": datos.get("retiradas", [])[:20],
        "coincidencias_inventario": datos.get(
            "coincidencias_inventario", {}
        ),
        "advertencia": (
            "Resultados de la última comparación guardada. "
            "No se ha ejecutado una nueva actualización. "
            "Las coincidencias de producto o fabricante "
            "no confirman afectación de los activos."
        ),
    }

    return json.dumps(
        respuesta,
        ensure_ascii=False,
    )


@tool(approval_mode="never_require")
def actualizar_novedades_kev(
    forzar_descarga: bool = True,
) -> str:
    """
    Actualiza bajo demanda la comparación de CISA KEV.

    Por defecto descarga de nuevo el catálogo.
    Compara contra la última referencia confirmada.
    No modifica ni avanza esa referencia.
    """

    print(
        ">>> HERRAMIENTA ACTUALIZACIÓN NOVEDADES EJECUTADA"
    )

    base = Path(__file__).resolve().parent
    ruta_resultados = base / "datos" / "novedades_kev.json"

    modificacion_anterior = (
        ruta_resultados.stat().st_mtime_ns
        if ruta_resultados.exists()
        else None
    )

    comando = [
        sys.executable,
        str(base / "novedades_kev.py"),
    ]

    if forzar_descarga:
        comando.append("--forzar")

    try:
        proceso = subprocess.run(
            comando,
            cwd=base,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )

        if proceso.returncode != 0:
            return json.dumps({
                "exito": False,
                "error": (
                    proceso.stderr.strip()
                    or proceso.stdout.strip()
                )[-1500:],
                "mensaje": (
                    "No se ha completado la actualización. "
                    "No utilizar resultados anteriores "
                    "como si fueran nuevos."
                ),
            }, ensure_ascii=False)

        if not ruta_resultados.exists():
            raise RuntimeError(
                "No se ha generado el archivo de novedades."
            )

        if (
            modificacion_anterior is not None
            and ruta_resultados.stat().st_mtime_ns
            <= modificacion_anterior
        ):
            raise RuntimeError(
                "El archivo de novedades no se ha actualizado."
            )

        datos = json.loads(
            ruta_resultados.read_text(encoding="utf-8")
        )

        if (
            forzar_descarga
            and datos.get("modo_fuente") != "descarga"
        ):
            raise RuntimeError(
                "No se ha confirmado una descarga nueva."
            )

        coincidencias = datos.get(
            "coincidencias_inventario", {}
        )

        respuesta = {
            "exito": True,
            "version_referencia": datos["version_referencia"],
            "version_actual": datos["version_actual"],
            "modo_fuente": datos["modo_fuente"],
            "resumen": datos["resumen"],
            "nuevas": datos.get("nuevas", [])[:20],
            "coincidencias_inventario": coincidencias,
            "referencia_actualizada": False,
            "advertencia": (
                "La comparación se ha actualizado, "
                "pero la referencia histórica permanece "
                "sin cambios. Las coincidencias no "
                "confirman vulnerabilidades."
            ),
        }

        return json.dumps(
            respuesta, ensure_ascii=False
        )

    except Exception as error:
        return json.dumps({
            "exito": False,
            "error": str(error),
        }, ensure_ascii=False)

        
@tool(approval_mode="never_require")
def consultar_historial_novedades_kev() -> str:
    """
    Consulta las comparaciones históricas de CISA KEV.
    No descarga información ni modifica referencias.
    """

    print(">>> HERRAMIENTA HISTORIAL CISA EJECUTADA")

    carpeta = (
        Path(__file__).resolve().parent
        / "datos"
        / "historial_kev"
    )

    historial = []

    for archivo in carpeta.glob("novedades_*_a_*.json"):
        datos = json.loads(
            archivo.read_text(encoding="utf-8")
        )

        historial.append({
            "fecha_comparacion": datos.get("fecha_comparacion"),
            "version_referencia": datos.get("version_referencia"),
            "version_actual": datos.get("version_actual"),
            "resumen": datos.get("resumen", {}),
            "nuevas": datos.get("nuevas", []),
            "coincidencias_inventario": datos.get(
                "coincidencias_inventario", {}
            ),
        })

    historial.sort(
        key=lambda r: r.get("fecha_comparacion") or "",
        reverse=True,
    )

    return json.dumps({
        "total_comparaciones_archivadas": len(historial),
        "comparaciones": historial[:10],
        "advertencia": (
            "Son resultados históricos ya procesados. "
            "Las coincidencias con inventario "
            "no confirman vulnerabilidades."
        ),
    }, ensure_ascii=False)



async def main(modo_evaluacion: bool = False):

    import os  # copia didactica portable: configuracion desde el entorno

    client = FoundryChatClient(
        project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT", ""),
        model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini"),
        credential=AzureCliCredential(),
    )

    agente = Agent(
        client=client,
        name="AgenteVulnerabilidadesMulti",        
        instructions=(
            "Eres un agente especializado en análisis de "
            "vulnerabilidades de ciberseguridad IT/OT. "
            "Trabajas con un inventario ficticio de Entrepinares. "
            "Responde siempre en español, con precisión técnica "
            "y explicaciones claras. "
            "No inventes datos, evidencias ni resultados.\n\n"

            "SELECCIÓN DE HERRAMIENTAS:\n"

            "- Usa consultar_activo cuando el usuario solicite "
            "únicamente información del inventario sobre "
            "un activo concreto.\n"

            "- Usa evaluar_activo cuando pregunte por "
            "vulnerabilidades, afectación, prioridad o "
            "justificación técnica de un activo. "
            "Esta herramienta utiliza las tres reglas "
            "de correlación originales.\n"

            "- Usa analizar_inventario para consultar "
            "las evaluaciones de vulnerabilidad realizadas "
            "mediante esas tres reglas sobre el inventario.\n"

            "- Usa consultar_cribado cuando el usuario pregunte "
            "por el cribado completo de CISA KEV, CVE candidatas, "
            "coincidencias de productos o coincidencias de "
            "un activo con el catálogo completo.\n"

            "- Usa consultar_cisa cuando soliciten información "
            "general del catálogo CISA, su versión, actualización "
            "o estado de la fuente. "
            "Si solicitan expresamente actualizarlo, utiliza "
            "forzar_actualizacion=True.\n"

            "- Usa generar_informes cuando el usuario solicite "
            "generar los informes Markdown y HTML. "
            "No afirmes haberlos generado si no se ha ejecutado "
            "correctamente la herramienta.\n\n"

            "INTERPRETACIÓN DE RESULTADOS:\n"

            "- El catálogo CISA KEV completo se ha utilizado "
            "para realizar un cribado inicial contra "
            "el inventario ficticio.\n"

            "- El cribado identifica CVE candidatas mediante "
            "coincidencias de fabricante, producto o familia. "
            "No demuestra que las versiones instaladas "
            "estén afectadas.\n"

            "- Distingue las coincidencias de producto o familia "
            "de las coincidencias únicamente de fabricante. "
            "Estas últimas requieren una revisión adicional.\n"

            "- Las tres reglas originales realizan una evaluación "
            "más detallada de versiones y configuraciones. "
            "No afirmes que esas reglas cubren todas las CVE "
            "del catálogo completo.\n"

            "- Respeta los estados, prioridades, justificaciones "
            "y limitaciones devueltos por Python. "
            "No transformes una coincidencia candidata "
            "en afectación confirmada.\n"

            "- Si el usuario solicita una visión completa, "
            "puedes combinar analizar_inventario y "
            "consultar_cribado, diferenciando claramente "
            "los resultados de ambas herramientas.\n"

            "- No confundas una versión afectada con "
            "explotación efectiva de un equipo. "
            "No consideres seguro un activo por no presentar "
            "coincidencias o por tener evaluaciones pendientes.\n"

            "- No afirmes que se han verificado las versiones "
            "de todas las CVE candidatas. "
            "El análisis NVD ampliado sigue siendo parcial "
            "y todavía no está integrado en las herramientas "
            "conversacionales del agente.\n\n"

            "GESTIÓN DE FUENTES Y CACHÉ:\n"

            "- Las herramientas evaluar_activo y "
            "analizar_inventario ya proporcionan información "
            "sobre la versión y vigencia del catálogo CISA. "
            "No llames adicionalmente a consultar_cisa "
            "cuando esos datos sean suficientes.\n"

            "- Cuando CISA indique modo cache, explica que "
            "los datos proceden de una copia local vigente "
            "según la política de actualización de 24 horas, "
            "y no de una consulta en directo.\n"

            "- Comunica cualquier aviso de descarga fallida "
            "o de caché desactualizada.\n"

            "- Para los resultados del cribado, utiliza "
            "los recuentos y la versión de catálogo devueltos "
            "por consultar_cribado. "
            "No presupongas que esos resultados están "
            "actualizados si no se ha regenerado el cribado.\n\n"

            "EFICIENCIA Y FIABILIDAD:\n"

            "- Selecciona únicamente las herramientas "
            "necesarias para responder a cada petición.\n"

            "- Evita consultas redundantes y reutiliza "
            "los resultados disponibles durante "
            "la conversación cuando sigan siendo válidos.\n"

            "- Si falta información para establecer "
            "una conclusión, indícalo expresamente "
            "y explica qué sería necesario comprobar.\n"

            "- Diferencia siempre entre datos del inventario, "
            "coincidencias candidatas, evaluaciones técnicas "
            "y vulnerabilidades confirmadas según la evidencia."

            "- Usa consultar_nvd_piloto cuando se pidan "
            "expresamente los resultados de evaluación NVD "
            "o de versiones investigadas en el piloto PAN-OS. "
            "Es un análisis parcial y no cubre las 194 CVE "
            "candidatas ni todos los productos del inventario.\n"

            "- Diferencia los estados coincidencia_cpe, "
            "fuera_criterios_nvd y pendiente_revision. "
            "No los transformes automáticamente en "
            "vulnerabilidades confirmadas o equipos seguros.\n"

            "- Usa consultar_novedades_kev cuando el usuario "
            "pregunte qué CVE nuevas se han detectado "
            "desde la referencia CISA guardada o cuáles "
            "coinciden con el inventario. "
            "Aclara que procede de la última comparación "
            "almacenada, no necesariamente de una descarga "
            "realizada en ese momento. "
            "No confundas coincidencias candidatas "
            "con vulnerabilidades confirmadas.\n"

            "- Usa actualizar_novedades_kev cuando el usuario "
            "pida expresamente comprobar ahora, actualizar "
            "o descargar nuevas vulnerabilidades de CISA. "
            "Utiliza consultar_novedades_kev cuando solo "
            "quiera consultar los resultados guardados. "
            "Actualizar la comparación no significa "
            "confirmar ni avanzar la referencia histórica. "
            "Si falla la actualización, no presentes "
            "resultados antiguos como actuales.\n"

            "- Usa consultar_historial_novedades_kev cuando "
            "el usuario pregunte por CVE nuevas detectadas "
            "en revisiones anteriores, comparaciones "
            "archivadas o novedades ya procesadas. "
            "No confundas el historial con la última "
            "comparación disponible.\n"
        ),
        tools=[
            consultar_cisa,
            consultar_activo,
            evaluar_activo,
            analizar_inventario,
            generar_informes,
            consultar_cribado,
            consultar_nvd_piloto,
            consultar_novedades_kev,
            actualizar_novedades_kev,
            consultar_historial_novedades_kev,
        ],
    )

        # Permitir reutilizar el agente en pruebas automáticas.
    if modo_evaluacion:
        return agente, client

    # Crear una sesión para mantener el contexto
    session = agente.create_session()

    print("\nAGENTE DE VULNERABILIDADES IT/OT")
    print("Conversación interactiva iniciada.")
    print("Escribe 'salir' para terminar.")
    print("Escribe '/nueva' para iniciar otra conversación.")

    while True:
        try:
            pregunta = input("\nTú > ").strip()

        except (KeyboardInterrupt, EOFError):
            print("\nConversación finalizada.")
            break

        if not pregunta:
            continue

        if pregunta.lower() in ("salir", "exit"):
            print("Conversación finalizada.")
            break

        if pregunta.lower() == "/nueva":
            session = agente.create_session()
            print("Nueva conversación iniciada.")
            continue

        try:
            respuesta = await agente.run(
                pregunta,
                session=session,
            )

            print("\nAGENTE:")
            print(respuesta.text)

        except Exception as error:
            print(f"\nERROR: {error}")



if __name__ == "__main__":
    asyncio.run(main())