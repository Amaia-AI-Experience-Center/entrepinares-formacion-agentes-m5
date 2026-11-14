# Entrepinares - Workflow alternativo A: tres agentes y un ejecutor final
# Grafo directo: Orquestador -> Correlacion -> Criticidad -> RespuestaFinal
# Variante EXPERIMENTAL de la PoC; NO reemplazar la version consolidada.
#
# SEGURIDAD / ALCANCE:
# - Consola: actualizar CISA y generar informes requieren APROBACION HUMANA
#   por solicitud Y su respectivo flag --habilitar-*-reales. Por defecto NO
#   se realizan escrituras aunque el usuario apruebe.
# - DevUI: solo lectura. No expone herramientas de escritura ni admite
#   aprobaciones para ejecutarlas. Usar --sin-auth solo en localhost.
# - Consultas: nunca descargan CISA de forma implicita en este proceso.
# - Ambas operaciones reales conservan respaldos y bloqueos de concurrencia
#   locales, pero NO restauran automaticamente en caso de error.
# - Inventario ficticio: no hay conexion a los sistemas reales de Entrepinares.
# - No se ha validado despliegue Hosted, concurrencia entre otros scripts o
#   restauracion. La consola de esta variante NO ha sido validada aun con Foundry.
#
# Dependencias del proyecto existentes en el mismo directorio:
#   agente_multiherramienta.py, fuente_kev.py, inventario.py,
#   priorizacion.py, cribado_kev.py, novedades_kev.py,
#   generar_informe.py, generar_html.py y los JSON de datos/.

"""Workflow multiagente didactico de tres agentes y un solo nodo final.

VARIANTE EXPERIMENTAL: conserva orquestacion_entrepinares.py original sin cambios.

Las decisiones del Orquestador se transmiten de forma estructurada entre
agentes; las aristas condicionales ejecutan esas decisiones. Los filtros de
contexto de AgentExecutor preparan el contenido que necesita cada agente,
sin introducir los ejecutores PrepararCorrelacion ni PuenteCorrelacion.

Se conservan las aprobaciones humanas y flags independientes para escritura.
La generacion de informes y actualizacion CISA siguen sin rollback automatico.

Rutas posibles (cuatro nodos visibles en DevUI):

  AgenteOrquestador -------------------------------> RespuestaFinal
       |               (respuesta directa)
       v
  AgenteCorrelacion --------(solo correlacion)----> RespuestaFinal
       |
       |               (analisis avanzado)
       v
  AgenteCriticidad -------------------------------> RespuestaFinal

Uso:
    .venv\\Scripts\\python.exe orquestacion_entrepinares_sin_puentes.py consola -q "..."
    .venv\\Scripts\\python.exe orquestacion_entrepinares_sin_puentes.py devui
"""

import argparse
import asyncio
import json
import sys
import os
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from agent_framework import (
    Agent,
    AgentExecutor,
    AgentExecutorResponse,
    Message,
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    tool,
)
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from pydantic import BaseModel, Field
from typing_extensions import Never

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import fuente_kev  # noqa: E402
from inventario import leer_inventario  # noqa: E402
# Se importa la herramienta original, pero no se registra directamente en
# ningun agente: approval_mode="never_require" no ofrece proteccion.
# Solo la invoca nuestro wrapper aprobado y con habilitacion explicita.
from agente_multiherramienta import (  # noqa: E402
    analizar_inventario,
    consultar_activo,
    consultar_cisa,
    consultar_cribado as _consultar_cribado_original,
    consultar_historial_novedades_kev,
    consultar_novedades_kev,
    consultar_nvd_piloto,
    evaluar_activo,
    actualizar_novedades_kev as _actualizar_novedades_original,
    generar_informes as _generar_informes_original,
)

# COPIA DIDACTICA PORTABLE: el endpoint del proyecto Foundry ya no esta fijado
# en el codigo; se lee de la variable de entorno FOUNDRY_PROJECT_ENDPOINT
# (ver .env.example y docs/CAMBIOS_RESPECTO_AL_ORIGINAL.md). El modelo sigue
# siendo gpt-4.1-mini por defecto (AZURE_AI_MODEL_DEPLOYMENT_NAME lo cambia).
PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1-mini")

ID_ORQUESTADOR = "AgenteOrquestador"
ID_CORRELACION = "AgenteCorrelacion"
ID_CRITICIDAD = "AgenteCriticidad"


# ---------------------------------------------------------------------------
# Contratos tipados
# ---------------------------------------------------------------------------

class DecisionOrquestador(BaseModel):
    """Salida estructurada del orquestador (la ruta no se deduce de texto libre)."""

    ruta: Literal["respuesta_directa", "correlacion", "analisis_avanzado"] = Field(
        description="Ruta a seguir en el workflow."
    )
    asset_id: str | None = Field(
        description="Identificador del activo mencionado (p. ej. IT-004) o null."
    )
    cve_id: str | None = Field(
        description="CVE mencionada expresamente por el usuario o null."
    )
    accion_explicita: Literal["ninguna", "actualizar_novedades", "generar_informes"] = Field(
        description=(
            "Solo si el usuario pide EXPRESAMENTE actualizar/descargar novedades "
            "CISA o generar informes. En cualquier otro caso: ninguna. "
            "Generar informes y actualizar CISA requieren aprobacion humana "
            "y habilitacion explicita e independiente en consola."
        )
    )
    respuesta_directa: str | None = Field(
        description=(
            "Respuesta final en espanol cuando ruta=respuesta_directa, basada solo "
            "en la herramienta consultar_activo. Null en las demas rutas. "
            "Si falta, el ejecutor RespuestaFinal recurrira exclusivamente "
            "al inventario local verificado, sin inventar datos."
        )
    )
    motivo: str = Field(description="Justificacion breve de la ruta elegida.")

    # La presencia de un texto para respuesta_directa se comprueba en
    # RespuestaFinal. Validarla aqui interrumpe FoundryChatClient ANTES de
    # entrar en el grafo, impidiendo una recuperacion segura.


# ---------------------------------------------------------------------------
# Permisos y operaciones bajo demanda
# ---------------------------------------------------------------------------
# Respuesta defensiva si el orquestador toma una ruta directa para una accion.
def _mensaje_accion_no_ejecutada(accion: str) -> str:
    etiqueta = {
        "actualizar_novedades": "actualizar las novedades de CISA KEV",
        "generar_informes": "generar informes HTML y Markdown",
    }.get(accion, accion)
    return (
        f"La operacion solicitada ({etiqueta}) no se ha ejecutado. "
        "En DevUI esta version funciona solo en modo lectura: las acciones "
        "con escritura se realizan exclusivamente por consola, con el flag "
        "de habilitacion correspondiente y aprobacion humana individual. "
        "Esta solicitud no ha ejecutado ninguna herramienta de escritura."
    )


ARCHIVOS_VIGILADOS = (
    BASE / "datos" / "cisa_kev_cache.json",
    BASE / "datos" / "novedades_kev.json",
    BASE / "datos" / "historial_kev" / "catalogo_referencia.json",
    BASE / "informes" / "informe_vulnerabilidades.md",
    BASE / "informes" / "informe_vulnerabilidades.html",
)


def _huella(ruta: Path) -> str | None:
    """Huella para comprobar que una prueba rechazada no ha alterado ficheros."""
    if not ruta.exists():
        return None
    h = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def _huellas_vigiladas() -> dict[str, str | None]:
    return {str(ruta.relative_to(BASE)): _huella(ruta) for ruta in ARCHIVOS_VIGILADOS}


def _ejecutar_actualizacion_real() -> str:
    """Bloqueo local + respaldo antes de reutilizar la herramienta existente.

    Nota: el bloqueo solo coordina las ejecuciones de ESTE nuevo script; otros
    programas que escriban los mismos ficheros sin respetarlo siguen siendo riesgo.
    """
    carpeta = BASE / "datos"
    candado = carpeta / ".actualizacion_cisa_controlada.lock"
    try:
        fd = os.open(str(candado), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return json.dumps({
            "exito": False,
            "mensaje": "Actualizacion abortada: otra ejecucion controlada tiene el bloqueo.",
            "candado": str(candado),
        }, ensure_ascii=False)
    except OSError as e:
        return json.dumps({"exito": False, "error": f"No se puede crear bloqueo: {e}"}, ensure_ascii=False)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\n")

        sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        respaldos = carpeta / "respaldos_kev" / sello
        respaldos.mkdir(parents=True, exist_ok=False)
        for ruta in ARCHIVOS_VIGILADOS[:3]:
            if ruta.is_file():
                destino = respaldos / ruta.relative_to(carpeta)
                destino.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ruta, destino)

        huella_referencia = _huella(ARCHIVOS_VIGILADOS[2])
        # Se lanza un subproceso nuevo; NO hereda el parche de descargas
        # implicitas del workflow padre.
        bruto = _actualizar_novedades_original.func(forzar_descarga=True)
        resultado = json.loads(bruto)
        resultado["directorio_respaldo"] = str(respaldos)
        if _huella(ARCHIVOS_VIGILADOS[2]) != huella_referencia:
            resultado["exito"] = False
            resultado["alerta_grave"] = "La referencia historica ha cambiado; investigar y restaurar respaldo."
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"exito": False, "error": str(e)}, ensure_ascii=False)
    finally:
        try:
            candado.unlink(missing_ok=True)
        except OSError:
            print(f"ADVERTENCIA: no se pudo eliminar el candado {candado}")


def crear_herramienta_actualizacion(permitir_escrituras: bool):
    """La habilitacion es INMUTABLE por instancia, no un permiso global mutable."""

    @tool(approval_mode="always_require", name="actualizar_novedades_cisa_controlada")
    def actualizar_novedades_cisa_controlada() -> str:
        """Solicita aprobacion para actualizar CISA KEV bajo demanda.

        Siempre requiere autorizacion humana. En modo por defecto las escrituras
        estan bloqueadas incluso si se aprueba. Con habilitacion explicita
        respalda archivos y descarga CISA mediante el script original.
        """
        if not permitir_escrituras:
            print("\n>>> ACTUALIZACION BLOQUEADA: modo sin escrituras")
            return json.dumps({
                "exito": False,
                "modo": "solo_prueba",
                "mensaje": "Herramienta aprobada, pero escrituras DESHABILITADAS por defecto.",
                "descarga_realizada": False,
                "archivos_modificados": False,
            }, ensure_ascii=False)
        print("\n>>> ACTUALIZACION REAL AUTORIZADA: se inicia subprocess original")
        return _ejecutar_actualizacion_real()

    return actualizar_novedades_cisa_controlada


def _ejecutar_informes_reales() -> str:
    """Genera informes con respaldo, candado y verificacion del resultado.

    No hay restauracion automatica en esta primera PoC. Si la generacion falla
    despues de escribir MD, se pueden mezclar versiones de MD y HTML; los
    archivos anteriores estan respaldados en informes/respaldos_informes.
    """
    carpeta = BASE / "informes"
    carpeta.mkdir(parents=True, exist_ok=True)
    candado = carpeta / ".generacion_informes_controlada.lock"
    try:
        fd = os.open(str(candado), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        return json.dumps({
            "exito": False,
            "mensaje": "Generacion abortada: otra ejecucion controlada posee el bloqueo.",
            "candado": str(candado),
        }, ensure_ascii=False)
    except OSError as e:
        return json.dumps({"exito": False, "error": f"No se puede crear bloqueo: {e}"}, ensure_ascii=False)

    respaldos = None
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"pid={os.getpid()}\n")

        sello = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        respaldos = carpeta / "respaldos_informes" / sello
        respaldos.mkdir(parents=True, exist_ok=False)
        for ruta in ARCHIVOS_VIGILADOS[3:]:
            if ruta.is_file():
                shutil.copy2(ruta, respaldos / ruta.name)

        # La herramienta original llama primero generar_informe() y despues
        # generar_html(). El parche bloquear_descargas_cisa() evita descargas
        # implicitas en este proceso: si la cache vencio, se marca desactualizada.
        bruto = _generar_informes_original.func()
        resultado = json.loads(bruto)
        resultado["directorio_respaldo"] = str(respaldos)
        resultado["descarga_cisa_forzada"] = False
        resultado["verificacion_completa"] = bool(
            resultado.get("exito") and resultado.get("contenido_completo")
        )
        if not resultado["verificacion_completa"]:
            resultado["advertencia_control"] = (
                "Revisar ambos informes antes de utilizarlos: se ha detectado "
                "un error o no se han validado todas las secciones. "
                "Los respaldos se conservan y NO se restauran automaticamente."
            )
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "exito": False,
            "error": str(e),
            "directorio_respaldo": str(respaldos) if respaldos else None,
            "advertencia_control": "No se realiza restauracion automatica.",
        }, ensure_ascii=False)
    finally:
        try:
            candado.unlink(missing_ok=True)
        except OSError:
            print(f"ADVERTENCIA: no se pudo eliminar el candado {candado}")


def crear_herramienta_informes(permitir_informes: bool):
    """Aprobacion de herramienta + permiso independiente e inmutable."""

    @tool(approval_mode="always_require", name="generar_informes_controlados")
    def generar_informes_controlados() -> str:
        """Solicita aprobacion antes de generar Markdown y HTML.

        Sin --habilitar-informes-reales no escribe nada aunque se apruebe.
        Al habilitarlo, guarda copia de ambos informes antes de reemplazarlos.
        """
        if not permitir_informes:
            print("\n>>> INFORMES BLOQUEADOS: modo sin escrituras")
            return json.dumps({
                "exito": False,
                "modo": "solo_prueba",
                "mensaje": "Aprobacion recibida; generacion real de informes DESHABILITADA.",
                "archivos_modificados": False,
            }, ensure_ascii=False)
        print("\n>>> INFORMES REALES AUTORIZADOS: generacion iniciada")
        return _ejecutar_informes_reales()

    return generar_informes_controlados


@tool(approval_mode="never_require", name="consultar_cribado")
def consultar_cribado(asset_id: str = "", cve_id: str = "") -> str:
    """
    Consulta el cribado almacenado de CISA KEV (solo lectura) para un activo
    y/o una CVE, con los resultados separados en dos apartados:
    coincidencias candidatas por producto/familia y coincidencias solo por
    fabricante (otro producto del mismo fabricante). Ninguna confirma
    afectacion. Sin filtros devuelve el resumen global.
    """
    bruto = json.loads(_consultar_cribado_original.func(asset_id, cve_id))

    # Resumen global, errores o fichero ausente: se devuelven tal cual.
    if "candidatos_mostrados" not in bruto:
        return json.dumps(bruto, ensure_ascii=False)

    def desglose(filas):
        por_producto: dict[str, int] = {}
        for f in filas:
            por_producto[f["producto_cisa"]] = por_producto.get(f["producto_cisa"], 0) + 1
        return por_producto

    cand = bruto["candidatos_mostrados"]
    solo_fab = bruto["pendientes_mostrados"]
    cand_recortado = bruto["total_candidatos"] > len(cand)
    fab_recortado = bruto["total_solo_fabricante"] > len(solo_fab)

    return json.dumps({
        "filtros": bruto["filtros"],
        "activo_inventario": (
            {
                "asset_id": cand[0]["activo"],
                "producto": cand[0]["producto"],
                "version_registrada": cand[0]["version"],
            } if cand else None
        ),
        "metodo": (
            "Comparacion de FABRICANTE y PRODUCTO/FAMILIA. NO se ha validado la "
            "version instalada contra las versiones afectadas de cada CVE."
        ),
        "A_coincidencias_candidatas_producto_o_familia": {
            "total": bruto["total_candidatos"],
            "desglose_por_producto_cisa": None if cand_recortado else desglose(cand),
            "cves_mostradas": cand,
            "lista_recortada": cand_recortado,
            "significado": "Candidatas pendientes de revision. NO son vulnerabilidades confirmadas.",
        },
        "B_coincidencias_solo_fabricante_otro_producto": {
            "total": bruto["total_solo_fabricante"],
            "desglose_por_producto_cisa": None if fab_recortado else desglose(solo_fab),
            "cves_mostradas": solo_fab,
            "lista_recortada": fab_recortado,
            "significado": (
                "Mismo fabricante pero OTRO producto (p. ej. Expedition). "
                "No son candidatas del producto del activo; presentar aparte."
            ),
        },
        "advertencia": bruto["advertencia"],
    }, ensure_ascii=False)


@tool(approval_mode="never_require", name="consultar_cisa")
def consultar_cisa_solo_lectura() -> str:
    """Consulta solo la version y vigencia de CISA KEV, sin descarga forzada.

    La proteccion frente a la renovacion automatica de una cache caducada
    depende de bloquear_descargas_cisa(), ejecutada al crear el workflow.
    """
    return consultar_cisa.func(forzar_actualizacion=False)


def bloquear_descargas_cisa() -> None:
    """Impide descargas implicitas de CISA en ESTE proceso.

    ``evaluar_activo`` y ``consultar_cisa`` llaman a ``obtener_catalogo()``,
    que descarga y reescribe la cache si tiene >24 h. Aqui se sustituye
    ``fuente_kev.descargar_catalogo`` por un fallo, con lo que
    ``obtener_catalogo`` devuelve la cache existente como "cache_desactualizada".

    LIMITACIONES:
    - Es un parche global de modulo: afecta a todo el proceso Python (no solo
      al workflow) y no se revierte. No modifica ningun fichero.
    - Si no existe una cache valida, ``obtener_catalogo`` lanza RuntimeError y
      la herramienta fallara.
    - Con cache caducada los datos pueden estar desactualizados (la herramienta
      lo indica en ``aviso``); no hay forma de refrescarlos desde aqui.
    - ``consultar_cisa(forzar_actualizacion=True)`` no descarga: devuelve la
      cache con aviso.
    - Es una salvaguarda de esta PoC, no un control de seguridad: otros
      modulos que usen urllib directamente no quedan cubiertos.
    """

    def _sin_red():
        raise RuntimeError("Descarga CISA desactivada en el workflow experimental.")

    fuente_kev.descargar_catalogo = _sin_red


# ---------------------------------------------------------------------------
# Instrucciones de los agentes
# ---------------------------------------------------------------------------

REGLAS_COMUNES = (
    "Trabajas con un inventario FICTICIO de Entrepinares; no hay escaneo real "
    "de equipos ni monitorizacion. Responde siempre en espanol. "
    "No inventes cantidades, estados ni prioridades: usa solo lo que devuelven "
    "las herramientas. Una coincidencia con CISA KEV es una coincidencia "
    "candidata, no una afectacion confirmada. No confundas la criticidad del "
    "activo (atributo del inventario) con la gravedad de sus CVE. No afirmes "
    "que existen o no existen ataques, incidentes o amenazas activas."
)

INSTRUCCIONES_ORQUESTADOR = (
    "Eres AgenteOrquestador, punto de entrada del usuario. " + REGLAS_COMUNES + "\n\n"
    "Tu salida es SIEMPRE el objeto estructurado solicitado. Elige la ruta:\n"
    "- respuesta_directa: preguntas sobre los datos de un activo del inventario "
    "(producto, version, centro, criticidad, responsable, configuracion), o un "
    "activo que no existe. Si mencionan un identificador de activo, llama "
    "SIEMPRE a consultar_activo y redacta respuesta_directa solo con su "
    "resultado. Si encontrado=false, di que el activo no existe en el "
    "inventario y no inventes datos.\n"
    "- correlacion: piden CVE candidatas, coincidencias con CISA KEV, cribado, "
    "novedades de KEV o su historial, sin pedir afectacion ni prioridad.\n"
    "- analisis_avanzado: piden analizar vulnerabilidades, afectacion por una "
    "CVE concreta, prioridad, riesgos, resultados NVD o informes.\n"
    "No hagas analisis tecnicos por tu cuenta. En correlacion y "
    "analisis_avanzado deja respuesta_directa en null. Si el activo mencionado "
    "no existe segun consultar_activo, usa respuesta_directa.\n"
    "accion_explicita: 'actualizar_novedades' solo si piden expresamente "
    "descargar/actualizar/comprobar ahora las novedades de CISA; "
    "'generar_informes' solo si piden expresamente generar o actualizar los "
    "informes; en cualquier otro caso 'ninguna'. Consultar no es actualizar. "
    "Si piden actualizar novedades, pon accion_explicita='actualizar_novedades', "
    "ruta='correlacion' y respuesta_directa=null. La herramienta de actualizacion "
    "requiere aprobacion humana individual y su ejecucion real tambien requiere "
    "habilitacion explicita por linea de comandos. Si piden generar informes, "
    "pon accion_explicita='generar_informes', "
    "ruta='correlacion' y respuesta_directa=null. Se solicitaran aprobacion "
    "humana y habilitacion por CLI, independientes de las de CISA. "
    "No afirmes haber generado informes sin verificacion_completa=true. "
    "No afirmes que se ha actualizado CISA sin un resultado exito=true. "
    "La version_referencia de novedades es una linea de base historica, "
    "no la version de la cache inmediatamente anterior."
)

# Estructura comun de datos que debe respetarse al explicar el cribado.
GUIA_CRIBADO = (
    "El cribado compara FABRICANTE y PRODUCTO/FAMILIA con el catalogo CISA KEV; "
    "no valida la version instalada contra las versiones afectadas de cada CVE. "
    "La version del inventario no demuestra afectacion por todas las CVE. "
    "Presenta siempre dos apartados separados: (A) coincidencias candidatas por "
    "producto/familia del activo (p. ej. las de PAN-OS) y (B) coincidencias solo "
    "por fabricante de OTRO producto (p. ej. Expedition), que no se suman al "
    "recuento de (A). Usa los totales exactos que devuelve la herramienta; son "
    "candidatas, no vulnerabilidades confirmadas. La criticidad del activo no "
    "indica la gravedad de cada candidata."
)

INSTRUCCIONES_CORRELACION = (
    "Eres AgenteCorrelacion. " + REGLAS_COMUNES + "\n\n"
    "Cruzas CISA KEV con el inventario usando SOLO lo almacenado. Herramientas:\n"
    "- consultar_cribado(asset_id, cve_id): herramienta principal; si hay "
    "activo, usala. Devuelve los apartados A_coincidencias_candidatas_"
    "producto_o_familia y B_coincidencias_solo_fabricante_otro_producto.\n"
    "- consultar_novedades_kev / consultar_historial_novedades_kev: solo si "
    "preguntan por novedades de CISA o su historial (datos ya guardados).\n"
    "- consultar_cisa: solo para version/estado del catalogo; nunca con "
    "forzar_actualizacion=True.\n"
    "- actualizar_novedades_cisa_controlada: cuando el orquestador indique "
    "ACCION EXPLICITA='actualizar_novedades', LLAMA a esta herramienta. "
    "Requiere aprobacion humana. Si se rechaza, NO se ejecuto; si se aprueba "
    "pero la herramienta responde exito=false, NO hubo actualizacion confirmada. "
    "Solo afirma que CISA se actualizo si la herramienta devuelve exito=true "
    "y modo_fuente=descarga. Version_referencia es la base historica "
    "de comparacion, NO la version previa de la cache. Las coincidencias "
    "del analisis se refieren solo a las NOVEDADES.\n"
    "- generar_informes_controlados: SOLO cuando el orquestador indique "
    "ACCION EXPLICITA='generar_informes', llama a esta herramienta; exige "
    "aprobacion individual. Si se rechaza, NO hay generacion; si devuelve "
    "exito=false, NO informes confirmados. Exige verificacion_completa=true "
    "antes de afirmar que ambos informes quedaron completos.\n"
    "El mensaje de contexto controlado contiene la PETICION, el ACTIVO, la CVE "
    "y la decision estructurada del Orquestador. No la reinterpretas.\n"
    "Llama unicamente a las herramientas necesarias. " + GUIA_CRIBADO + " "
    "Cita siempre el identificador del activo. No decidas afectacion "
    "confirmada ni asignes prioridades a las candidatas. Si una lista esta "
    "recortada, dilo y no inventes el desglose."
)

INSTRUCCIONES_CRITICIDAD = (
    "Eres AgenteCriticidad. " + REGLAS_COMUNES + "\n\n"
    "Recibes la peticion del usuario y la salida de AgenteCorrelacion, que son "
    "COINCIDENCIAS CANDIDATAS (no evidencias de afectacion). Herramientas:\n"
    "- evaluar_activo(asset_id): reglas deterministas de afectacion y prioridad. "
    "Llamala si hay un activo. Cubre solo tres CVE con reglas especificas.\n"
    "- consultar_nvd_piloto(asset_id, cve_id): solo si piden NVD/versiones "
    "investigadas o el activo es PAN-OS y es relevante. Una coincidencia CPE no "
    "prueba afectacion; fuera_criterios_nvd no significa equipo seguro.\n"
    "- analizar_inventario: solo para una vision global del inventario.\n"
    "La actualizacion CISA y la generacion de informes no son herramientas "
    "de este agente: son acciones del AgenteCorrelacion en modo consola, "
    "con aprobacion humana individual.\n"
    + GUIA_CRIBADO + "\n"
    "Las conclusiones sobre CVE-2023-27350, CVE-2024-3400 y CVE-2016-8562 "
    "proceden de NUESTRAS reglas deterministas aplicadas al inventario ficticio, "
    "no de un escaneo del dispositivo real. No afirmes que se haya comprobado "
    "ningun equipo real ni que existan o no ataques activos.\n"
    "Usa exclusivamente estados y prioridades devueltos por las herramientas. "
    "Si te preguntan por una CVE concreta, responde sobre esa CVE segun las "
    "reglas (p. ej. 'corregida' o 'aplicable' para este inventario ficticio). "
    "Que una CVE este corregida no significa que el activo este libre de otras "
    "vulnerabilidades. Distingue con claridad: 1) datos del inventario, "
    "2) coincidencias candidatas del cribado (no evaluadas), 3) evaluacion "
    "especifica por reglas. No describas las candidatas como de criticidad "
    "alta/media/baja. Cierra con una conclusion breve y las limitaciones."
)


# ---------------------------------------------------------------------------
# Enrutamiento sin ejecutores auxiliares
# ---------------------------------------------------------------------------
# Esta variante usa exclusivamente las conexiones del WorkflowBuilder y los
# filtros de contexto de AgentExecutor. Son funciones Python, NO nodos del grafo.
# No se guarda ninguna decision en variables globales ni en el estado de otros
# workflows. La decision se transporta dentro del mensaje del propio flujo.

MARCADOR_CONTROL = "CONTEXTO_CONTROLADO_ENTREPINARES_V1"
MARCADOR_DECISION = "DECISION_ORQUESTADOR_JSON="
MARCADOR_PREGUNTA = "PREGUNTA_USUARIO_JSON="


def _decision(mensaje) -> DecisionOrquestador | None:
    """Lee la decision estructurada del Orquestador, no interpreta texto libre."""
    if not isinstance(mensaje, AgentExecutorResponse):
        return None
    if mensaje.executor_id != ID_ORQUESTADOR:
        return None
    try:
        valor = mensaje.agent_response.value
    except Exception:
        return None
    return valor if isinstance(valor, DecisionOrquestador) else None


def _texto_mensaje(mensaje) -> str:
    return getattr(mensaje, "text", None) or ""


def _pregunta_original(mensajes: list[Message]) -> str:
    """Toma el turno de usuario mas reciente (permite reutilizar sesiones)."""
    for mensaje in reversed(mensajes):
        if str(mensaje.role) == "user" and _texto_mensaje(mensaje):
            return _texto_mensaje(mensaje)
    return ""


def _decision_de_mensajes_orquestador(mensajes: list[Message]) -> DecisionOrquestador | None:
    """Recupera la respuesta JSON del Orquestador al encadenar agentes.

    AgentExecutor transmite la conversacion completa. En la version del proyecto
    el Orquestador ya emite su DecisionOrquestador como JSON visible en DevUI.
    No se confia en una decision extraida de la peticion del usuario.
    """
    for mensaje in reversed(mensajes):
        if str(mensaje.role) != "assistant":
            continue
        contenido = _texto_mensaje(mensaje).strip()
        try:
            valor = DecisionOrquestador.model_validate_json(contenido)
        except (ValueError, TypeError):
            continue
        return valor
    return None


def _contexto_correlacion(mensajes: list[Message]) -> list[Message]:
    """Prepara un turno de usuario para Correlacion SIN un ejecutor intermedio.

    En caso de que el JSON del Orquestador no estuviese disponible en el
    historial, no inventa la ruta ni autoriza herramientas con escritura.
    """
    decision = _decision_de_mensajes_orquestador(mensajes)
    pregunta = _pregunta_original(mensajes)
    if decision is None:
        return [Message(role="user", contents=[
            "ERROR DE CONTEXTO: falta la decision estructurada del Orquestador. "
            "No ejecutes herramientas, especialmente acciones de escritura. "
            "Responde que no se ha podido continuar el analisis."
        ])]
    asset_id = (decision.asset_id or "").strip().upper() or "no indicado"
    if decision.accion_explicita == "actualizar_novedades":
        tarea = (
            "ACCION EXPLICITA: actualizar_novedades. Llama SOLO a la herramienta "
            "actualizar_novedades_cisa_controlada para pedir aprobacion humana. "
            "Si se rechaza o exito=false, no afirmes actualizacion. "
            "Solo confirma descarga si exito=true y modo_fuente=descarga."
        )
    elif decision.accion_explicita == "generar_informes":
        tarea = (
            "ACCION EXPLICITA: generar_informes. Llama SOLO a la herramienta "
            "generar_informes_controlados para pedir aprobacion humana. "
            "Si se rechaza o exito=false, no afirmes generacion. "
            "Solo confirma ambos informes si verificacion_completa=true."
        )
    else:
        tarea = (
            "ACCION EXPLICITA: ninguna. Utiliza solo las herramientas de lectura "
            "necesarias para cruzar CISA KEV con el inventario. "
            "Separa candidatas por producto de coincidencias solo por fabricante. "
            "No confirmes afectacion ni asignes prioridad a las candidatas."
        )
    contexto = (
        f"{MARCADOR_CONTROL}\n"
        f"{MARCADOR_DECISION}{decision.model_dump_json()}\n"
        f"{MARCADOR_PREGUNTA}{json.dumps(pregunta, ensure_ascii=False)}\n\n"
        f"ACTIVO: {asset_id}\n"
        f"CVE: {decision.cve_id or 'ninguna'}\n"
        f"RUTA ELEGIDA POR EL ORQUESTADOR: {decision.ruta}\n"
        f"{tarea}\n"
        "El inventario es ficticio. No cambies de ruta ni ejecutes otras acciones."
    )
    return [Message(role="user", contents=[contexto])]


def _extraer_contexto_controlado(mensajes: list[Message]) -> tuple[DecisionOrquestador | None, str]:
    """Lee SOLO el mensaje de control que nosotros creamos para Correlacion.

    No interpreta las respuestas del LLM ni usa variables globales. El primer
    mensaje user enviado a Correlacion empieza por MARCADOR_CONTROL. Busca la
    ultima ocurrencia valida, no texto repetido de una ejecucion anterior.
    """
    for mensaje in reversed(mensajes):
        if str(mensaje.role) != "user":
            continue
        texto = _texto_mensaje(mensaje)
        lineas = texto.splitlines()
        if not lineas or lineas[0] != MARCADOR_CONTROL:
            continue
        if len(lineas) < 3 or not lineas[1].startswith(MARCADOR_DECISION):
            continue
        if not lineas[2].startswith(MARCADOR_PREGUNTA):
            continue
        try:
            decision = DecisionOrquestador.model_validate_json(
                lineas[1][len(MARCADOR_DECISION):]
            )
            pregunta = json.loads(lineas[2][len(MARCADOR_PREGUNTA):])
            if not isinstance(pregunta, str):
                continue
            return decision, pregunta
        except (ValueError, TypeError):
            continue
    return None, ""


def _decision_de_correlacion(respuesta: AgentExecutorResponse) -> DecisionOrquestador | None:
    if not isinstance(respuesta, AgentExecutorResponse) or respuesta.executor_id != ID_CORRELACION:
        return None
    decision, _ = _extraer_contexto_controlado(respuesta.full_conversation)
    return decision


def _contexto_criticidad(mensajes: list[Message]) -> list[Message]:
    """Prepara el trabajo de Criticidad en context_filter, sin PuenteCorrelacion."""
    decision, pregunta = _extraer_contexto_controlado(mensajes)
    if decision is None or decision.ruta != "analisis_avanzado" or decision.accion_explicita != "ninguna":
        return [Message(role="user", contents=[
            "ERROR DE CONTEXTO: ruta de Criticidad no validada. "
            "No ejecutes herramientas ni inventes resultados."
        ])]
    texto_correlacion = ""
    for mensaje in reversed(mensajes):
        if str(mensaje.role) == "assistant" and _texto_mensaje(mensaje).strip():
            texto_correlacion = _texto_mensaje(mensaje)
            break
    prompt = (
        f"PETICION DEL USUARIO: {pregunta}\n"
        f"ACTIVO: {decision.asset_id or 'no indicado'}\n"
        f"CVE MENCIONADA: {decision.cve_id or 'ninguna'}\n\n"
        "SALIDA DE AgenteCorrelacion (COINCIDENCIAS CANDIDATAS del cribado KEV; "
        "no son afectaciones confirmadas):\n"
        f"{texto_correlacion}\n\n"
        "Evalua afectacion y prioridad usando tus herramientas. Distingue los "
        "hallazgos candidatos de las reglas deterministas, y cita limitaciones."
    )
    return [Message(role="user", contents=[prompt])]


def _respuesta_inventario_verificada(asset_id: str | None) -> str:
    """Respaldo de SOLO LECTURA para decisiones directas sin texto.

    El identificador puede estar ausente o ser incorrecto; jamas se inventa
    una respuesta. La lectura directa usa la herramienta ya existente.
    """
    objetivo = (asset_id or "").strip().upper()
    if not objetivo:
        return (
            "El orquestador eligio respuesta directa sin proporcionar texto "
            "ni identificador de activo verificable. No se han inventado datos."
        )
    try:
        datos = json.loads(consultar_activo.func(objetivo))
        if not isinstance(datos, dict):
            raise ValueError("Respuesta de inventario inesperada")
        if not datos.get("encontrado"):
            return f"El activo {objetivo} no existe en el inventario ficticio."
        activo = datos.get("activo")
        if not isinstance(activo, dict) or activo.get("asset_id", "").upper() != objetivo:
            raise ValueError("Identificador de inventario incoherente")
        return (
            f"Datos verificados del inventario ficticio para {objetivo}: "
            f"{json.dumps(activo, ensure_ascii=False, sort_keys=True)}"
        )
    except Exception:
        return (
            f"No se pudo construir una respuesta verificada para {objetivo}; "
            "la respuesta incompleta del modelo no se ha presentado como un hecho."
        )


class RespuestaFinal(Executor):
    """Unico ejecutor auxiliar y unico punto de salida del workflow."""

    def __init__(self):
        super().__init__(id="RespuestaFinal")

    @handler
    async def desde_agente(
        self,
        respuesta: AgentExecutorResponse,
        ctx: WorkflowContext[Never, str],
    ) -> None:
        decision = _decision(respuesta)
        if respuesta.executor_id == ID_ORQUESTADOR:
            if decision is None:
                texto = (
                    "No se pudo interpretar la decision tipada del Orquestador. "
                    "No se ha realizado ningun analisis. Reformula la consulta."
                )
            elif decision.asset_id and not _existe_activo(decision.asset_id):
                texto = (
                    f"El activo {decision.asset_id.strip().upper()} no existe en "
                    "el inventario (ficticio). No se ha realizado ningun analisis."
                )
            elif decision.accion_explicita != "ninguna":
                texto = _mensaje_accion_no_ejecutada(decision.accion_explicita)
            else:
                texto = (decision.respuesta_directa or "").strip()
                if not texto:
                    texto = _respuesta_inventario_verificada(decision.asset_id)
        elif respuesta.executor_id == ID_CORRELACION:
            # Importante: en una reanudacion tras aprobacion (HITL), MAF
            # puede reconstruir el historial de Correlacion solo con el
            # resultado de la aprobacion y perder el marcador de ruta.
            # En esa situacion la arista ya envia a RespuestaFinal, y aqui
            # conservamos la respuesta del agente en lugar de descartarla.
            # Las herramientas siguen teniendo sus dos barreras de seguridad:
            # permiso CLI inmutable y aprobacion individual.
            texto = respuesta.agent_response.text
        else:
            texto = respuesta.agent_response.text
        await ctx.yield_output(texto)


def _existe_activo(asset_id: str) -> bool:
    objetivo = asset_id.strip().upper()
    return any(a["asset_id"].upper() == objetivo for a in leer_inventario())


# ---------------------------------------------------------------------------
# Construccion (separada de la ejecucion)
# ---------------------------------------------------------------------------

def crear_credencial() -> AzureCliCredential:
    """Sesion de Azure CLI del usuario (`az login` en su propio ordenador).

    COPIA DIDACTICA: si AZURE_TENANT_ID esta definido, se pide el token de ese
    tenant. Autenticarse NO concede permisos: el usuario necesita un rol en el
    proyecto Foundry.
    """
    tenant = os.environ.get("AZURE_TENANT_ID", "").strip()
    return AzureCliCredential(tenant_id=tenant) if tenant else AzureCliCredential()


def crear_cliente() -> FoundryChatClient:
    # Se relee el entorno en cada llamada (un .env cargado despues del import
    # tambien funciona). Sin endpoint no se intenta ninguna conexion.
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "") or PROJECT_ENDPOINT
    if not endpoint:
        raise RuntimeError(
            "Falta FOUNDRY_PROJECT_ENDPOINT. Copia .env.example a .env y rellena "
            "el endpoint de TU proyecto Foundry (ver la guia)."
        )
    return FoundryChatClient(
        project_endpoint=endpoint,
        model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "") or MODEL,
        credential=crear_credencial(),
    )


def construir_agentes(
    client, *, permitir_escrituras: bool = False, permitir_informes: bool = False,
    acciones_interactivas: bool = True,
) -> dict[str, Agent]:
    orquestador = Agent(
        client=client,
        name=ID_ORQUESTADOR,
        description="Punto de entrada: responde consultas de inventario y decide la ruta.",
        instructions=INSTRUCCIONES_ORQUESTADOR,
        tools=[consultar_activo],
        default_options={"response_format": DecisionOrquestador},
    )
    herramientas_correlacion = [
        consultar_cribado,
        consultar_novedades_kev,
        consultar_historial_novedades_kev,
        consultar_cisa_solo_lectura,
    ]
    instrucciones_correlacion = INSTRUCCIONES_CORRELACION
    if acciones_interactivas:
        herramientas_correlacion.extend([
            crear_herramienta_actualizacion(permitir_escrituras),
            crear_herramienta_informes(permitir_informes),
        ])
    else:
        # DevUI: no registramos siquiera las dos herramientas con escritura.
        instrucciones_correlacion += (
            "\nMODO DEVUI / SOLO LECTURA: las herramientas "
            "actualizar_novedades_cisa_controlada y generar_informes_controlados "
            "NO estan disponibles en este modo. No intentes invocarlas."
        )
    correlacion = Agent(
        client=client,
        name=ID_CORRELACION,
        description="Cruza CISA KEV con el inventario (coincidencias candidatas).",
        instructions=instrucciones_correlacion,
        tools=herramientas_correlacion,
    )
    criticidad = Agent(
        client=client,
        name=ID_CRITICIDAD,
        description="Evalua afectacion y prioridad segun las reglas deterministas.",
        instructions=INSTRUCCIONES_CRITICIDAD,
        tools=[
            evaluar_activo,
            consultar_nvd_piloto,
            analizar_inventario,
        ],
    )
    return {
        ID_ORQUESTADOR: orquestador,
        ID_CORRELACION: correlacion,
        ID_CRITICIDAD: criticidad,
    }


def construir_workflow(
    client=None, *, permitir_escrituras: bool = False,
    permitir_informes: bool = False, acciones_interactivas: bool = True,
):
    """Devuelve (workflow, agentes); grafo de solo cuatro nodos.

    Las condiciones de las conexiones ejecutan decisiones del Orquestador;
    context_filter prepara los mensajes sin ejecutores auxiliares.
    DevUI no registra herramientas de escritura y deniega acciones explicitas.
    """
    bloquear_descargas_cisa()
    client = client or crear_cliente()
    agentes = construir_agentes(
        client,
        permitir_escrituras=permitir_escrituras,
        permitir_informes=permitir_informes,
        acciones_interactivas=acciones_interactivas,
    )

    orquestador = AgentExecutor(agentes[ID_ORQUESTADOR], id=ID_ORQUESTADOR)
    correlacion = AgentExecutor(
        agentes[ID_CORRELACION],
        id=ID_CORRELACION,
        context_mode="custom",
        context_filter=_contexto_correlacion,
        ensure_trailing_user_turn=True,
    )
    criticidad = AgentExecutor(
        agentes[ID_CRITICIDAD],
        id=ID_CRITICIDAD,
        context_mode="custom",
        context_filter=_contexto_criticidad,
        ensure_trailing_user_turn=True,
    )
    final = RespuestaFinal()

    def va_a_correlacion(m):
        d = _decision(m)
        if d is None:
            return False
        if d.asset_id and not _existe_activo(d.asset_id):
            return False
        if d.accion_explicita in ("actualizar_novedades", "generar_informes"):
            return acciones_interactivas
        return d.accion_explicita == "ninguna" and d.ruta in (
            "correlacion", "analisis_avanzado"
        )

    def va_directo_a_final(m):
        return not va_a_correlacion(m)

    def va_a_criticidad(m):
        decision = _decision_de_correlacion(m)
        return bool(
            decision
            and decision.ruta == "analisis_avanzado"
            and decision.accion_explicita == "ninguna"
        )

    def correlacion_termina(m):
        return not va_a_criticidad(m)

    workflow = (
        WorkflowBuilder(
            name="WorkflowEntrepinaresSinPuentes",
            description=(
                "Tres agentes conectados directamente; enrutamiento condicional "
                "del Orquestador, contexto mediante filtros y unico nodo final."
            ),
            start_executor=orquestador,
            output_from=[final],
            intermediate_output_from="all_other",
        )
        .add_edge(orquestador, final, condition=va_directo_a_final)
        .add_edge(orquestador, correlacion, condition=va_a_correlacion)
        .add_edge(correlacion, final, condition=correlacion_termina)
        .add_edge(correlacion, criticidad, condition=va_a_criticidad)
        .add_edge(criticidad, final)
        .build()
    )
    return workflow, agentes


# ---------------------------------------------------------------------------
# Modos de ejecucion
# ---------------------------------------------------------------------------

CASOS_MANUALES = [
    ("A basica", "¿Qué versión tiene IT-004?"),
    ("B correlacion", "¿Qué CVE candidatas aparecen para IT-004 en CISA KEV?"),
    ("C avanzado", "Analiza las vulnerabilidades y la prioridad de IT-004."),
    ("D inexistente", "¿Qué versión tiene IT-999?"),
    ("E corregida", "¿Está afectado IT-006 por CVE-2024-3400? ¿Qué otros riesgos podrían existir?"),
    ("F aprobacion CISA", "Actualiza ahora las novedades de CISA KEV."),
    ("G aprobacion informes", "Genera ahora los informes HTML y Markdown de vulnerabilidades."),
]


async def ejecutar_consola(
    pregunta: str, *, permitir_escrituras: bool = False, permitir_informes: bool = False
) -> None:
    """Ejecuta workflow, atiende aprobaciones y muestra solo la respuesta final.

    La aprobacion es por request_id; no se usan permisos globales. Ninguna
    aprobacion esta preconcedida: por defecto cada solicitud se RECHAZA.
    """
    workflow, _ = construir_workflow(
        permitir_escrituras=permitir_escrituras,
        permitir_informes=permitir_informes,
        acciones_interactivas=True,
    )
    print(f"\nCONSULTA: {pregunta}\n")
    print("MODO CISA:", "REAL HABILITADO" if permitir_escrituras else "BLOQUEADO")
    print("MODO INFORMES:", "REAL HABILITADO" if permitir_informes else "BLOQUEADO")
    print("AMBAS ACCIONES EXIGEN APROBACION HUMANA INDIVIDUAL")
    antes = _huellas_vigiladas()


    resultado = await workflow.run(pregunta)
    eventos_todos = list(resultado)

    for _ in range(5):  # Limite defensivo ante nuevas solicitudes imprevistas.
        pendientes = resultado.get_request_info_events()
        if not pendientes:
            break

        respuestas = {}
        for evento in pendientes:
            solicitud = evento.data
            if getattr(solicitud, "type", None) != "function_approval_request":
                raise RuntimeError(f"Solicitud HITL inesperada: {solicitud!r}")
            llamada = getattr(solicitud, "function_call", None)
            nombre = getattr(llamada, "name", "desconocida")
            argumentos = getattr(llamada, "arguments", None)
            if nombre not in ("actualizar_novedades_cisa_controlada", "generar_informes_controlados"):
                raise RuntimeError(f"Herramienta inesperada: {nombre}")
            print(f"\nAPROBACION SOLICITADA: {nombre}")
            print(f"Argumentos: {argumentos}")
            texto = input("¿Aprobar esta operacion? [s/N]: ").strip().lower()
            aprobado = texto in ("s", "si", "sí")
            print("Decision:", "APROBADA" if aprobado else "RECHAZADA")
            respuestas[evento.request_id] = solicitud.to_function_approval_response(
                approved=aprobado
            )

        resultado = await workflow.run(responses=respuestas)
        eventos_todos.extend(resultado)
    else:
        raise RuntimeError("Demasiadas solicitudes de aprobacion: ejecucion detenida")

    ruta = [
        e.executor_id for e in eventos_todos
        if e.type == "executor_invoked"
    ]
    agentes = [r for r in ruta if r.startswith("Agente")]
    print("\nRUTA COMPLETA :", " -> ".join(ruta))
    print("AGENTES USADOS:", " -> ".join(agentes) or "(ninguno)")
    print("\nRESPUESTA FINAL:")
    for salida in resultado.get_outputs():
        print(salida)

    despues = _huellas_vigiladas()
    print("\nCONTROL DE ARCHIVOS (SHA-256 antes/despues):")
    for ruta in antes:
        print(f"  {ruta}: {'SIN CAMBIOS' if antes[ruta] == despues[ruta] else 'MODIFICADO'}")


def ejecutar_devui(puerto: int, sin_auth: bool) -> None:
    from agent_framework.devui import serve

    workflow, _ = construir_workflow(
        permitir_escrituras=False,
        permitir_informes=False,
        acciones_interactivas=False,
    )
    print(f"DevUI en http://127.0.0.1:{puerto} (solo localhost)")
    print("DevUI: SOLO LECTURA; acciones de escritura NO disponibles")
    # Solo cuatro nodos visibles; agentes no ejecutables fuera del workflow.
    serve(
        entities=[workflow],
        host="127.0.0.1",
        port=puerto,
        auto_open=False,
        auth_enabled=not sin_auth,
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="modo", required=True)

    p_consola = sub.add_parser("consola", help="Ejecuta una consulta y muestra la ruta.")
    p_consola.add_argument("-q", "--consulta", help="Consulta; si se omite, se pregunta.")
    p_consola.add_argument(
        "--habilitar-actualizacion-real", action="store_true",
        help="Solo consola: habilita actualizacion CISA real tras aprobacion humana.",
    )

    p_consola.add_argument(
        "--habilitar-informes-reales", action="store_true",
        help="Solo consola: permite escribir informes MD y HTML tras aprobacion humana.",
    )

    p_devui = sub.add_parser("devui", help="Abre DevUI en localhost.")
    p_devui.add_argument("--puerto", type=int, default=8090)
    p_devui.add_argument(
        "--sin-auth", action="store_true",
        help="Desactiva el token Bearer de DevUI (solo para localhost).",
    )

    sub.add_parser("casos", help="Lista los casos de prueba manuales.")

    args = parser.parse_args()

    if args.modo == "casos":
        for nombre, texto in CASOS_MANUALES:
            print(f"{nombre:15} {texto}")
    elif args.modo == "consola":
        pregunta = args.consulta or input("Consulta > ").strip()
        if pregunta:
            asyncio.run(ejecutar_consola(
                pregunta,
                permitir_escrituras=args.habilitar_actualizacion_real,
                permitir_informes=args.habilitar_informes_reales,
            ))
    else:
        ejecutar_devui(args.puerto, args.sin_auth)


if __name__ == "__main__":
    main()