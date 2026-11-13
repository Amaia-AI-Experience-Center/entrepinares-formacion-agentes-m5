# Cambios respecto al proyecto original

Este repositorio es una **copia didáctica independiente**. Del proyecto original solo se han copiado los archivos necesarios para ejecutar el workflow `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` y los cuadernos. Se han conservado las rutas de los módulos para no romper las importaciones.

## Archivos modificados (únicamente portabilidad y autenticación)

| Archivo | Cambio | Motivo |
|---|---|---|
| `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` | (1) `PROJECT_ENDPOINT` y `MODEL` se leen de `FOUNDRY_PROJECT_ENDPOINT` y `AZURE_AI_MODEL_DEPLOYMENT_NAME` (modelo por defecto `gpt-4.1-mini`). (2) Nueva `crear_credencial()` con `ClientSecretCredential` a partir de `AZURE_TENANT_ID`, `AZURE_CLIENT_ID` y `AZURE_CLIENT_SECRET`; `crear_cliente()` la usa en lugar de la credencial de Azure CLI y falla con un mensaje claro (solo nombres de variables) si falta algo | El original llevaba fijado el endpoint de la organización y se autenticaba con la sesión de Azure CLI de la persona. Aquí cada entorno usa su endpoint y una identidad de aplicación **no interactiva** |
| `agente_multiherramienta.py` | En `main()` (solo lo usa la evaluación original, no incluida) el endpoint, el modelo y la credencial salen del entorno | Mismo motivo |

**No se ha tocado** la lógica de enrutamiento, las instrucciones de los agentes, las herramientas, el grafo, los contratos, los tres agentes ni el modelo `gpt-4.1-mini`.

## Autenticación: qué admite realmente el SDK instalado

Análisis (inspección del código de `agent-framework-foundry 1.15.0` y `azure-ai-projects 2.7.0`, sin llamadas de red):

| Método | ¿Viable con la arquitectura actual? | Motivo |
|---|---|---|
| **API key** | **No** con `FoundryChatClient` | El cliente solo acepta `credential` de tipo token de Microsoft Entra ID (`TokenCredential`/`AsyncTokenCredential`); `AIProjectClient` exige `AsyncTokenCredential`. No hay parámetro `api_key`: el SDK construye internamente el cliente de OpenAI con un *proveedor de tokens* (ámbito `https://ai.azure.com/.default`). Usar una API key obligaría a **cambiar de cliente** (otra clase y otro tipo de endpoint) y no se ha verificado que conserve las capacidades del workflow |
| **`ClientSecretCredential`** (aplicación de Entra ID) | **Sí** | Es un `TokenCredential` aceptado por el cliente y se comporta igual que la credencial anterior desde el punto de vista del SDK. Es el método implementado |
| Azure CLI / dispositivo / interactivo | Descartado | Requieren sesión personal; prohibido en Codespaces |

Alternativas si no se pudiera crear una aplicación: un cliente basado en API key del *recurso* exigiría un cambio de cliente que debe autorizarse y validarse por separado (no se ha hecho).

## Entorno de Codespaces y dependencias

- `.devcontainer/devcontainer.json`: imagen `mcr.microsoft.com/devcontainers/python:1-3.13-bookworm`, extensiones *Python* y *Jupyter*, intérprete `/usr/local/bin/python`, **sin features** (sin Azure CLI), puerto **8091** (DevUI, privado). No incluye secretos, variables de construcción ni los puertos 8000/8088.
- `.devcontainer/post-create.sh`: instala `requirements-codespaces.lock.txt`, ejecuta `pip check` y `scripts/verificar_entorno.py`.
- **Lock para Linux** (`requirements-codespaces.lock.txt`, 97 paquetes): resuelto con `uv` para `manylinux_2_28` / Python 3.13 usando el lock de Windows como restricciones. Las versiones coinciden con el lock de Windows (incluidas las de Microsoft Agent Framework); solo se añaden `uvloop`, `pexpect` y `ptyprocess` (propios de Linux) y no hay `pywin32`/`pywinpty`/`colorama`. Se ha dejado fuera JupyterLab (los cuadernos se ejecutan en VS Code) y los paquetes de *hosting* y telemetría del lock de Windows, que el workflow no usa.
- El lock de Windows (`requirements-notebook.lock.txt`, 184 paquetes) **no** se ha modificado.

## Archivos copiados sin cambios (idénticos por SHA-256 al original)

`fuente_kev.py`, `inventario.py`, `priorizacion.py`, `correlacion.py`, `generar_informe.py`, `generar_html.py`, `cribado_kev.py`, `novedades_kev.py` y los ocho archivos de `datos/`: `inventario_demo.csv`, `kev_demo.json`, `cisa_kev_cache.json`, `cribado_kev.json`, `novedades_kev.json`, `evaluacion_nvd_piloto.json`, `historial_kev/catalogo_referencia.json`, `historial_kev/novedades_2026.10.28_a_2026.10.29.json`.

Los datos son: un inventario **ficticio** y una copia del catálogo público CISA KEV (versión 2026.10.30, obtenida el 3 de noviembre de 2026) que se queda **desactualizada a propósito**: las descargas están bloqueadas.

## Archivos nuevos

- `notebooks/entrepinares_01_fundamentos_offline.ipynb` y `notebooks/entrepinares_02_workflow_foundry.ipynb`.
- `notebooks/entrepinares_utils.py`: adaptador mínimo (preparación segura, trazas, comprobación de credenciales sin mostrar valores, huellas SHA-256). No contiene lógica de negocio.
- `notebooks/tests/test_entrepinares_utils.py`: pruebas sin red.
- `.devcontainer/`, `scripts/lanzar_devui.py`, `scripts/verificar_entorno.py`.
- `requirements.txt`, `requirements.lock.txt`, `requirements-notebook.lock.txt`, `requirements-codespaces.lock.txt`, `.env.example`, `.gitignore`, `.gitattributes`, `README.md` y estos documentos.

## Qué no se incluye

Hosted (V4/V5), Azure Blob, respaldos, ZIP históricos, scripts de mantenimiento, evaluaciones, informes generados, entornos virtuales, logs y cualquier archivo de configuración de Azure. El workflow que se construye aquí es **siempre de solo lectura** (`acciones_interactivas=False`).
