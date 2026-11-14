# Guía de instalación y ejecución (Windows, paso a paso)

Con esta guía montas el proyecto **desde cero** en tu ordenador Windows y ejecutas los dos cuadernos, DevUI y la consulta al agente **Hosted V5**. Todo lo necesario está en el repositorio.

## Leyenda

| Símbolo | Tipo de paso |
|---|---|
| 🟢 | **Offline**: sin Azure, sin credenciales y sin coste. (La instalación descarga paquetes de internet.) |
| 🔵 | **Llamadas al modelo** de Foundry (`gpt-4.1-mini`) con tu `az login`: consume recursos, coste muy bajo |
| 🟣 | **Consultas al agente Hosted o a Azure Blob** con tu `az login`: solo lectura |
| 🟠 | **Operación administrativa**: no forma parte del recorrido; solo se describe |

> ⚠️ **`az login` te identifica, pero no concede permisos.** Para los pasos 🔵 y 🟣 tu usuario necesita roles concretos (ver paso 9 y `docs/HOSTED_V5.md`). Si faltan, verás errores 401/403: el material **no** los sustituye por simulaciones.

Todos los comandos son de **PowerShell**. «Raíz del repositorio» es la carpeta `entrepinares-formacion-agentes-m5` que crearás en el paso 1.

| # | Paso | Tipo | Tiempo |
|---|---|---|---|
| 1 | Clonar el repositorio | 🟢 | 2 min |
| 2 | Verificar Python 3.13, Git y Azure CLI | 🟢 | 5 min |
| 3 | Crear y activar el entorno virtual | 🟢 | 2 min |
| 4 | Instalar las dependencias exactas | 🟢 | 5-10 min |
| 5 | Ejecutar las comprobaciones | 🟢 | 1 min |
| 6 | Abrir VS Code / Jupyter | 🟢 | 2 min |
| 7 | Cuaderno 1 | 🟢 | 15 min |
| 8 | `az login` | 🔵🟣 | 2 min |
| 9 | Comprobar tenant y acceso a Foundry | 🔵 | 3 min |
| 10 | Cuaderno 2 | 🔵 | 15 min |
| 11 | Bonus: DevUI 8091 | 🔵 | 10 min |
| 12 | Consultar Hosted V5 | 🟣 | 3 min |
| 13 | Versión KEV activa y su origen | 🟣 | 1 min |
| 14 | Informe existente y almacenamiento Blob | 🟣 | 2 min |
| 15 | Cerrar los procesos | 🟢 | 1 min |

---

## Paso 1 · Clonar el repositorio 🟢

**Dónde:** PowerShell, en la carpeta donde quieras el proyecto (ejemplo: `C:\Proyectos`).

```powershell
mkdir C:\Proyectos -ErrorAction SilentlyContinue
cd C:\Proyectos
git clone https://github.com/Amaia-AI-Experience-Center/entrepinares-formacion-agentes-m5.git
cd entrepinares-formacion-agentes-m5
```
**Resultado esperado:** `Cloning into 'entrepinares-formacion-agentes-m5'...` sin errores. Es un repositorio **privado**: Git puede abrir el navegador para que inicies sesión en GitHub (y autorices el acceso SSO de la organización).

**Comprobación:** `dir` muestra `README.md`, `notebooks`, `datos`, `docs`, `scripts` y `requirements.lock.txt`.

| Si falla… | Qué hacer |
|---|---|
| `git` no se reconoce | Paso 2 (instala Git) y reabre PowerShell. |
| `Repository not found` / `403` | Tu cuenta de GitHub no tiene acceso o falta autorizar SSO. Pide acceso a quien administra el repositorio. |

---

## Paso 2 · Verificar Python 3.13, Git y Azure CLI 🟢

**Dónde:** cualquier PowerShell.

```powershell
py -3.13 --version
git --version
az --version
```
**Resultado esperado:** `Python 3.13.x`, `git version 2.x` y `azure-cli 2.x` en la primera línea de `az --version`.

**Si falta alguno** (si tu empresa restringe la instalación, pide ayuda a TI):
```powershell
winget install --id Python.Python.3.13 -e
winget install --id Git.Git -e
winget install --id Microsoft.AzureCLI -e
```
Cierra y abre PowerShell después de instalar.

| Si falla… | Qué hacer |
|---|---|
| `py -3.13` no encuentra Python | Instala Python **3.13 de 64 bits**: el lock está fijado para esa versión. |
| `winget` no existe | Instala desde python.org, git-scm.com y learn.microsoft.com/cli/azure. |

---

## Paso 3 · Crear y activar el entorno virtual 🟢

**Dónde:** raíz del repositorio.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
**Resultado esperado:** el prompt empieza por `(.venv)`.

**Comprobación:**
```powershell
python --version
(Get-Command python).Source
```
→ `Python 3.13.x` y una ruta que termina en `\.venv\Scripts\python.exe`.

| Si falla… | Qué hacer |
|---|---|
| «la ejecución de scripts está deshabilitada» | Solo para esta ventana: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y repite la activación. |
| La ruta de `python` no es la de `.venv` | No se activó: repite `.\.venv\Scripts\Activate.ps1`. |

> Cada vez que abras una terminal nueva para el proyecto: `cd` a la raíz y `.\.venv\Scripts\Activate.ps1`.

---

## Paso 4 · Instalar las dependencias exactas 🟢

**Dónde:** raíz del repositorio, con `(.venv)`.

```powershell
python -m pip install -r requirements.lock.txt
```
Instala **184 paquetes con versión fija** (Microsoft Agent Framework, DevUI, Jupyter, Azure). Descarga unos 350 MB desde PyPI.

**Resultado esperado:** `Successfully installed ...` al final.

**Comprobación:** `python -m pip check` → `No broken requirements found.`

| Si falla… | Qué hacer |
|---|---|
| `No matching distribution found` | No es Python 3.13 de 64 bits: pasos 2 y 3. |
| Errores `SSL` / `ProxyError` | La red filtra PyPI: pide a TI el proxy (`pip install --proxy http://proxy:puerto -r requirements.lock.txt`). No desactives la verificación SSL. |
| Se corta | Repite el mismo comando. |

---

## Paso 5 · Ejecutar las comprobaciones 🟢

**Dónde:** raíz del repositorio, con `(.venv)`.

```powershell
python scripts\verificar_entorno.py
python -B -m unittest discover -s notebooks/tests -v
```
**Resultado esperado:**
- `verificar_entorno.py`: líneas `[OK]` y `Entorno coherente. Puedes abrir el Cuaderno 1.`
- Pruebas: `Ran 21 tests` y `OK`. No usan red ni credenciales.

| Si falla… | Qué hacer |
|---|---|
| `[FALLO] Estás dentro de un entorno virtual` | Activa el venv (paso 3). |
| `[FALLO] Paquetes del lock … faltan` | Repite el paso 4. |
| `ModuleNotFoundError` en las pruebas | No estás en la raíz o el venv no está activado. |

---

## Paso 6 · Abrir VS Code / Jupyter 🟢

**Opción recomendada: VS Code**
1. Instala las extensiones **Python** y **Jupyter** (de Microsoft).
2. Desde la raíz, con `(.venv)`: `code .`
3. Abre `notebooks\entrepinares_01_fundamentos_offline.ipynb`.
4. Arriba a la derecha, **Select Kernel → Python Environments →** el intérprete `.venv` (`.venv\Scripts\python.exe`).

**Opción alternativa: JupyterLab**
```powershell
python -m jupyterlab
```
Se abre `http://localhost:8888/lab`; abre la carpeta `notebooks`. El kernel *Python 3 (ipykernel)* es el del venv si lanzaste JupyterLab con `(.venv)` activo.

**Comprobación del kernel:** en una celda nueva, `import sys; print(sys.executable)` → debe terminar en `\.venv\Scripts\python.exe`.

| Si falla… | Qué hacer |
|---|---|
| No aparece `.venv` en VS Code | *Ctrl+Shift+P → Python: Select Interpreter →* `.venv\Scripts\python.exe` y recarga la ventana. |
| `No module named jupyterlab` | Venv no activado o paso 4 incompleto. |

---

## Paso 7 · Cuaderno 1 (fundamentos, offline) 🟢

**Dónde:** `notebooks\entrepinares_01_fundamentos_offline.ipynb`.

**Cómo:** **Run All**, o celda a celda con `Shift + Enter` para leerlo.

**Resultado esperado:**

| Apartado | Qué ves |
|---|---|
| 1. Preparación | `Descarga de CISA bloqueada ✔`, `Archivos de datos protegidos: 8` |
| 2. Inventario | Tabla de **11 activos** ficticios |
| 3. Herramientas | IT-004 (PAN-OS 11.1.2); IT-999 «no existe»; cribado **(A) 13** candidatas y **(B) 3** solo fabricante; IT-006 + CVE-2024-3400 → `no_aplicable`; CISA `cache_desactualizada`, versión `2026.10.30` |
| 4. Contrato | Esquema de `DecisionOrquestador` y una ruta inventada rechazada |
| 5-6. Agentes y grafo | Herramientas de cada agente, `¿Alguna herramienta de escritura registrada? False` y grafo de 4 nodos |
| 7-8. Contexto y respuesta directa | Mensajes que recibe cada agente; datos verificados de IT-004 |
| 9. Evidencias | Catálogo `2026.10.30`, 1766 CVE, fuente y huellas SHA-256 |
| 10. Informe local | `salidas\informe_vulnerabilidades.md` y `.html` (ignorados por Git) |
| 11. Integridad | **`INTEGRIDAD: SIN CAMBIOS en datos/`** |

**Comprobación:** abre `salidas\informe_vulnerabilidades.html` con doble clic. `git status` no lo muestra (está ignorado).

| Si falla… | Qué hacer |
|---|---|
| `StopIteration` en la primera celda | El cuaderno no está dentro del repositorio: ábrelo desde la carpeta clonada. |
| `ModuleNotFoundError` | Kernel equivocado (paso 6). |
| `AssertionError: ¡Algún dato ha cambiado!` | `git checkout -- datos` y repite. |

---

## Paso 8 · Iniciar sesión con `az login` 🔵🟣

**Dónde:** PowerShell en **tu propio ordenador autorizado**.

```powershell
az login
```
Si tu cuenta pertenece a varios tenants, indica el de la formación:
```powershell
az login --tenant <id-o-dominio-del-tenant>
```
**Resultado esperado:** se abre el navegador, inicias sesión y la terminal muestra tu suscripción.

| Si falla… | Qué hacer |
|---|---|
| No se abre el navegador | `az login --use-device-code`. |
| Acceso condicional / MFA | Sigue la política de tu organización; pide ayuda a TI si se bloquea. |

---

## Paso 9 · Comprobar tenant y acceso a Foundry 🔵

**9.1 Tenant y suscripción** (raíz, `(.venv)`):
```powershell
az account show --query "{tenant:tenantId, suscripcion:name}" -o table
```
→ el tenant y la suscripción de la formación. Si no, `az account set --subscription "<nombre>"` o repite el paso 8 con `--tenant`.

**9.2 Configuración local:**
```powershell
Copy-Item .env.example .env
notepad .env
```
Rellena `FOUNDRY_PROJECT_ENDPOINT` (portal de Foundry → tu proyecto → *Endpoint del proyecto*) y, si tu despliegue no se llama así, `AZURE_AI_MODEL_DEPLOYMENT_NAME`. Para los pasos 12-14, `ENTREPINARES_BLOB_ACCOUNT_URL`. Guarda. El `.env` no contiene secretos y está en `.gitignore`.

**9.3 Acceso real al proyecto:** la prueba definitiva es el **caso A del Cuaderno 2** (paso 10). Si devuelve 401/403, necesitas un rol en el proyecto Foundry que permita usar el modelo (p. ej. *Azure AI User*). Pídelo a quien lo administra 🟠.

---

## Paso 10 · Cuaderno 2 (Microsoft Agent Framework con Foundry) 🔵

**Dónde:** `notebooks\entrepinares_02_workflow_foundry.ipynb`, celda a celda.

**10.1 Sin llamadas al modelo** (apartados 1-3): `.env ✔`, `FOUNDRY_PROJECT_ENDPOINT ✔ <host>`, `az` en el PATH ✔, `{'token_obtenido': True, …}` (sesión válida; no implica permisos) y las herramientas de cada agente, ninguna de escritura.

**10.2 Con llamadas al modelo** (apartado 4 en adelante). Cada consulta imprime **RUTA, AGENTES, DECISIÓN, HERRAMIENTAS LLAMADAS, TIEMPO y RESPUESTA**. Resultado de la validación del 14/11/2026 (puede variar, el modelo no es determinista):

| Caso | Pregunta | Ruta observada | Herramientas observadas |
|---|---|---|---|
| A | ¿Qué versión tiene IT-004? | Orquestador → Final | `consultar_activo` |
| B | ¿Qué CVE candidatas aparecen para IT-004 en CISA KEV? | Orquestador → Correlación → Final | `consultar_activo`, `consultar_cribado` |
| C | Analiza las vulnerabilidades y la prioridad de IT-004. | Orquestador → Correlación → Criticidad → Final | `+ evaluar_activo` |
| D | ¿Qué versión tiene IT-999? | Orquestador → Final | `consultar_activo` |
| E | ¿Está afectado IT-006 por CVE-2024-3400? … | Los tres agentes | `consultar_cribado(IT-006, CVE-2024-3400)`, `evaluar_activo` |
| F | Actualiza ahora las novedades de CISA KEV. | Orquestador → Final | ninguna: «La operación solicitada … no se ha ejecutado» |

Después: tabla comparativa, **variabilidad** (3 repeticiones; en la validación salió siempre `analisis_avanzado`, pero puede cambiar) e **`INTEGRIDAD: SIN CAMBIOS en datos/`**.

| Si falla… | Qué hacer |
|---|---|
| `Azure CLI no tiene sesión válida` | Paso 8 y *Restart Kernel*. |
| `Falta el endpoint` | Paso 9.2 y *Restart Kernel*. |
| `…no tiene permisos en el proyecto Foundry` (401/403) | Te falta el rol (paso 9.3) 🟠. |
| `No se encuentra el modelo` (404) | Revisa `AZURE_AI_MODEL_DEPLOYMENT_NAME`. |
| `Límite de cuota (429)` | Espera un minuto; baja `REPETICIONES`. |

---

## Paso 11 · Bonus: DevUI en el puerto 8091 🔵

**Dónde:** una **terminal nueva**, raíz del repositorio, `(.venv)` y tras `az login`.

**Con autenticación (recomendado):**
```powershell
$env:DEVUI_AUTH_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:DEVUI_AUTH_TOKEN
python scripts\lanzar_devui.py --puerto 8091
```
**Sin autenticación** (solo en tu equipo, para una demo):
```powershell
python scripts\lanzar_devui.py --puerto 8091 --sin-auth
```
**Resultado esperado:** `DevUI en http://127.0.0.1:8091 (solo localhost)` y `DevUI: SOLO LECTURA; acciones de escritura NO disponibles`. Abre <http://127.0.0.1:8091>; si pide token, pega el de la segunda línea (no lo compartas).

**Comprobación:** aparece el workflow `WorkflowEntrepinaresSinPuentes`; pregunta `¿Qué versión tiene IT-004?` y verás el grafo de 4 nodos. (Validado en local: sin token la API responde `401`, con token `200`, y solo escucha en `127.0.0.1`.)

| Si falla… | Qué hacer |
|---|---|
| `Address already in use` | Usa `--puerto 8092` o cierra la otra instancia. |
| La web carga pero las preguntas fallan | Mira la terminal: mismos errores que el paso 10. |

---

## Paso 12 · Consultar Hosted V5 🟣

**Dónde:** raíz, `(.venv)`, tras `az login` y con `.env` (paso 9.2).

```powershell
python scripts\probar_hosted_v5.py --esperar-version 2026.11.10
```
Hace tres preguntas de **solo lectura** al agente desplegado (versión publicada **v6**; no lo despliega ni aprueba ninguna escritura), en **una sola sesión**: inventario, versión CISA y correlación.

**Resultado de la validación del 14/11/2026:**
- `[inventario]` → «IT-004 … versión 11.1.2» → **COMPROBACIÓN: OK**
- `[cisa]` → `Version: 2026.11.10`, `Origen: azure_blob_verificado`, `Publicacion Blob: 20261113T135058Z-17735c10…` → **OK**
- `[correlacion]` → IT-007 / CVE-2026-124194 reconocida (coincidencia solo por fabricante) → **OK**

La v6 corrige el defecto de caché que hacía fallar las preguntas KEV en los primeros ~15 s de cada sandbox (ver `docs/HOSTED_V5.md`). Para verlo en una versión antigua: `--version 4`.

Otras preguntas: `python scripts\probar_hosted_v5.py --pregunta "¿Qué versión tiene IT-001?"`

| Si falla… | Qué hacer |
|---|---|
| `403: tu usuario no tiene permisos…` | Necesitas un rol para invocar agentes en el proyecto 🟠. |
| `404` | Revisa `FOUNDRY_PROJECT_ENDPOINT` y `HOSTED_AGENT_NAME`. |
| `AVISO: el agente solicita aprobación humana` | El cliente no aprueba nada: no se ha escrito nada. Reformula como pregunta de lectura. |

---

## Paso 13 · Versión KEV activa y su origen 🟣

```powershell
python scripts\consultar_kev_blob.py
```
Lee, con tu `az login` y sin SAS, el **puntero** y el manifiesto de la publicación activa.

**Resultado esperado (14/11/2026):** publicación `20261113T135058Z-17735c10…`, catálogo `2026.11.10`, `validado=True`, fuente `cisagov/kev-data`.

| Si falla… | Qué hacer |
|---|---|
| `403 … Storage Blob Data Reader` | Te falta un rol de lectura de datos en el almacenamiento 🟠. |
| `Falta ENTREPINARES_BLOB_ACCOUNT_URL` | Paso 9.2. |

---

## Paso 14 · Informe existente y almacenamiento Blob 🟣

```powershell
python scripts\consultar_kev_blob.py --informe 20261112T122224Z-ef460b7657ca4e2ab756c478c722ff5a
```
**Resultado esperado:** `Verificación completa: True`, `Catálogo CISA usado: 2026.11.10`, `Origen KEV: azure_blob_verificado` y `Publicación KEV usada: 20261112T122111Z-d4ec…`.

**Cómo leerlo:** cada informe guarda en su manifiesto **qué publicación KEV** usó. La de este informe es **anterior** a la activa del paso 13, aunque las dos sean del catálogo 2026.11.10. Por eso la versión de un informe antiguo **no** demuestra qué usa una ejecución nueva. Estructura en Blob:

```
entrepinares-kev/       control/version_activa.json   (puntero)
                        versiones/<id>/…              (paquete verificado + manifest_local.json)
entrepinares-informes/  informes/<id>/manifest.json   (+ informe .md y .html)
```
Generar un informe nuevo en Hosted es una **escritura con aprobación humana** 🟠 y no forma parte de esta guía.

---

## Paso 15 · Cerrar los procesos 🟢

| Proceso | Cómo |
|---|---|
| DevUI | `Ctrl + C` en su terminal |
| JupyterLab | `Ctrl + C` dos veces en su terminal |
| Kernel en VS Code | Barra del cuaderno → **Restart/Interrupt**, o cierra el cuaderno |
| Entorno virtual | `deactivate` |
| Sesión de Azure (opcional) | `az logout` |

No hagas `git commit` de `.env`, `salidas\` ni de cuadernos con salidas (`git status` debe salir limpio si no has cambiado código).

---

## Lista final de comprobación

| ✔ | Comprobación |
|---|---|
| ☐ | `python scripts\verificar_entorno.py` → `Entorno coherente` |
| ☐ | 21 pruebas → `OK` |
| ☐ | Cuaderno 1 → `INTEGRIDAD: SIN CAMBIOS` e informe en `salidas\` |
| ☐ | Cuaderno 2 → casos A–F con ruta y `INTEGRIDAD: SIN CAMBIOS` |
| ☐ | DevUI en `http://127.0.0.1:8091` |
| ☐ | Hosted V5: inventario OK; CISA/correlación según el estado de `docs/HOSTED_V5.md` |
| ☐ | KEV activo y manifiesto de informe leídos |
