"""Lectura de SOLO LECTURA de Azure Blob: KEV activo de Hosted V5 y manifiestos de informes.

Uso (raiz del repositorio, venv activado, tras `az login`):

    python scripts/consultar_kev_blob.py                       # version KEV activa
    python scripts/consultar_kev_blob.py --informe <ID>        # manifiesto de un informe publicado

Configuracion (.env o variables de entorno):
    ENTREPINARES_BLOB_ACCOUNT_URL   https://<cuenta>.blob.core.windows.net (obligatorio)
    AZURE_TENANT_ID                 opcional

Autenticacion: tu sesion de Azure CLI (Microsoft Entra ID), SIN SAS. Necesitas un
rol de lectura de datos sobre los contenedores (p. ej. "Storage Blob Data Reader");
`az login` por si solo no lo concede. Solo se leen manifiestos JSON pequenos.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CONTENEDOR_KEV = "entrepinares-kev"
CONTENEDOR_INFORMES = "entrepinares-informes"
PUNTERO = "control/version_activa.json"
ID_VALIDO = re.compile(r"\A\d{8}T\d{6}Z-[0-9a-f]{32}\Z")


def _cargar_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(RAIZ / ".env", override=False)
    except ImportError:
        pass


def _leer_json(servicio, contenedor: str, nombre: str) -> dict:
    datos = servicio.get_blob_client(contenedor, nombre).download_blob().readall()
    if len(datos) > 512 * 1024:
        raise ValueError(f"{nombre}: demasiado grande para un manifiesto")
    return json.loads(datos)


def _pista(exc: BaseException) -> str:
    nombre, texto = type(exc).__name__, str(exc).splitlines()[0][:200] if str(exc) else ""
    if "CredentialUnavailable" in nombre or "az login" in texto.lower():
        return "Sin sesión de Azure CLI: ejecuta `az login` y repite."
    if "AuthorizationPermissionMismatch" in str(exc) or "AuthorizationFailure" in str(exc) or "403" in texto:
        return "403: tu usuario no tiene un rol de lectura de datos en Blob (p. ej. 'Storage Blob Data Reader')."
    if "ResourceNotFound" in nombre or "BlobNotFound" in str(exc):
        return "No existe ese blob: revisa el identificador."
    return f"{nombre}: {texto}"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--informe", help="ID de publicación del informe (AAAAMMDDTHHMMSSZ-<32 hex>).")
    args = parser.parse_args()

    _cargar_env()
    cuenta = os.environ.get("ENTREPINARES_BLOB_ACCOUNT_URL", "").strip()
    if not cuenta:
        print("Falta ENTREPINARES_BLOB_ACCOUNT_URL (en .env o variable de entorno).")
        return 2
    from azure.identity import AzureCliCredential
    from azure.storage.blob import BlobServiceClient

    tenant = os.environ.get("AZURE_TENANT_ID", "").strip() or None
    servicio = BlobServiceClient(account_url=cuenta,
                                 credential=AzureCliCredential(tenant_id=tenant) if tenant else AzureCliCredential())
    try:
        if args.informe:
            if not ID_VALIDO.fullmatch(args.informe):
                print("Identificador con formato no válido.")
                return 2
            m = _leer_json(servicio, CONTENEDOR_INFORMES, f"informes/{args.informe}/manifest.json")
            f = m.get("fuentes", {})
            print(f"INFORME              : {m.get('id')} ({m.get('fecha_utc')})")
            print(f"Verificación completa: {m.get('verificacion_completa')}")
            print(f"Catálogo CISA usado  : {f.get('cisa_catalog_version')} (descargado {f.get('cisa_ultima_descarga')})")
            print(f"Origen KEV           : {f.get('origen_kev')}")
            print(f"Publicación KEV usada: {f.get('id_publicacion_kev')}")
            print(f"Cribado              : {f.get('cribado')}")
            for tipo, a in (m.get("archivos") or {}).items():
                print(f"Archivo {tipo:8}     : {a.get('blob', '')}  sha256={a.get('sha256', '')[:16]}…")
            return 0

        puntero = _leer_json(servicio, CONTENEDOR_KEV, PUNTERO)
        vid = puntero.get("version_id", "")
        print(f"PUNTERO ACTIVO       : {PUNTERO}")
        print(f"Publicación activa   : {vid}")
        print(f"Catálogo (puntero)   : {puntero.get('catalog_version')}")
        print(f"Activada (UTC)       : {puntero.get('fecha_activacion_utc')}")
        if ID_VALIDO.fullmatch(vid):
            man = _leer_json(servicio, CONTENEDOR_KEV, f"versiones/{vid}/manifest_local.json")
            print(f"Catálogo (manifiesto): {man.get('version_catalogo')} | validado={man.get('validado')}")
            print(f"Obtenido de CISA     : {man.get('ultima_obtencion_utc')} | modo={man.get('modo_fuente')}")
            print(f"Fuente               : {man.get('fuente')}")
            print(f"Archivos publicados  : {sorted(man.get('archivos') or {})}")
        return 0
    except Exception as exc:
        print("ERROR:", _pista(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
