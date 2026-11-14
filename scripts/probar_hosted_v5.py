"""Cliente de SOLO LECTURA para el agente Hosted V5 de Entrepinares en Microsoft Foundry.

Uso (raiz del repositorio, venv activado, tras `az login`):

    python scripts/probar_hosted_v5.py                    # las tres pruebas
    python scripts/probar_hosted_v5.py --prueba cisa      # una prueba
    python scripts/probar_hosted_v5.py --pregunta "¿Qué versión tiene IT-001?"

Configuracion (variables de entorno o .env de la raiz):
    FOUNDRY_PROJECT_ENDPOINT   endpoint del proyecto Foundry (obligatorio)
    HOSTED_AGENT_NAME          nombre del agente Hosted (por defecto entrepinares-itot-v5-lab)
    AZURE_TENANT_ID            opcional: tenant para AzureCliCredential

Autenticacion: tu sesion de Azure CLI (AzureCliCredential). `az login` NO concede
permisos: tu usuario necesita un rol en el proyecto Foundry que permita invocar
agentes (p. ej. "Azure AI User").

Seguridad: el cliente solo hace preguntas de lectura. Si el agente pidiera una
aprobacion humana para escribir (actualizar CISA o publicar informes), el cliente
NO la concede y se detiene. Nunca imprime tokens ni SAS.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
AGENTE_POR_DEFECTO = "entrepinares-itot-v5-lab"

NEGATIVAS = ["no ha sido posible", "no se pudo", "no está disponible", "no esta disponible",
             "no disponible", "no dispongo", "error", "no se ha podido"]

PRUEBAS = {
    "inventario": {
        "pregunta": "¿Qué versión tiene IT-004?",
        "esperado": ["11.1.2"],
        "explica": "Lectura del inventario ficticio empaquetado en el agente.",
    },
    "cisa": {
        "pregunta": ("Consulta con tu herramienta de solo lectura el estado del catálogo CISA KEV y dime "
                     "su versión, su origen y su identificador de publicación. No actualices nada."),
        "esperado": ["azure_blob_verificado"],  # --esperar-version añade la versión esperada
        "explica": "La herramienta consultar_cisa debe leer el puntero activo de Azure Blob.",
    },
    "correlacion": {
        "pregunta": ("¿Aparece la CVE-2026-124194 en el cribado de CISA KEV del activo IT-007? "
                     "Responde únicamente con lo que devuelva el cribado."),
        "esperado": ["CVE-2026-124194"],
        "explica": ("Esa CVE solo existe en el cribado del catálogo publicado en Blob el 13/11/2026 "
                    "(versión 2026.11.10); la copia empaquetada en el agente (2026.11.09) no la contiene."),
    },
}


def evaluar(texto: str, caso: dict) -> tuple[bool, str]:
    """Comprobación orientativa: deben aparecer los esperados y ninguna frase de fallo."""
    bajo = texto.lower()
    faltan = [e for e in caso.get("esperado", []) if e.lower() not in bajo]
    fallos = [n for n in NEGATIVAS if n in bajo]
    if faltan or fallos:
        return False, f"faltan {faltan}" + (f"; indicios de fallo {fallos}" if fallos else "")
    return True, "OK"


def _ocultar(texto: str) -> str:
    texto = re.sub(r"(sig|se|sp|sv|sr|st|spr)=[^&\s\"']+", r"\1=***", str(texto))
    return re.sub(r"eyJ[A-Za-z0-9_\-.]{20,}", "***", texto)


def _cargar_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(RAIZ / ".env", override=False)
    except ImportError:
        pass


def _pista(exc: BaseException) -> str:
    nombre, texto = type(exc).__name__, _ocultar(exc)
    if "CredentialUnavailable" in nombre or "az login" in texto.lower() or "AzureCliCredential" in texto:
        return "No hay sesión de Azure CLI válida: ejecuta `az login` (con --tenant si procede) y repite."
    if "401" in texto or "Unauthorized" in texto:
        return "401: el token no es válido para este recurso. Revisa el tenant de `az login`."
    if "403" in texto or "PermissionDenied" in texto or "AuthorizationFailed" in texto:
        return ("403: tu usuario no tiene permisos en el proyecto Foundry. Pide un rol que permita "
                "invocar agentes (p. ej. 'Azure AI User').")
    if "404" in texto or "NotFound" in nombre:
        return "404: revisa FOUNDRY_PROJECT_ENDPOINT y HOSTED_AGENT_NAME."
    if "puntero KEV" in texto or "SAS" in texto:
        return "El agente no pudo leer Azure Blob: el SAS de su conexión puede haber caducado."
    return f"{nombre}: {texto[:400]}"


def _texto_respuesta(resp) -> str:
    texto = getattr(resp, "output_text", None)
    if texto:
        return texto
    partes = []
    for item in getattr(resp, "output", None) or []:
        for c in getattr(item, "content", None) or []:
            if getattr(c, "text", None):
                partes.append(c.text)
    return "\n".join(partes)


def _pide_aprobacion(resp) -> list[str]:
    tipos = []
    for item in getattr(resp, "output", None) or []:
        tipo = getattr(item, "type", "")
        if "approval" in tipo or tipo == "function_call":
            tipos.append(f"{tipo}:{getattr(item, 'name', '')}")
    return tipos


def preguntar(cliente_openai, pregunta: str) -> tuple[str, float, list[str]]:
    inicio = time.perf_counter()
    resp = cliente_openai.responses.create(input=pregunta)
    return _texto_respuesta(resp), round(time.perf_counter() - inicio, 1), _pide_aprobacion(resp)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--prueba", choices=["todas", *PRUEBAS], default="todas")
    parser.add_argument("--pregunta", help="Pregunta libre (de solo lectura).")
    parser.add_argument("--esperar-version", help="Versión CISA esperada en la prueba 'cisa' (p. ej. 2026.11.10).")
    args = parser.parse_args()

    _cargar_env()
    endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    agente = os.environ.get("HOSTED_AGENT_NAME", "").strip() or AGENTE_POR_DEFECTO
    if not endpoint:
        print("Falta FOUNDRY_PROJECT_ENDPOINT (en .env o variable de entorno).")
        return 2

    from azure.ai.projects import AIProjectClient
    from azure.identity import AzureCliCredential

    tenant = os.environ.get("AZURE_TENANT_ID", "").strip() or None
    credencial = AzureCliCredential(tenant_id=tenant) if tenant else AzureCliCredential()
    proyecto = AIProjectClient(endpoint=endpoint, credential=credencial, allow_preview=True)

    print(f"Proyecto : {endpoint.split('/api/')[0]}")
    print(f"Agente   : {agente}")
    try:
        datos = proyecto.agents.get(agent_name=agente).as_dict()
        ultima = (datos.get("versions") or {}).get("latest") or {}
        print(f"Versión  : {ultima.get('version')} ({ultima.get('status')})")
    except Exception as exc:  # leer metadatos es opcional
        print("Versión  : no disponible ->", _pista(exc))

    try:
        cliente = proyecto.get_openai_client(agent_name=agente)
    except Exception as exc:
        print("ERROR al preparar el cliente:", _pista(exc))
        return 1

    if args.pregunta:
        casos = {"libre": {"pregunta": args.pregunta, "esperado": [], "explica": "Pregunta libre."}}
    else:
        casos = PRUEBAS if args.prueba == "todas" else {args.prueba: PRUEBAS[args.prueba]}
    if args.esperar_version and "cisa" in casos:
        casos["cisa"] = {**casos["cisa"], "esperado": casos["cisa"]["esperado"] + [args.esperar_version]}

    fallos = 0
    for nombre, caso in casos.items():
        print("\n" + "=" * 72)
        print(f"[{nombre}] {caso['explica']}")
        print("PREGUNTA :", caso["pregunta"])
        try:
            texto, segundos, aprobaciones = preguntar(cliente, caso["pregunta"])
        except Exception as exc:
            print("ERROR    :", _pista(exc))
            fallos += 1
            continue
        print(f"TIEMPO   : {segundos} s")
        if aprobaciones:
            print("AVISO    : el agente solicita aprobación humana", aprobaciones,
                  "-> este cliente NO aprueba nada y no se ha escrito nada.")
        print("RESPUESTA:")
        print(_ocultar(texto) or "(respuesta vacía)")
        if caso["esperado"]:
            ok, detalle = evaluar(texto, caso)
            print("COMPROBACIÓN:", detalle if ok else f"NO SUPERADA ({detalle}); revisa la respuesta")
            fallos += not ok
    print("\nResultado:", "sin incidencias" if not fallos else f"{fallos} prueba(s) con incidencias")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
