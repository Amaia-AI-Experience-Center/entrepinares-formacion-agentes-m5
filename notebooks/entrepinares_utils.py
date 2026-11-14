"""Adaptador minimo para los cuadernos didacticos de Entrepinares.

NO contiene logica de negocio: importa el workflow tal cual
(orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py) y solo
  1. prepara el entorno de forma segura (sys.path, .env, bloqueo de descargas CISA),
  2. ejecuta una consulta y convierte los eventos de MAF en una traza legible,
  3. comprueba que los datos protegidos no cambian (SHA-256).

El workflow que se construye es SIEMPRE de solo lectura
(acciones_interactivas=False): no registra las herramientas de escritura.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parents[1]
MODULO_WORKFLOW = "orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION"
ENDPOINT_SIN_CONEXION = "https://ejemplo.invalid/api/projects/sin-conexion"


# ---------------------------------------------------------------------------
# Preparacion del entorno
# ---------------------------------------------------------------------------

def preparar_entorno(cargar_env: bool = True):
    """Deja el kernel listo y devuelve el modulo del workflow.

    - Anade la raiz del repositorio a sys.path.
    - Carga RAIZ/.env si existe (sin pisar variables ya definidas).
    - Importa el workflow y BLOQUEA las descargas de CISA en este proceso.
      Es imprescindible hacerlo antes de usar cualquier herramienta: sin el
      bloqueo, una cache de mas de 24 h provocaria una descarga y la
      sobrescritura de datos/cisa_kev_cache.json.
    Es idempotente.
    """
    if str(RAIZ) not in sys.path:
        sys.path.insert(0, str(RAIZ))
    if cargar_env:
        try:
            from dotenv import load_dotenv

            load_dotenv(RAIZ / ".env", override=False)
        except ImportError:  # python-dotenv es opcional
            pass
    modulo = importlib.import_module(MODULO_WORKFLOW)
    modulo.bloquear_descargas_cisa()
    return modulo


def comprobar_configuracion() -> dict[str, Any]:
    """Comprueba la configuracion local SIN llamadas de red."""
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    host = urlparse(endpoint).hostname if endpoint else None
    return {
        "endpoint_configurado": bool(endpoint),
        "host_endpoint": host,
        "modelo": os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "") or "gpt-4.1-mini",
        "tenant_indicado": bool(os.environ.get("AZURE_TENANT_ID", "").strip()),
        "az_en_path": shutil.which("az") is not None,
        "archivo_env_existe": (RAIZ / ".env").is_file(),
    }


def construir_workflow_sin_conexion(modulo=None):
    """Workflow de solo lectura con un cliente que NUNCA se usa (sin red).

    Sirve para explicar la estructura del grafo sin Foundry: construir el
    cliente no abre ninguna conexion ni pide tokens.
    """
    modulo = modulo or preparar_entorno()
    cliente = modulo.FoundryChatClient(
        project_endpoint=ENDPOINT_SIN_CONEXION,
        model=modulo.MODEL,
        credential=modulo.AzureCliCredential(),  # no se usa: el cliente nunca llama al modelo
    )
    return modulo.construir_workflow(cliente, acciones_interactivas=False)


# ---------------------------------------------------------------------------
# Informe local de ejercicio (carpeta ignorada por Git)
# ---------------------------------------------------------------------------

CARPETA_SALIDAS = RAIZ / "salidas"


def generar_informe_local(destino: Path | None = None) -> dict[str, Path]:
    """Genera el informe Markdown + HTML con los modulos ORIGINALES, pero en
    `salidas/` (ignorada por Git) en lugar de `informes/`.

    Solo se redirigen las rutas de salida; la logica de los informes no cambia.
    Requiere haber llamado antes a preparar_entorno() (descargas CISA bloqueadas).
    """
    import generar_html
    import generar_informe

    destino = Path(destino) if destino else CARPETA_SALIDAS
    destino.mkdir(parents=True, exist_ok=True)
    md = destino / "informe_vulnerabilidades.md"
    html = destino / "informe_vulnerabilidades.html"
    originales = (generar_informe.RUTA_INFORME, generar_html.ORIGEN, generar_html.DESTINO)
    try:
        generar_informe.RUTA_INFORME = md
        generar_html.ORIGEN, generar_html.DESTINO = md, html
        generar_informe.generar_informe()
        generar_html.generar_html()
    finally:
        generar_informe.RUTA_INFORME, generar_html.ORIGEN, generar_html.DESTINO = originales
    return {"markdown": md, "html": html}


def evidencias_datos() -> dict[str, Any]:
    """Procedencia de los datos guardados: version CISA, fecha y origen del cribado."""
    cache = json.loads((RAIZ / "datos" / "cisa_kev_cache.json").read_text(encoding="utf-8"))
    cribado = json.loads((RAIZ / "datos" / "cribado_kev.json").read_text(encoding="utf-8"))
    return {
        "catalogo_cisa": {
            "version": cache["catalogo"]["catalogVersion"],
            "total_cve": cache["catalogo"]["count"],
            "obtenido_en_utc": cache["obtenido_en_utc"],
            "fuente": cache.get("fuente"),
        },
        "cribado": {"fuente": cribado.get("fuente"), "resumen": cribado.get("resumen")},
    }


def diagrama_mermaid(workflow) -> str:
    from agent_framework import WorkflowViz

    return WorkflowViz(workflow).to_mermaid()


def mostrar_mermaid(codigo: str) -> None:
    """Muestra el diagrama (JupyterLab >= 4.1 lo dibuja) y el codigo en texto."""
    try:
        from IPython.display import Markdown, display

        display(Markdown(f"```mermaid\n{codigo}\n```"))
    except ImportError:  # pragma: no cover
        pass
    print(codigo)


# ---------------------------------------------------------------------------
# Integridad de los datos
# ---------------------------------------------------------------------------

def huellas_datos(carpeta: Path | None = None) -> dict[str, str]:
    """SHA-256 de todos los archivos de datos/ (ruta relativa -> hash)."""
    base = Path(carpeta) if carpeta else RAIZ / "datos"
    huellas: dict[str, str] = {}
    for ruta in sorted(base.rglob("*")):
        if ruta.is_file():
            h = hashlib.sha256()
            with ruta.open("rb") as f:
                for bloque in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(bloque)
            huellas[ruta.relative_to(base).as_posix()] = h.hexdigest()
    return huellas


def comparar_huellas(antes: dict[str, str], despues: dict[str, str]) -> dict[str, list[str]]:
    return {
        "modificados": sorted(k for k in antes if k in despues and antes[k] != despues[k]),
        "nuevos": sorted(k for k in despues if k not in antes),
        "ausentes": sorted(k for k in antes if k not in despues),
    }


def informe_integridad(antes: dict[str, str], despues: dict[str, str]) -> bool:
    """Imprime el resultado y devuelve True si no hay ningun cambio."""
    dif = comparar_huellas(antes, despues)
    limpio = not any(dif.values())
    print(f"Archivos en datos/: {len(despues)}")
    print("INTEGRIDAD:", "SIN CAMBIOS en datos/" if limpio else f"CAMBIOS DETECTADOS {dif}")
    return limpio


# ---------------------------------------------------------------------------
# Trazas de ejecucion
# ---------------------------------------------------------------------------

@dataclass
class LlamadaHerramienta:
    agente: str
    nombre: str
    argumentos: str
    resultado: str = ""


@dataclass
class Traza:
    pregunta: str
    ruta: list[str] = field(default_factory=list)
    agentes: list[str] = field(default_factory=list)
    decision: dict | None = None
    herramientas: list[LlamadaHerramienta] = field(default_factory=list)
    respuesta: str = ""
    duracion_s: float = 0.0
    eventos: list[tuple[str, str | None]] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)


def _recortar(texto: Any, maximo: int = 160) -> str:
    texto = texto if isinstance(texto, str) else json.dumps(texto, ensure_ascii=False, default=str)
    texto = " ".join(texto.split())
    return texto if len(texto) <= maximo else texto[: maximo - 1] + "…"


def _a_dict(valor: Any) -> dict | None:
    if valor is None:
        return None
    if hasattr(valor, "model_dump"):
        return valor.model_dump()
    if isinstance(valor, dict):
        return valor
    return None


def _decision_de(respuesta: Any) -> dict | None:
    """Decision estructurada del Orquestador: .value si existe; si no, el JSON del texto."""
    try:
        d = _a_dict(respuesta.value)
        if d:
            return d
    except Exception:
        pass
    try:
        d = json.loads(respuesta.text)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def _herramientas_de(agente: str, respuesta: Any) -> list[LlamadaHerramienta]:
    """Llamadas a herramientas (function_call) y sus resultados (function_result)."""
    llamadas: dict[str, LlamadaHerramienta] = {}
    orden: list[str] = []
    for mensaje in getattr(respuesta, "messages", None) or []:
        for c in getattr(mensaje, "contents", None) or []:
            tipo = getattr(c, "type", None)
            if tipo == "function_call":
                cid = getattr(c, "call_id", None) or f"sin-id-{len(orden)}"
                args = getattr(c, "arguments", "")
                llamadas[cid] = LlamadaHerramienta(
                    agente, getattr(c, "name", "?"), _recortar(args if args else "{}")
                )
                orden.append(cid)
            elif tipo == "function_result":
                cid = getattr(c, "call_id", None)
                if cid in llamadas:
                    llamadas[cid].resultado = _recortar(getattr(c, "result", ""), 200)
    return [llamadas[i] for i in orden]


async def ejecutar_consulta(pregunta: str, *, workflow=None, modulo=None) -> Traza:
    """Ejecuta UNA consulta y devuelve la traza estructurada.

    Por defecto construye un workflow nuevo de solo lectura (llama a Foundry,
    necesita FOUNDRY_PROJECT_ENDPOINT y `az login`). Se puede inyectar un
    `workflow` propio (por ejemplo, en las pruebas).
    """
    if workflow is None:
        modulo = modulo or preparar_entorno()
        workflow, _ = modulo.construir_workflow(acciones_interactivas=False)
    inicio = time.perf_counter()
    resultado = await workflow.run(pregunta)
    traza = Traza(pregunta=pregunta, duracion_s=round(time.perf_counter() - inicio, 2))

    vistos: set[tuple[str, str]] = set()
    for e in list(resultado):
        traza.eventos.append((e.type, getattr(e, "executor_id", None)))
        ejecutor = getattr(e, "executor_id", None)
        if e.type == "executor_invoked" and ejecutor:
            traza.ruta.append(ejecutor)
        datos = getattr(e, "data", None)
        resp = getattr(datos, "agent_response", datos)
        if e.type in ("intermediate", "output", "data", "executor_completed") and hasattr(resp, "messages"):
            if ejecutor and ejecutor.startswith("Agente"):
                if ejecutor.endswith("Orquestador") and traza.decision is None:
                    traza.decision = _decision_de(resp)
                for h in _herramientas_de(ejecutor, resp):
                    clave = (h.agente, h.nombre + h.argumentos)
                    if clave not in vistos:
                        vistos.add(clave)
                        traza.herramientas.append(h)

    traza.agentes = [r for r in traza.ruta if r.startswith("Agente")]
    traza.respuesta = "\n".join(str(s) for s in resultado.get_outputs())
    if resultado.get_request_info_events():
        traza.avisos.append(
            "El workflow pidio una aprobacion (HITL). Este cuaderno es de solo "
            "lectura y no concede aprobaciones."
        )
    return traza


_VARIABLES_SECRETAS = ("DEVUI_AUTH_TOKEN",)


def _ocultar_secretos(texto: str) -> str:
    """Sustituye por *** cualquier valor secreto del entorno o token que aparezca en un texto."""
    import re

    for nombre in _VARIABLES_SECRETAS:
        valor = os.environ.get(nombre, "")
        if len(valor) >= 4:
            texto = texto.replace(valor, "***")
    texto = re.sub(r"eyJ[A-Za-z0-9_\-.]{20,}", "***", texto)
    return re.sub(r"(sig|se|sp|sv)=[^&\s\"']+", r"\1=***", texto)


def probar_credencial() -> dict[str, Any]:
    """Pide UN token para Foundry con tu sesion de Azure CLI (operacion opcional).

    No usa el modelo ni consume cuota. Nunca devuelve ni imprime el token.
    Que funcione NO demuestra que tengas permisos en el proyecto Foundry.
    """
    from datetime import datetime, timezone

    modulo = preparar_entorno()
    token = modulo.crear_credencial().get_token("https://ai.azure.com/.default")
    caduca = datetime.fromtimestamp(token.expires_on, tz=timezone.utc).isoformat()
    return {"token_obtenido": True, "el_token_caduca_utc": caduca}


def explicar_error(exc: BaseException) -> str:
    """Traduce los fallos tipicos de conexion a una pista accionable (sin secretos)."""
    nombre = type(exc).__name__
    texto = _ocultar_secretos(str(exc))
    if "FOUNDRY_PROJECT_ENDPOINT" in texto:
        return "Falta el endpoint: copia .env.example a .env y rellena FOUNDRY_PROJECT_ENDPOINT; reinicia el kernel."
    if ("CredentialUnavailable" in nombre or "az login" in texto.lower()
            or "AzureCliCredential" in texto or "Azure CLI not found" in texto):
        return "Azure CLI no tiene sesión válida: ejecuta `az login` en una terminal y reinicia el kernel."
    if "AADSTS" in texto and ("tenant" in texto.lower() or "AADSTS50020" in texto or "AADSTS90002" in texto):
        return "El tenant no es el correcto: `az login --tenant <id>` o define AZURE_TENANT_ID en .env."
    if "401" in texto or "403" in texto or "PermissionDenied" in texto or "AuthorizationFailed" in texto:
        return ("Te has autenticado, pero tu usuario no tiene permisos en el proyecto Foundry: "
                "pide un rol que permita usar el modelo (normalmente 'Azure AI User').")
    if "404" in texto or "DeploymentNotFound" in texto:
        return "No se encuentra el modelo: revisa AZURE_AI_MODEL_DEPLOYMENT_NAME y el endpoint."
    if "429" in texto or "RateLimit" in nombre:
        return "Límite de cuota (429): espera un minuto y repite."
    return f"{nombre}: {_recortar(texto, 300)}"


# ---------------------------------------------------------------------------
# Presentacion
# ---------------------------------------------------------------------------

def mostrar_traza(t: Traza) -> None:
    print("=" * 72)
    print("CONSULTA :", t.pregunta)
    print("RUTA     :", " -> ".join(t.ruta) or "(sin eventos)")
    print("AGENTES  :", " -> ".join(t.agentes) or "(ninguno)")
    if t.decision:
        print("DECISION DEL ORQUESTADOR:")
        for clave in ("ruta", "asset_id", "cve_id", "accion_explicita", "motivo"):
            if clave in t.decision:
                print(f"   {clave:17}: {t.decision[clave]}")
    if t.herramientas:
        print("HERRAMIENTAS LLAMADAS:")
        for h in t.herramientas:
            print(f"   [{h.agente}] {h.nombre}({h.argumentos})")
            if h.resultado:
                print(f"        -> {h.resultado}")
    else:
        print("HERRAMIENTAS LLAMADAS: (ninguna visible en los eventos)")
    for aviso in t.avisos:
        print("AVISO    :", aviso)
    print(f"TIEMPO   : {t.duracion_s} s")
    print("RESPUESTA FINAL:")
    print(t.respuesta)


def tabla_resumen(trazas: list[Traza]) -> None:
    filas = [("Consulta", "Ruta del orquestador", "Agentes", "Herramientas", "s")]
    for t in trazas:
        ruta = (t.decision or {}).get("ruta", "?")
        filas.append((
            _recortar(t.pregunta, 48), ruta, str(len(t.agentes)),
            str(len(t.herramientas)), str(t.duracion_s),
        ))
    anchos = [max(len(f[i]) for f in filas) for i in range(5)]
    for i, f in enumerate(filas):
        print("  ".join(c.ljust(anchos[j]) for j, c in enumerate(f)))
        if i == 0:
            print("  ".join("-" * a for a in anchos))


def json_bonito(valor: Any, maximo: int = 1500) -> str:
    if isinstance(valor, str):
        try:
            valor = json.loads(valor)
        except ValueError:
            return valor[:maximo]
    texto = json.dumps(valor, ensure_ascii=False, indent=2, default=str)
    return texto if len(texto) <= maximo else texto[:maximo] + "\n… (recortado)"
