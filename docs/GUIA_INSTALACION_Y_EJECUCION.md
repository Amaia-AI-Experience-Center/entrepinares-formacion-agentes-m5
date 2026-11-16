# Guía de instalación y ejecución (Windows, 12 pasos)

Con esta guía montas el proyecto **desde cero** en tu ordenador Windows. Después ejecutas los dos cuadernos y DevUI, y consultas el agente **Hosted** (versión publicada **v6**). Todo lo necesario está en el repositorio.

## Local frente a Hosted V6

| | **Local**: cuadernos y DevUI (pasos 5-8) | **Hosted V6**: agente en Foundry (pasos 9-12) |
|---|---|---|
| Inventario | Ficticio, `datos/inventario_demo.csv` | El mismo inventario ficticio, empaquetado en el agente |
| Catálogo CISA KEV | **Histórico** fijo del repositorio: `2026.10.30`, 1766 CVE | **Activo** en Azure Blob, dinámico (el 16/11/2026: `2026.11.13`) |
| Correlación (cribado) | Se lee el cribado guardado en `datos/` | Se usa el cribado de la publicación activa en Blob, verificada con SHA-256 |
| Informes | Locales, en `salidas/` (ignorada por Git), con el Cuaderno 1 | Se publican en Blob (`informes/<id>/`) con su `manifest.json` |
| Actualización de CISA | Bloqueada: se trabaja con la copia histórica | Posible: crea una publicación nueva y mueve el puntero |
| Aprobación humana (HITL) | No aplica: no hay nada que aprobar | Obligatoria en cada escritura |
| Herramientas de escritura | **No registradas**: los agentes no pueden escribir | `actualizar_novedades_cisa_controlada` y `generar_informes_controlados`, disponibles solo con aprobación |

- **Local** es una demostración de **solo lectura** para las herramientas de los agentes. La única salida que genera son los informes de práctica en `salidas/`.
- **Hosted** dispone de herramientas de escritura, que un administrador aprueba una a una desde el **Playground** de Foundry.
- En esta guía, **Hosted solo se consulta**: el cliente `probar_hosted_v5.py` no aprueba nunca nada.

## Leyenda

| Símbolo | Tipo de paso |
|---|---|
| 🟢 | **Offline**: sin Azure, sin credenciales y sin coste. (La instalación descarga paquetes de internet.) |
| 🔵 | **Llamadas al modelo** de Foundry (`gpt-4.1-mini`) con tu `az login`. Consume recursos, con un coste muy bajo |
| 🟣 | **Consultas al agente Hosted o a Azure Blob** con tu `az login`, solo de lectura |
| 🟠 | **Operación administrativa con escritura**: no forma parte del recorrido; solo se explica |

> ⚠️ **`az login` te identifica, pero no concede permisos.** Para los pasos 🔵 y 🟣 tu usuario necesita roles concretos (paso 6 y `docs/HOSTED_V5.md`). Si te faltan, verás errores 401/403. El material **no** los sustituye por simulaciones.

Todos los comandos son de **PowerShell**. La «raíz del repositorio» es la carpeta `entrepinares-formacion-agentes-m5` que creas en el paso 1.

| # | Paso | Tipo | Tiempo |
|---|---|---|---|
| 1 | Clonar el repositorio privado | 🟢 | 2 min |
| 2 | Crear el entorno virtual con Python 3.13 | 🟢 | 5 min |
| 3 | Instalar las dependencias | 🟢 | 5-10 min |
| 4 | Comprobar el entorno | 🟢 | 1 min |
| 5 | Ejecutar el Cuaderno 1 | 🟢 | 15 min |
| 6 | Iniciar sesión con `az login` | 🔵🟣 | 5 min |
| 7 | Ejecutar el Cuaderno 2 | 🔵 | 15 min |
| 8 | Abrir DevUI en el puerto 8091 | 🔵 | 10 min |
| 9 | Consultar Hosted V6 con el cliente | 🟣 | 3 min |
| 10 | Comprobar la versión KEV activa y la correlación | 🟣 | 2 min |
| 11 | Entender la actualización CISA, HITL y los informes (sin escribir) | 🟢 lectura | 5 min |
| 12 | Consultar los resultados y la persistencia en Blob | 🟣 | 3 min |

---

## Paso 1 · Clonar el repositorio privado 🟢

**Comando** (PowerShell, en la carpeta donde quieras el proyecto):
```powershell
mkdir C:\Proyectos -ErrorAction SilentlyContinue
cd C:\Proyectos
git clone https://github.com/Amaia-AI-Experience-Center/entrepinares-formacion-agentes-m5.git
cd entrepinares-formacion-agentes-m5
```
> ⚠️ **Usa una ruta corta**, como `C:\Proyectos\entrepinares-formacion-agentes-m5`. Si clonas en una ruta larga, sobre todo dentro de `Documents` u OneDrive, la instalación del paso 3 puede fallar. Algunas dependencias, como JupyterLab, crean archivos con rutas muy largas, y Windows las rechaza si no tiene habilitado el soporte de rutas largas. El error es `OSError: [Errno 2] No such file or directory` y va acompañado de una pista sobre *Long Path support*.

**Resultado esperado:** `Cloning into 'entrepinares-formacion-agentes-m5'...` sin errores. Como el repositorio es **privado**, Git puede abrir el navegador para que inicies sesión en GitHub y autorices el SSO de la organización.

**Comprobación:** `dir` muestra `README.md`, `notebooks`, `datos`, `docs`, `scripts` y `requirements.lock.txt`.

| Error frecuente | Qué hacer |
|---|---|
| `git` no se reconoce | `winget install --id Git.Git -e` y reabre PowerShell. |
| `Repository not found` / `403` | Tu cuenta de GitHub no tiene acceso, o falta autorizar el SSO. Pide acceso a quien administra el repositorio. |

---

## Paso 2 · Crear el entorno virtual con Python 3.13 🟢

**Comandos** (en la raíz del repositorio):
```powershell
py -3.13 --version
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
**Resultado esperado:** `Python 3.13.x`, y el prompt empieza por `(.venv)`.

**Comprobación:**
```powershell
python --version
(Get-Command python).Source
```
Debe mostrar `Python 3.13.x` y una ruta que termina en `\.venv\Scripts\python.exe`.

| Error frecuente | Qué hacer |
|---|---|
| `py -3.13` no encuentra Python | `winget install --id Python.Python.3.13 -e` (64 bits; el lock está fijado para 3.13). Si tu empresa restringe la instalación, pide ayuda a TI. |
| «la ejecución de scripts está deshabilitada» | Solo para esta ventana: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y repite la activación. |
| La ruta de `python` no es la de `.venv` | El entorno no se activó: repite `.\.venv\Scripts\Activate.ps1`. |

> Cada vez que abras una terminal nueva para el proyecto: `cd` a la raíz y `.\.venv\Scripts\Activate.ps1`.

---

## Paso 3 · Instalar las dependencias 🟢

**Comando** (en la raíz, con `(.venv)`):
```powershell
python -m pip install -r requirements.lock.txt
```
Instala **184 paquetes con versión fija**: Microsoft Agent Framework, DevUI, Jupyter y las librerías de Azure. Descarga unos 350 MB.

**Resultado esperado:** `Successfully installed ...` al final.

**Comprobación:** `python -m pip check` responde `No broken requirements found.`

| Error frecuente | Qué hacer |
|---|---|
| `No matching distribution found` | No estás usando Python 3.13 de 64 bits: vuelve al paso 2. |
| Errores `SSL` / `ProxyError` | La red filtra PyPI. Pide el proxy a TI y usa `pip install --proxy http://proxy:puerto -r requirements.lock.txt`. No desactives la verificación SSL. |
| La instalación se corta | Repite el mismo comando. |
| `OSError … No such file or directory` con la pista *Long Path support* | La ruta del repositorio es demasiado larga (paso 1). Vuelve a clonar en una ruta corta, como `C:\Proyectos`, y repite desde el paso 2. |

---

## Paso 4 · Comprobar el entorno 🟢

**Comandos** (en la raíz, con `(.venv)`):
```powershell
python scripts\verificar_entorno.py
python -B -m unittest discover -s notebooks/tests -v
```
**Resultado esperado:**
- `verificar_entorno.py`: líneas `[OK]` y `Entorno coherente. Puedes abrir el Cuaderno 1.`
- Pruebas: `Ran 21 tests` y `OK`. No usan red ni credenciales.

**Comprobación:** las dos órdenes terminan sin `[FALLO]` ni `FAILED`.

| Error frecuente | Qué hacer |
|---|---|
| `[FALLO] Estás dentro de un entorno virtual` | Activa el entorno virtual (paso 2). |
| `[FALLO] Paquetes del lock … faltan` | Repite el paso 3. |
| `ModuleNotFoundError` en las pruebas | No estás en la raíz, o el entorno virtual no está activado. |

---

## Paso 5 · Ejecutar el Cuaderno 1 (fundamentos, offline) 🟢

**Comando:** abre el cuaderno en VS Code (extensiones **Python** y **Jupyter**):
```powershell
code .
```
1. Abre `notebooks\entrepinares_01_fundamentos_offline.ipynb`.
2. **Select Kernel → Python Environments →** `.venv\Scripts\python.exe`.
3. **Run All**, o celda a celda con `Shift + Enter`.

Si prefieres JupyterLab: `python -m jupyterlab` y abre la carpeta `notebooks`.

**Resultado esperado:**

| Apartado | Qué ves |
|---|---|
| 1. Preparación | `Descarga de CISA bloqueada ✔`, `Archivos de datos protegidos: 8` |
| 2. Inventario | Tabla de **11 activos** ficticios |
| 3. Herramientas | IT-004 (PAN-OS 11.1.2). IT-999 «no existe». Cribado con **(A) 13** candidatas y **(B) 3** solo por fabricante. IT-006 + CVE-2024-3400 → `no_aplicable`. CISA `cache_desactualizada`, versión `2026.10.30` (la copia **local** del repositorio) |
| 4. Contrato | Esquema de `DecisionOrquestador` y una ruta inventada rechazada |
| 5-6. Agentes y grafo | `¿Alguna herramienta de escritura registrada? False` y un grafo de 4 nodos |
| 7-8. Contexto y respuesta directa | Mensajes que recibe cada agente y los datos verificados de IT-004 |
| 9. Evidencias | Catálogo local `2026.10.30`, 1766 CVE, fuente y huellas SHA-256 |
| 10. Informe local | `salidas\informe_vulnerabilidades.md` y `.html` (ignorados por Git) |
| 11. Integridad | **`INTEGRIDAD: SIN CAMBIOS en datos/`** |

**Comprobación:** en una celda, `import sys; print(sys.executable)` debe terminar en `\.venv\Scripts\python.exe`. Abre `salidas\informe_vulnerabilidades.html` con doble clic: no aparece en `git status`.

| Error frecuente | Qué hacer |
|---|---|
| No aparece `.venv` como kernel | *Ctrl+Shift+P → Python: Select Interpreter →* `.venv\Scripts\python.exe` y recarga la ventana. |
| `StopIteration` en la primera celda | Abre el cuaderno desde la carpeta clonada. |
| `ModuleNotFoundError` | Has elegido un kernel equivocado. |
| `AssertionError: ¡Algún dato ha cambiado!` | `git checkout -- datos` y repite. |

---

## Paso 6 · Iniciar sesión con `az login` 🔵🟣

**Comandos** (en tu propio ordenador autorizado; instala Azure CLI con `winget install --id Microsoft.AzureCLI -e` si falta):
```powershell
az login
az account show --query "{tenant:tenantId, suscripcion:name}" -o table
Copy-Item .env.example .env
notepad .env
```
Si tu cuenta pertenece a varios tenants, usa `az login --tenant <id-o-dominio-del-tenant>` y añade `AZURE_TENANT_ID` en `.env`.

En `.env`, rellena estas variables y guarda:
- `FOUNDRY_PROJECT_ENDPOINT`: en el portal de Foundry → tu proyecto → *Endpoint del proyecto*.
- `ENTREPINARES_BLOB_ACCOUNT_URL`: necesaria para los pasos 10 y 12.
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`: solo si tu despliegue no se llama así.

El `.env` no contiene secretos y está en `.gitignore`.

> ⚠️ **Guarda `.env` en UTF-8 sin BOM.** El Bloc de notas lo hace por defecto (codificación «UTF-8»). En cambio, `Set-Content -Encoding utf8` y `Out-File` de **PowerShell 5.1** añaden un BOM, y entonces el archivo no se lee: verás `Falta FOUNDRY_PROJECT_ENDPOINT` aunque esté relleno. Si lo editaste así, en la raíz y con `(.venv)`, conviértelo:
> ```powershell
> python -c "import pathlib; p = pathlib.Path('.env'); p.write_text(p.read_text(encoding='utf-8-sig'), encoding='utf-8')"
> ```

**Resultado esperado:** el navegador se abre, inicias sesión y la tabla muestra el tenant y la suscripción de la formación.

**Comprobación:** `az account show` no da error. **Esto solo demuestra que tienes sesión, no que tengas permisos.** Los permisos se comprueban en la práctica:
- Usar el modelo (paso 7): un rol en el proyecto Foundry, p. ej. *Azure AI User*.
- Invocar el agente Hosted (paso 9): un rol que permita invocar agentes, p. ej. *Azure AI User*.
- Leer Blob (pasos 10 y 12): un rol de lectura de datos, p. ej. *Storage Blob Data Reader*.

Si te falta alguno, pídelo a quien administra los recursos 🟠.

| Error frecuente | Qué hacer |
|---|---|
| No se abre el navegador | `az login --use-device-code`. |
| Acceso condicional / MFA | Sigue la política de tu organización; si se bloquea, pide ayuda a TI. |
| Tenant o suscripción equivocados | `az account set --subscription "<nombre>"` o `az login --tenant …`. |

---

## Paso 7 · Ejecutar el Cuaderno 2 (Microsoft Agent Framework con Foundry) 🔵

**Comando:** abre `notebooks\entrepinares_02_workflow_foundry.ipynb` y ejecútalo celda a celda.

**Resultado esperado:**
- **Sin llamadas al modelo** (apartados 1-3):
  - `.env ✔` y `FOUNDRY_PROJECT_ENDPOINT ✔ <host>`.
  - `az` en el PATH ✔.
  - `{'token_obtenido': True, …}`: la sesión es válida, lo que no implica permisos.
  - Las herramientas de cada agente, ninguna de escritura.
- **Con llamadas al modelo** (apartado 4 en adelante): cada consulta imprime **RUTA, AGENTES, DECISIÓN, HERRAMIENTAS LLAMADAS, TIEMPO y RESPUESTA**. Esto es lo que se observó en la validación; puede variar, porque el modelo no es determinista:

| Caso | Pregunta | Ruta observada | Herramientas observadas |
|---|---|---|---|
| A | ¿Qué versión tiene IT-004? | Orquestador → Final | `consultar_activo` |
| B | ¿Qué CVE candidatas aparecen para IT-004 en CISA KEV? | Orquestador → Correlación → Final | `consultar_activo`, `consultar_cribado` |
| C | Analiza las vulnerabilidades y la prioridad de IT-004. | Orquestador → Correlación → Criticidad → Final | `+ evaluar_activo` |
| D | ¿Qué versión tiene IT-999? | Orquestador → Final | `consultar_activo` |
| E | ¿Está afectado IT-006 por CVE-2024-3400? … | Los tres agentes | `consultar_cribado(IT-006, CVE-2024-3400)`, `evaluar_activo` |
| F | Actualiza ahora las novedades de CISA KEV. | Orquestador → Final | ninguna: «La operación solicitada … no se ha ejecutado» |

Al final del cuaderno verás la tabla comparativa, la **variabilidad** (3 repeticiones) e **`INTEGRIDAD: SIN CAMBIOS en datos/`**.

**Comprobación:** el caso A responde 11.1.2. Si funciona, tienes permisos sobre el modelo.

| Error frecuente | Qué hacer |
|---|---|
| `Azure CLI no tiene sesión válida` | Repite el paso 6 y haz *Restart Kernel*. |
| `Falta el endpoint` | Revisa `.env` (paso 6): debe estar relleno y guardado en UTF-8 sin BOM. Después haz *Restart Kernel*. |
| `…no tiene permisos en el proyecto Foundry` (401/403) | Te falta el rol 🟠. |
| `No se encuentra el modelo` (404) | Revisa `AZURE_AI_MODEL_DEPLOYMENT_NAME`. |
| `Límite de cuota (429)` | Espera un minuto o baja `REPETICIONES`. |

---

## Paso 8 · Abrir DevUI en el puerto 8091 🔵

**Comando** (en una terminal **nueva**: raíz, `(.venv)` y tras `az login`):
```powershell
$env:DEVUI_AUTH_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:DEVUI_AUTH_TOKEN
python scripts\lanzar_devui.py --puerto 8091
```
Para una demo solo en tu equipo, sin autenticación: `python scripts\lanzar_devui.py --puerto 8091 --sin-auth`.

**Resultado esperado:** `DevUI en http://127.0.0.1:8091 (solo localhost)` y `DevUI: SOLO LECTURA; acciones de escritura NO disponibles`.

**Comprobación:**
1. Abre <http://127.0.0.1:8091>. Si pide token, pega el de la segunda línea y no lo compartas.
2. Comprueba que aparece el workflow `WorkflowEntrepinaresSinPuentes`.
3. Pregunta `¿Qué versión tiene IT-004?`: verás el grafo de 4 nodos.

| Error frecuente | Qué hacer |
|---|---|
| `Address already in use` | Usa `--puerto 8092` o cierra la otra instancia. |
| La web carga pero las preguntas fallan | Mira la terminal: los errores son los mismos que en el paso 7. |

Para cerrar DevUI: `Ctrl + C` en su terminal.

---

## Paso 9 · Consultar Hosted V6 con el cliente 🟣

**Comando** (raíz, `(.venv)`, tras `az login` y con `.env`):
```powershell
python scripts\probar_hosted_v5.py
```
Hace tres preguntas de **solo lectura** al agente desplegado, en **una sola sesión** fijada a la versión que recibe el tráfico (v6): inventario, estado CISA y correlación. No despliega nada ni aprueba ninguna escritura.

**Resultado esperado:**
- La cabecera muestra `Versión  : 6` y una línea `Sesión   : …`.
- `[inventario]`: IT-004, versión 11.1.2 → **COMPROBACIÓN: OK**.
- `[cisa]`: `Origen: azure_blob_verificado`, la versión del catálogo y el identificador de la publicación activa → **OK**.
- `[correlacion]`: reconoce CVE-2026-124194 en IT-007 (coincidencia solo por fabricante) → **OK**.
- Final: `Resultado: sin incidencias`.

**Comprobación:** apunta la **versión del catálogo** y la **publicación** que da `[cisa]`. En el paso 10 las comparas con Blob. El 16/11/2026 eran `2026.11.13` y `20261116T072220Z-cc181488…`, pero **el catálogo es dinámico**: cambia cuando un administrador aprueba una actualización CISA (paso 11). No esperes un valor fijo.

Para hacer otras preguntas: `python scripts\probar_hosted_v5.py --pregunta "¿Qué versión tiene IT-001?"`

| Error frecuente | Qué hacer |
|---|---|
| `403: tu usuario no tiene permisos…` | Necesitas un rol para invocar agentes en el proyecto 🟠. |
| `404` | Revisa `FOUNDRY_PROJECT_ENDPOINT` y `HOSTED_AGENT_NAME`. |
| `[cisa]` dice que no hay puntero o paquete, o menciona el SAS | El agente no ha podido leer Blob. El SAS de su conexión caduca el **03/12/2026**; avisa al administrador 🟠. |
| `AVISO: el agente solicita aprobación humana` | El cliente no aprueba nada, así que no se ha escrito nada. Reformula la pregunta como lectura. |

---

## Paso 10 · Comprobar la versión KEV activa y la correlación 🟣

**10.1 Leer el catálogo activo en Blob:**
```powershell
python scripts\consultar_kev_blob.py
```
Este comando lee, con tu `az login` y **sin SAS**, el **puntero** `control/version_activa.json` y el manifiesto de la publicación activa. Apunta el valor de la línea `Catálogo (puntero)`. Ejemplo del 16/11/2026:
```
Publicación activa   : 20261116T072220Z-cc181488b7be49688a2b1d280f6621e7
Catálogo (puntero)   : 2026.11.13
```

**10.2 Comprobar que el agente usa ese mismo catálogo.** Pasa a `--esperar-version` el valor apuntado. Con el ejemplo anterior:
```powershell
python scripts\probar_hosted_v5.py --prueba cisa --esperar-version 2026.11.13
```
Si Blob te ha mostrado otro catálogo, escribe ese valor en lugar de `2026.11.13`. También puedes dejar que PowerShell lo copie por ti:
```powershell
$catalogo = ((python scripts\consultar_kev_blob.py | Select-String "puntero\)").ToString() -split ":")[-1].Trim()
$catalogo
python scripts\probar_hosted_v5.py --prueba cisa --esperar-version $catalogo
```

**10.3 Comprobar la correlación con ese catálogo:**
```powershell
python scripts\probar_hosted_v5.py --prueba correlacion
```

**Resultado esperado:**
- 10.1: `Publicación activa`, `Catálogo (puntero)`, `Activada (UTC)` y `validado=True`, con fuente `cisagov/kev-data`.
- 10.2: `COMPROBACIÓN: OK` y `Resultado: sin incidencias`.
- 10.3: `COMPROBACIÓN: OK` (reconoce CVE-2026-124194 en IT-007).

**Comprobación:** la publicación y el catálogo de Blob **coinciden** con los que dio el agente en el paso 9. Eso demuestra que el agente desplegado lee el KEV vigente de Blob desde la **primera** pregunta, y no su copia empaquetada. La v6 corrige el defecto de caché de las versiones anteriores (ver `docs/HOSTED_V5.md`). La correlación de IT-007 confirma que el cribado se recalcula con ese catálogo.

| Error frecuente | Qué hacer |
|---|---|
| `403 … Storage Blob Data Reader` | Te falta un rol de lectura de datos en el almacenamiento 🟠. |
| `Falta ENTREPINARES_BLOB_ACCOUNT_URL` | Revisa `.env` (paso 6). |
| La versión de Blob y la del agente no coinciden | Puede que se haya activado una publicación nueva entre las dos consultas: repite el paso 9. |

---

## Paso 11 · Entender la actualización CISA, HITL y los informes (sin escribir) 🟢

En este paso **no ejecutas ningún comando**: solo lees cómo funcionan las escrituras. El detalle está en `docs/HOSTED_V5.md`.

El agente Hosted tiene **dos herramientas de escritura**, y las dos exigen **aprobación humana (HITL)**: el agente se detiene y devuelve una solicitud `mcp_approval_request`, y solo continúa si un administrador la aprueba explícitamente 🟠.

| Herramienta | Qué hace al aprobarse |
|---|---|
| `actualizar_novedades_cisa_controlada` | Descarga CISA KEV, valida y publica un paquete nuevo en `entrepinares-kev/versiones/<id>/` y **mueve el puntero** a esa publicación. |
| `generar_informes_controlados` | Genera los informes Markdown y HTML con el KEV **activo y verificado**, y los publica en `entrepinares-informes/informes/<id>/` con un `manifest.json` que registra qué publicación KEV usó. |

**Por qué el recorrido no las usa:**
- `scripts/probar_hosted_v5.py` **nunca aprueba** solicitudes.
- El workflow local (cuadernos y DevUI) no registra herramientas de escritura.
- El administrador hace estas operaciones desde el Playground de Foundry.

**Protección de la v6:** si el agente no puede leer un KEV verificado en Blob, la generación de informes **falla antes de escribir** y nunca usa el catálogo empaquetado.

**Ejemplo real (16/11/2026, pruebas autorizadas del propietario desde el Playground):**

| Hora (UTC) | Operación aprobada | Resultado |
|---|---|---|
| 07:12 | Actualización CISA | Publicación `20261116T071235Z-8bc180…` (2026.11.13), activa |
| 07:15 | Generación de informes | Informe `20261116T071514Z-936bfb65…`, generado con la publicación `8bc180…` |
| 07:22 | Actualización CISA | Publicación `20261116T072220Z-cc181488…` (2026.11.13), que pasa a ser la activa |

**Comprobación:** sabes explicar por qué el informe del paso 12 cita `8bc180…` mientras el puntero del paso 10 indica otra publicación posterior.

---

## Paso 12 · Consultar los resultados y la persistencia en Blob 🟣

**Comando:**
```powershell
python scripts\consultar_kev_blob.py --informe 20261116T071514Z-936bfb65c984419a9c24888ae0742944
```
Este es el informe generado por el agente Hosted v6 el 16/11/2026 tras la aprobación HITL.

**Resultado esperado:**
- `Verificación completa: True`.
- `Catálogo CISA usado: 2026.11.13`.
- `Origen KEV: azure_blob_verificado`.
- `Publicación KEV usada: 20261116T071235Z-8bc180…`.
- `Cribado: recalculado_offline_desde_blob_verificado`.
- Los dos archivos (`.md` y `.html`) con su huella SHA-256.

**Cómo leerlo:** cada informe guarda en su manifiesto **la publicación KEV vigente cuando se generó**. Este informe usó `8bc180…`, la activa a las 07:15. La publicación posterior de las 07:22 (`cc181488…`) pasó a ser la activa, pero eso no cambia el informe ya emitido. **No es un error de correlación**: es trazabilidad. Para saber qué usará una ejecución nueva, consulta el puntero (paso 10), no un informe antiguo.

Estructura en Blob:
```
entrepinares-kev/       control/version_activa.json   (puntero a la publicación activa)
                        versiones/<id>/…              (paquete verificado + manifest_local.json)
entrepinares-informes/  informes/<id>/manifest.json   (+ informe_vulnerabilidades.md y .html)
```

**Comprobación:**
- Los informes anteriores siguen ahí, porque cada publicación usa un `<id>` nuevo y nunca sobrescribe. Puedes comprobarlo con `python scripts\consultar_kev_blob.py --informe 20261112T122224Z-ef460b7657ca4e2ab756c478c722ff5a`, un informe del 12/11 con el catálogo 2026.11.10.
- Si un administrador te pasa un **enlace de descarga** de un informe, ese enlace lleva un SAS temporal (válido hasta el 03/12/2026 15:42 UTC) que da acceso de lectura a **todos** los informes. **Trátalo como una credencial**: no lo pegues en documentos, chats ni repositorios.

| Error frecuente | Qué hacer |
|---|---|
| `403` | Te falta el rol de lectura en el almacenamiento 🟠. |
| `Identificador con formato no válido` | Copia el ID completo: `AAAAMMDDTHHMMSSZ-` seguido de 32 caracteres hexadecimales. |
| No existe el informe | Revisa el ID; los informes nunca se borran desde este material. |

---

## Al terminar

| Proceso | Cómo |
|---|---|
| DevUI | `Ctrl + C` en su terminal |
| JupyterLab | `Ctrl + C` dos veces en su terminal |
| Kernel en VS Code | Barra del cuaderno → **Restart/Interrupt**, o cierra el cuaderno |
| Entorno virtual | `deactivate` |
| Sesión de Azure (opcional) | `az logout` |

No hagas `git commit` de `.env`, de `salidas\` ni de cuadernos con salidas. Si no has cambiado código, `git status` debe salir limpio.

## Lista final de comprobación

| ✔ | Comprobación |
|---|---|
| ☐ | `verificar_entorno.py` → `Entorno coherente`; 21 pruebas → `OK` |
| ☐ | Cuaderno 1 → `INTEGRIDAD: SIN CAMBIOS` e informe en `salidas\` |
| ☐ | Cuaderno 2 → casos A–F con su ruta y `INTEGRIDAD: SIN CAMBIOS` |
| ☐ | DevUI en `http://127.0.0.1:8091` |
| ☐ | Hosted V6 → `Resultado: sin incidencias` |
| ☐ | La publicación KEV activa en Blob coincide con la que da el agente |
| ☐ | El manifiesto del informe `20261116T071514Z-936bfb65…` se ha leído y verificado |
