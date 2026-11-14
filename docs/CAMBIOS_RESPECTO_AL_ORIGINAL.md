# Cambios respecto al proyecto original

Este repositorio es una **copia didáctica independiente**. Del proyecto original solo se han copiado los archivos necesarios para ejecutar el workflow `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` y los cuadernos, conservando las rutas de los módulos para no romper importaciones.

## Archivos modificados (solo portabilidad)

| Archivo | Cambio | Motivo |
|---|---|---|
| `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` | `PROJECT_ENDPOINT` y `MODEL` se leen de `FOUNDRY_PROJECT_ENDPOINT` y `AZURE_AI_MODEL_DEPLOYMENT_NAME` (por defecto `gpt-4.1-mini`). Nueva `crear_credencial()`: `AzureCliCredential`, con `AZURE_TENANT_ID` opcional. `crear_cliente()` falla con un mensaje claro si falta el endpoint | El original llevaba el endpoint fijado en el código |
| `agente_multiherramienta.py` | En `main()` (no usado por el paquete) endpoint y modelo salen del entorno | Mismo motivo |

**No se ha tocado** el enrutamiento, las instrucciones, las herramientas, el grafo de cuatro nodos, los contratos ni el modelo `gpt-4.1-mini`. La autenticación es la misma que en el original: la sesión de Azure CLI del usuario.

## Archivos copiados sin cambios de contenido

`fuente_kev.py`, `inventario.py`, `priorizacion.py`, `correlacion.py`, `generar_informe.py`, `generar_html.py`, `cribado_kev.py`, `novedades_kev.py`: código idéntico al original; el repositorio los guarda con finales de línea LF (`.gitattributes`), por lo que su SHA-256 no coincide byte a byte con los originales en CRLF.

Los ocho archivos de `datos/` **sí** son idénticos por SHA-256 al original (marcados `-text` para que Git no los convierta): `inventario_demo.csv`, `kev_demo.json`, `cisa_kev_cache.json`, `cribado_kev.json`, `novedades_kev.json`, `evaluacion_nvd_piloto.json`, `historial_kev/catalogo_referencia.json`, `historial_kev/novedades_2026.10.28_a_2026.10.29.json`. El catálogo local es la versión 2026.10.30 (obtenida el 03/11/2026) y queda **desactualizado a propósito**: las descargas están bloqueadas.

## Archivos nuevos

- Cuadernos: `notebooks/entrepinares_01_fundamentos_offline.ipynb`, `notebooks/entrepinares_02_workflow_foundry.ipynb`.
- `notebooks/entrepinares_utils.py`: adaptador sin lógica de negocio (preparación segura, trazas MAF, informe local en `salidas/`, evidencias, huellas SHA-256). El informe usa los módulos originales; solo se redirige la carpeta de salida.
- `notebooks/tests/test_entrepinares_utils.py`: 21 pruebas sin red.
- `scripts/probar_hosted_v5.py` (cliente de solo lectura del agente Hosted), `scripts/consultar_kev_blob.py` (lectura de puntero y manifiestos con `az login`), `scripts/lanzar_devui.py`, `scripts/verificar_entorno.py`.
- `requirements.txt` (dependencias directas), `requirements.lock.txt` (184 paquetes exactos, Windows / Python 3.13, validado desde cero), `.env.example`, `.gitignore`, `.gitattributes`, `README.md` y la documentación de `docs/`.

## Qué no se incluye

El código de Hosted V4/V5 y sus despliegues, la administración de Azure Blob (publicar KEV o informes), SAS, respaldos, ZIP históricos, scripts de mantenimiento, evaluaciones, informes generados, entornos virtuales y logs. Tampoco el entorno de GitHub Codespaces, abandonado en favor de la instalación local en Windows.
