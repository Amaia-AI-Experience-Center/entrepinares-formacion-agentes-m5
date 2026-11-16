# Entrepinares · Formación en agentes de IA (Microsoft Agent Framework)

Repositorio **privado** de formación. Aprenderás cómo funciona un workflow de **tres agentes** construido con Microsoft Agent Framework (MAF): analiza vulnerabilidades de un **inventario ficticio** IT/OT cruzándolo con el catálogo público CISA KEV. El mismo workflow está desplegado como agente **Hosted V5** en Microsoft Foundry (versión publicada **v6**, que lee el catálogo KEV activo de Azure Blob).

## Inicio rápido (Windows, PowerShell)

```powershell
git clone https://github.com/Amaia-AI-Experience-Center/entrepinares-formacion-agentes-m5.git
cd entrepinares-formacion-agentes-m5
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
python scripts\verificar_entorno.py       # debe terminar en "Entorno coherente"
code .                                    # abre notebooks\ y ejecuta el Cuaderno 1
```

Para el Cuaderno 2, DevUI y Hosted: `az login` en tu ordenador, copia `.env.example` a `.env` y rellena el endpoint de tu proyecto Foundry. Todo el recorrido, con resultados esperados y soluciones: **[`docs/GUIA_INSTALACION_Y_EJECUCION.md`](docs/GUIA_INSTALACION_Y_EJECUCION.md)**.

## Qué contiene

| Qué | Dónde |
|---|---|
| **Cuaderno 1:** fundamentos, herramientas, cribado, criticidad, informe local, **sin Azure** | `notebooks/entrepinares_01_fundamentos_offline.ipynb` |
| **Cuaderno 2:** el workflow multiagente con `gpt-4.1-mini` en Foundry | `notebooks/entrepinares_02_workflow_foundry.ipynb` |
| Guía paso a paso (12 pasos, Windows) | `docs/GUIA_INSTALACION_Y_EJECUCION.md` |
| Hosted V5: ciclo, permisos y estado verificado | `docs/HOSTED_V5.md` |
| Cliente de solo lectura para Hosted V5 | `scripts/probar_hosted_v5.py` |
| Lectura del KEV activo y de manifiestos de informes en Blob | `scripts/consultar_kev_blob.py` |
| DevUI (bonus) y verificación del entorno | `scripts/lanzar_devui.py`, `scripts/verificar_entorno.py` |
| Workflow, módulos y datos ficticios | `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py`, `*.py`, `datos/` |
| Adaptador de los cuadernos y pruebas | `notebooks/entrepinares_utils.py`, `notebooks/tests/` |
| Diferencias con el proyecto original | `docs/CAMBIOS_RESPECTO_AL_ORIGINAL.md` |

## Autenticación y permisos

- Se usa **tu sesión de Azure CLI** (`AzureCliCredential`): no hay claves ni secretos en el repositorio.
- `az login` **no concede permisos**. Para el Cuaderno 2 necesitas un rol en el proyecto Foundry que permita usar el modelo; para Hosted, uno que permita invocar agentes; para leer Blob, uno de lectura de datos (`docs/HOSTED_V5.md`).
- Si un permiso falta, verás el error real; nada se sustituye por simulaciones.

## Garantías de seguridad

- Datos **ficticios** (inventario) o **públicos** (catálogo CISA KEV).
- El workflow local se construye **siempre en solo lectura**: no registra herramientas de escritura. El cliente Hosted nunca aprueba escrituras.
- Las **descargas de CISA están bloqueadas** y los cuadernos comprueban con SHA-256 que `datos/` no cambia. Los informes de ejercicio se guardan en `salidas/` (ignorada por Git).
- DevUI solo escucha en `127.0.0.1`, con autenticación por defecto.

## Pruebas

```powershell
python -B -m unittest discover -s notebooks/tests -v
```
21 pruebas **sin red ni credenciales** (adaptador, autenticación, informe local, cliente Hosted y estructura de los cuadernos). No sustituyen a ejecutar los cuadernos ni a las consultas reales.
