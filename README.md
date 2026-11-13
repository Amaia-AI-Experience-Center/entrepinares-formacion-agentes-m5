# Entrepinares · Formación en agentes de IA (Microsoft Agent Framework)

Repositorio **privado** de formación. Aprenderás cómo funciona un workflow de **tres agentes** construido con Microsoft Agent Framework (MAF) que analiza vulnerabilidades de un **inventario ficticio** IT/OT cruzándolo con el catálogo público CISA KEV.

## Cómo empezar: GitHub Codespaces (recomendado)

1. Entra en el repositorio con tu cuenta autorizada.
2. **Code → Codespaces → Create codespace on main**.
3. Espera a que termine la preparación automática (terminal: `Codespace listo`).
4. Abre `notebooks/entrepinares_01_fundamentos_offline.ipynb` y pulsa **Run All**. 🟢 No necesita credenciales.

Para el **Cuaderno 2** hacen falta cinco *Codespaces Secrets* (conexión **no interactiva** a Foundry, sin Azure CLI ni inicio de sesión de cuentas personales). Todo el recorrido, con comprobaciones y soluciones a errores: **[`docs/GUIA_INSTALACION_Y_EJECUCION.md`](docs/GUIA_INSTALACION_Y_EJECUCION.md)**.

## Qué contiene

| Qué | Dónde |
|---|---|
| **Cuaderno 1:** fundamentos, **sin conexión** 🟢 | `notebooks/entrepinares_01_fundamentos_offline.ipynb` |
| **Cuaderno 2:** el workflow con Foundry 🔴 | `notebooks/entrepinares_02_workflow_foundry.ipynb` |
| **Guía de instalación y ejecución** | [`docs/GUIA_INSTALACION_Y_EJECUCION.md`](docs/GUIA_INSTALACION_Y_EJECUCION.md) |
| Entorno de Codespaces | `.devcontainer/` |
| El workflow | `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` |
| Módulos y datos ficticios | `*.py` de la raíz y `datos/` |
| Adaptador y pruebas | `notebooks/entrepinares_utils.py`, `notebooks/tests/` |
| DevUI (bonus) y verificación del entorno | `scripts/lanzar_devui.py`, `scripts/verificar_entorno.py` |
| Qué cambió respecto al proyecto original | [`docs/CAMBIOS_RESPECTO_AL_ORIGINAL.md`](docs/CAMBIOS_RESPECTO_AL_ORIGINAL.md) |

🟢 = funciona sin credenciales ni Azure · 🔴 = necesita credenciales y consume recursos de Azure.

## Autenticación

El workflow se autentica con una **aplicación de Microsoft Entra ID** (`ClientSecretCredential`), no con la sesión de ninguna persona. Variables (todas como *Codespaces Secrets*):

`FOUNDRY_PROJECT_ENDPOINT`, `AZURE_AI_MODEL_DEPLOYMENT_NAME`, `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`.

`.env.example` es solo una plantilla con valores ficticios. **Una API key no puede sustituir a esta credencial** con el cliente actual (`FoundryChatClient` solo admite credenciales de Microsoft Entra ID); los motivos están en `docs/CAMBIOS_RESPECTO_AL_ORIGINAL.md`.

## Garantías de seguridad

- Los datos son **ficticios** (inventario) o **públicos** (catálogo CISA KEV). No hay datos corporativos reales.
- El workflow se construye **siempre en solo lectura**: no registra herramientas de escritura.
- Las **descargas de CISA están bloqueadas** y cada cuaderno comprueba con SHA-256 que `datos/` no cambia.
- **No hay secretos en el repositorio**, ni se necesitan para crear el Codespace ni para el Cuaderno 1. Los cuadernos nunca imprimen valores secretos.
- DevUI solo escucha en `127.0.0.1`; el puerto 8091 se reenvía en modo **privado** y con autenticación por defecto.

## Estructura

```
├── README.md
├── .devcontainer/        devcontainer.json y post-create.sh (Codespaces)
├── docs/                 guía de instalación y cambios respecto al original
├── notebooks/            los dos cuadernos, el adaptador y sus pruebas
├── scripts/              verificar_entorno.py, lanzar_devui.py
├── datos/                inventario ficticio y copia del catálogo CISA KEV
├── orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py   el workflow
├── agente_multiherramienta.py, fuente_kev.py, inventario.py, ...    módulos
├── requirements-codespaces.lock.txt   instalación exacta en Linux (Codespaces)
├── requirements-notebook.lock.txt     instalación exacta en Windows (alternativa local)
├── requirements.lock.txt              solo el workflow, sin Jupyter (Windows)
├── requirements.txt                   dependencias directas (referencia)
└── .env.example
```

## Pruebas

```bash
python -B -m unittest discover -s notebooks/tests -v
```
Pruebas **sin red y sin credenciales**: comprueban el adaptador, la autenticación con credenciales simuladas, el `devcontainer`, los locks y la estructura de los cuadernos (limpios, sin secretos, de solo lectura). **No validan** servicios de Azure ni un Codespace real.
