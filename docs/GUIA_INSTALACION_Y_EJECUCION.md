# Guía de instalación y ejecución · GitHub Codespaces

Con esta guía abres el proyecto en **GitHub Codespaces** (un entorno de VS Code en el navegador, ya preparado) y ejecutas los dos cuadernos. **No instalas nada en tu equipo y no inicias sesión en Azure con ninguna cuenta personal**: la conexión al modelo usa credenciales de una *aplicación* guardadas como secretos.

## Leyenda

| Símbolo | Significado |
|---|---|
| 🟢 | **Offline.** No usa Azure ni credenciales y no consume nada. |
| 🔴 | **Necesita credenciales y consume recursos de Azure** (llamadas al modelo de Foundry; coste muy bajo pero real). |

## Mapa del recorrido

| # | Paso | Tipo | Tiempo aprox. |
|---|---|---|---|
| 1 | Entrar al repositorio privado | 🟢 | 1 min |
| 2 | Crear el Codespace | 🟢 | 1 min |
| 3 | Esperar la preparación automática | 🟢 | 3-6 min |
| 4 | Verificar Python, dependencias y kernel | 🟢 | 2 min |
| 5 | Ejecutar el Cuaderno 1 | 🟢 | 10 min |
| 6 | Resultados esperados del Cuaderno 1 | 🟢 | — |
| 7 | Credenciales no interactivas (Codespaces Secrets) | 🔴 | 5 min |
| 8 | Endpoint y modelo de Foundry | 🔴 | 2 min |
| 9 | Ejecutar el Cuaderno 2 | 🔴 | 15 min |
| 10 | Bonus: DevUI en el puerto 8091 | 🔴 | 10 min |
| 11 | Detener o cerrar el Codespace | 🟢 | 1 min |

> **Si solo quieres ver el funcionamiento sin credenciales:** pasos 1 a 6. El Cuaderno 1 no necesita ningún secreto.

> **Quién hace qué:** los pasos 1-6 los hace cualquier persona con acceso al repositorio. El **paso 7** depende de quién tenga permisos de administración: si eres alumno y ya te han dicho que los secretos están configurados, salta al paso 9 (revisa el 8 solo para saber de dónde salen los valores). Si te toca configurarlos, está todo en los pasos 7 y 8 y en el **Anexo A**.

---

## Paso 1 · Entrar al repositorio privado 🟢

**Dónde:** el navegador, con la cuenta de GitHub que tiene acceso (la que te haya autorizado tu organización).

1. Abre <https://github.com/Amaia-AI-Experience-Center/entrepinares-formacion-agentes-m5>.
2. Si GitHub te pide autorizar el acceso de tu cuenta a la organización (*SSO*), acéptalo.

**Resultado esperado:** ves la página del repositorio con `README.md`, `notebooks`, `datos`, `docs`, etc. y arriba el botón verde **Code**.

| Si falla… | Qué hacer |
|---|---|
| `404 Not found` | No has iniciado sesión con la cuenta autorizada, o no tienes acceso. Cierra sesión, entra con la cuenta correcta o pide acceso a quien administra el repositorio. |
| Te pide autorizar *SAML SSO* | Pulsa *Authorize* con tu cuenta corporativa de la organización. |

---

## Paso 2 · Crear el Codespace 🟢

**Dónde:** la página del repositorio.

1. Pulsa el botón verde **Code**.
2. Abre la pestaña **Codespaces**.
3. Pulsa **Create codespace on main**.

**Resultado esperado:** se abre una pestaña nueva con *"Setting up your codespace…"* y después VS Code en el navegador.

> ⚠️ **Si vas a usar el Cuaderno 2:** los secretos (paso 7) deben estar definidos **antes** de crear el Codespace. Si los añades después, mira la nota del paso 7.

| Si falla… | Qué hacer |
|---|---|
| No aparece la pestaña **Codespaces** o el botón está desactivado | La organización no permite Codespaces para tu cuenta o este repositorio. Pide a quien administra la organización que lo habilite para ti. |
| Error de *billing* / cuota | Pide a la organización que revise la facturación de Codespaces o tu cuota. |
| Se queda cargando más de 10 minutos | Cierra la pestaña y vuelve a *Code → Codespaces* y reabre el mismo Codespace. |

---

## Paso 3 · Esperar la preparación automática 🟢

El Codespace instala **solo** las dependencias exactas del proyecto (97 paquetes). **No instala Azure CLI.** Tarda unos minutos la primera vez.

**Dónde:** la propia ventana de VS Code. Verás el progreso en la terminal que se abre sola.

**Resultado esperado:** al final de la terminal aparece:

```
Entorno coherente. Puedes abrir el Cuaderno 1.
== Codespace listo. Abre notebooks/entrepinares_01_fundamentos_offline.ipynb
```

**Cómo comprobar si hubo errores:** menú `F1` (o `Ctrl/Cmd + Shift + P`) → escribe **Codespaces: View Creation Log** → Enter. Busca líneas con `ERROR`.

| Si falla… | Qué hacer |
|---|---|
| Mensaje *"This codespace is in recovery mode"* | Falló la instalación. En `F1` → **Codespaces: Rebuild Container** → espera de nuevo. Suele ser un fallo de red momentáneo. |
| `ERROR: no se pudieron instalar las dependencias tras 3 intentos` | Hay un problema de red o de PyPI. Espera unos minutos y haz *Rebuild Container*. |
| La terminal no muestra nada | Abre una con `` Ctrl + ` `` y ejecuta el paso 4. |

---

## Paso 4 · Verificar Python, dependencias y kernel 🟢

**Dónde:** terminal del Codespace (`` Ctrl + ` `` si no se ve), en la carpeta raíz del repositorio (ya estás en ella).

```bash
python --version
python scripts/verificar_entorno.py
python -B -m unittest discover -s notebooks/tests
```

**Resultado esperado:**
- `Python 3.13.x`
- `verificar_entorno.py` muestra líneas `[OK]` y termina en `Entorno coherente. Puedes abrir el Cuaderno 1.` (al final lista de variables de Foundry: `NO definida` es normal si aún no hiciste el paso 7).
- Las pruebas terminan en `Ran 24 tests` y `OK`.

**Kernel:** abre `notebooks/entrepinares_01_fundamentos_offline.ipynb` (panel izquierdo → carpeta `notebooks`). Arriba a la derecha debe aparecer un kernel de **Python 3.13** (`/usr/local/bin/python`). Si pone *Select Kernel*:
1. Pulsa **Select Kernel** → **Python Environments** → `Python 3.13.x /usr/local/bin/python`.

Para comprobarlo, en una celda nueva: `import sys; print(sys.executable)` → `/usr/local/bin/python`.

| Si falla… | Qué hacer |
|---|---|
| `[FALLO] Paquetes del lock ... faltan` | La instalación no terminó. Terminal: `python -m pip install -r requirements-codespaces.lock.txt` y repite. |
| No aparece ningún kernel de Python | Instala las extensiones: pestaña de Extensiones → busca *Python* y *Jupyter* (de Microsoft) → *Install in Codespace*. Después `F1` → **Developer: Reload Window**. |
| Pregunta si confías en los autores del cuaderno | Es tu propio repositorio: pulsa **Trust**. |

---

## Paso 5 · Ejecutar el Cuaderno 1 completamente 🟢

**Dónde:** `notebooks/entrepinares_01_fundamentos_offline.ipynb`, en el editor de VS Code (no hace falta JupyterLab).

**Cómo:** en la barra superior del cuaderno pulsa **Run All**. Para leer con calma, ejecuta celda a celda con `Shift + Enter`.

**Resultado esperado:** todas las celdas se ejecutan sin error (aparece una marca verde ✔ a la izquierda de cada celda) y la **última** imprime:

```
INTEGRIDAD: SIN CAMBIOS en datos/
```

| Si falla… | Qué hacer |
|---|---|
| `ModuleNotFoundError` | Kernel equivocado: repite el selector del paso 4. |
| `StopIteration` en la primera celda | El cuaderno se abrió fuera del repositorio. Ábrelo desde el panel de archivos del Codespace. |
| `AssertionError: ¡Algún dato ha cambiado!` | Terminal: `git checkout -- datos` y repite. |
| Una celda se queda cargando | **Restart** (barra del cuaderno) y *Run All*. |

---

## Paso 6 · Resultados esperados del Cuaderno 1 🟢

| Apartado | Qué debes ver |
|---|---|
| 1. Preparación | `Descarga de CISA bloqueada ✔`, `Archivos de datos protegidos: 8`, `Modelo configurado: gpt-4.1-mini` |
| 2. Inventario | Tabla de **11 activos** (`IT-001` … `OT-004`) |
| 3.1 `consultar_activo` | Datos de `IT-004` (Firewall perimetral, PAN-OS 11.1.2) y `"encontrado": false` para `IT-999` |
| 3.2 Cribado | `(A) candidatas del producto : 13` y `(B) solo fabricante (otro) : 3` (Expedition) |
| 3.3 `evaluar_activo` | `CVE-2024-3400: estado=no_aplicable` para `IT-006` |
| 3.4 CISA | `modo: cache_desactualizada`, versión `2026.10.30`, aviso de descarga desactivada |
| 4. Contrato | Esquema de `DecisionOrquestador` y un error de validación al probar una ruta inventada |
| 5. Agentes | Herramientas de cada agente y `¿Alguna herramienta de escritura registrada? False` |
| 6. Grafo | Diagrama de 4 nodos (o su texto Mermaid) |
| 7. Mensajes entre agentes | Los textos que reciben `AgenteCorrelacion` y `AgenteCriticidad` y un `ERROR DE CONTEXTO` controlado |
| 8. Respuesta directa | Datos verificados de `IT-004` y "no existe" para `IT-999` |
| 9. Integridad | **`INTEGRIDAD: SIN CAMBIOS en datos/`** |

---

## Paso 7 · Credenciales no interactivas con Codespaces Secrets 🔴

Esta parte sirve para el Cuaderno 2 y DevUI. **No uses `az` ni inicies sesión con tu cuenta personal:** el workflow se autentica con una **aplicación de Microsoft Entra ID** (identidad de aplicación) cuyas credenciales llegan al Codespace como **variables de entorno**.

> 🔒 **Los secretos nunca se escriben en el repositorio, en los cuadernos ni en la terminal.** Se guardan en GitHub y el Codespace los recibe automáticamente.

### 7.1 Variables necesarias (nombres exactos)

| Variable | ¿Secreta? | Qué es |
|---|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | No | Endpoint de tu proyecto de Foundry (paso 8) |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | No | Nombre del despliegue del modelo (paso 8; normalmente `gpt-4.1-mini`) |
| `AZURE_TENANT_ID` | No | Identificador del tenant de la aplicación |
| `AZURE_CLIENT_ID` | No | Identificador de la aplicación |
| `AZURE_CLIENT_SECRET` | **Sí** | Secreto de cliente de la aplicación |

Los tres últimos los facilita el administrador de Azure (ver Anexo A). En GitHub se guardan **todos** como *Codespaces secrets* (GitHub no ofrece otra forma de pasar variables a un Codespace).

### 7.2 Dónde configurarlas en GitHub

**Opción recomendada (la configura una persona con permisos de administración del repositorio):**
1. Repositorio → **Settings**.
2. **Secrets and variables** → **Codespaces**.
3. **New repository secret** → escribe el **nombre exacto** y el valor → **Add secret**. Repite para las 5 variables.

**Opción alternativa (secretos propios, para quien tenga permiso de crear Codespaces pero no administre el repositorio):**
1. GitHub → tu foto (arriba a la derecha) → **Settings** → **Codespaces** → **Secrets** → **New secret**.
2. Nombre exacto, valor y, en *Repository access*, selecciona `entrepinares-formacion-agentes-m5`.

> ⏱️ Los secretos se cargan **cuando el Codespace arranca**. Si los añadiste con el Codespace ya abierto: *Stop Current Codespace* (paso 11) y vuelve a abrirlo; si siguen sin aparecer, crea un Codespace nuevo. *(Este comportamiento no se ha probado todavía en nuestro repositorio.)*

### 7.3 Comprobar que están definidas (sin ver los valores)

**Dónde:** terminal del Codespace.

```bash
python scripts/verificar_entorno.py
```
**Resultado esperado:** al final, las cinco variables aparecen como `definida` (y nunca se imprime su valor).

| Si falla… | Qué hacer |
|---|---|
| Alguna sale `NO definida` | Revisa que el **nombre** esté escrito exactamente igual, que el secreto esté en **Codespaces** (no en *Actions*) y que el repositorio tenga acceso. Reinicia el Codespace. |

> 🚨 Si alguna vez un secreto se muestra en pantalla, en un cuaderno o en un chat, **avisa al administrador para que lo regenere**.

---

## Paso 8 · Endpoint y modelo de Foundry 🔴

Son dos de las cinco variables del paso 7.

- **Endpoint** → `FOUNDRY_PROJECT_ENDPOINT`: en el portal de Microsoft Foundry, página principal de tu **proyecto** → *Endpoint del proyecto* (tiene la forma `https://<recurso>.services.ai.azure.com/api/projects/<proyecto>`).
- **Modelo** → `AZURE_AI_MODEL_DEPLOYMENT_NAME`: el **nombre del despliegue** (no el nombre genérico del modelo) en la sección de *Modelos + puntos de conexión* del proyecto. Por defecto `gpt-4.1-mini`.

**Comprobación:** en el Cuaderno 2, la primera celda muestra `FOUNDRY_PROJECT_ENDPOINT ✔ <tu-recurso>.services.ai.azure.com` (solo el nombre del servidor, nunca secretos).

---

## Paso 9 · Ejecutar el Cuaderno 2 🔴

**Antes:** pasos 7 y 8 hechos y Codespace **reiniciado** después de configurar los secretos. **Esto consume llamadas al modelo** (2-4 por pregunta).

**Dónde:** `notebooks/entrepinares_02_workflow_foundry.ipynb`, ejecutando **celda a celda** (`Shift + Enter`), con el mismo kernel Python 3.13.

### 9.1 Celdas que NO llaman al modelo (diagnóstico)

| Celda | Resultado esperado |
|---|---|
| 1. Preparación | `FOUNDRY_PROJECT_ENDPOINT ✔ <host>`, modelo `gpt-4.1-mini`, las tres variables `AZURE_*` con `✔ definida` y `Autenticación completa: ✔ sí` |
| 2. Comprobar la credencial *(opcional)* | `{'autenticacion_correcta': True, 'el_token_caduca_utc': '…'}` · Esta celda hace **una petición de token** a Microsoft Entra ID (no usa el modelo ni cuota) y **nunca imprime el token** |
| 3. Construir el workflow | Herramientas de cada agente (**ninguna de escritura**) y el diagrama del grafo |

Si algo falla aquí, **corrígelo antes de seguir** (tabla de más abajo).

### 9.2 Celdas que SÍ llaman al modelo (apartado 4 en adelante)

Cada una imprime una **traza**: `CONSULTA`, `RUTA`, `AGENTES`, `DECISION DEL ORQUESTADOR`, `HERRAMIENTAS LLAMADAS`, `TIEMPO` y `RESPUESTA FINAL`.

**Qué esperar (comportamiento previsto por el diseño; el modelo no es determinista y puede variar):**

| Caso | Pregunta | Ruta prevista |
|---|---|---|
| A | ¿Qué versión tiene IT-004? | Respuesta directa: **ningún agente especialista** |
| B | ¿Qué CVE candidatas aparecen para IT-004 en CISA KEV? | Orquestador → **Correlación** |
| C | Analiza las vulnerabilidades y la prioridad de IT-004. | Orquestador → Correlación → **Criticidad** |
| D | ¿Qué versión tiene IT-999? | Activo inexistente: **no** pasa por Correlación |
| E | ¿Está afectado IT-006 por CVE-2024-3400? … | Análisis completo; la CVE figura como **corregida** (inventario ficticio) |
| F | Actualiza ahora las novedades de CISA KEV. | **No se ejecuta nada**: explica que en solo lectura no se actualiza |

Al final: tabla comparativa, la sección de **variabilidad** (3 repeticiones de una pregunta ambigua) y `INTEGRIDAD: SIN CAMBIOS en datos/`.

> Los resultados reales dependen del modelo y pueden diferir en el texto. Comprueba la **ruta** y que la integridad final dice `SIN CAMBIOS`. Si en «HERRAMIENTAS LLAMADAS» aparece `(ninguna visible en los eventos)`, es una limitación de lo que expone el SDK en ese caso, no un fallo.

### 9.3 Errores habituales (los cuadernos muestran un mensaje en español, sin secretos)

| Mensaje | Causa y solución |
|---|---|
| `Faltan variables de autenticacion: …` | Falta alguna variable (solo se cita su **nombre**). Paso 7 y reinicia el Codespace. |
| `Falta el endpoint…` | Falta `FOUNDRY_PROJECT_ENDPOINT`. |
| `El client secret no es válido o ha caducado` | El administrador debe generar un secreto nuevo y actualizar `AZURE_CLIENT_SECRET`. |
| `No se encuentra la aplicación` / `Tenant no válido` | `AZURE_CLIENT_ID` o `AZURE_TENANT_ID` incorrectos. |
| `…no tiene permiso en el proyecto Foundry…` (401/403) | La aplicación existe pero no tiene rol sobre el proyecto: el administrador debe asignárselo (Anexo A). |
| `No se encuentra el modelo` (404) | Revisa `AZURE_AI_MODEL_DEPLOYMENT_NAME` y el endpoint. |
| `Límite de cuota (429)` | Espera un minuto y repite la celda; reduce `REPETICIONES`. |
| Otro error | Copia el mensaje completo que muestra la celda (no contiene secretos) y envíalo al responsable del curso. |

---

## Paso 10 · Bonus: DevUI en el puerto 8091 🔴

DevUI es una web de desarrollo para ver el grafo y los eventos. Se ejecuta en una **terminal aparte**, no en el cuaderno.

**Seguridad:** DevUI escucha solo dentro del Codespace y el puerto 8091 se reenvía de forma **privada** (solo tu cuenta de GitHub). **No cambies su visibilidad a *Public*.**

**Dónde:** terminal nueva (`` Ctrl + Shift + ` ``), en la raíz del repositorio.

**Opción A · con autenticación (por defecto, recomendada):**
```bash
export DEVUI_AUTH_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
echo "$DEVUI_AUTH_TOKEN"
python scripts/lanzar_devui.py --puerto 8091
```
La segunda línea muestra el token que acabas de crear: cópialo (no lo compartas ni lo guardes en un archivo).

**Opción B · sin autenticación** (solo mientras el puerto sea privado, para una demo):
```bash
python scripts/lanzar_devui.py --puerto 8091 --sin-auth
```

**Resultado esperado en la terminal:** `DevUI en http://127.0.0.1:8091 (solo localhost)` y `DevUI: SOLO LECTURA; acciones de escritura NO disponibles`.

**Abrir la web:** pestaña **Ports** (panel inferior de VS Code) → fila **8091** → icono del globo *Open in Browser*. Con la opción A, si la interfaz pide un token, pega el de `echo`. *(Comprobado en local: la API devuelve `401` sin token y `200` con él; el flujo de la interfaz web no se ha probado de principio a fin.)*

**Comprobación:** selecciona el workflow `WorkflowEntrepinaresSinPuentes`, envía `¿Qué versión tiene IT-004?` y verás el grafo de 4 nodos y la respuesta.

**Para parar:** `Ctrl + C` en esa terminal.

| Si falla… | Qué hacer |
|---|---|
| `Faltan variables de autenticacion…` / `Falta FOUNDRY_PROJECT_ENDPOINT` | Paso 7. |
| El puerto 8091 no aparece en **Ports** | Espera unos segundos tras arrancar; si no, *Forward a Port* → `8091`. |
| La web carga pero las preguntas fallan | Mira la terminal: es el mismo error de la tabla 9.3. |
| `Address already in use` | Otra instancia sigue abierta: `Ctrl + C` en la otra terminal, o usa `--puerto 8092`. |

---

## Paso 11 · Detener o cerrar el Codespace 🟢

- **Detener (conserva tus archivos):** esquina inferior izquierda de VS Code (el nombre del Codespace) → **Stop Current Codespace**. También se detiene solo tras un rato de inactividad.
- **Reabrirlo:** repositorio → **Code → Codespaces** → pulsa el Codespace existente.
- **Borrarlo al terminar** (libera almacenamiento): <https://github.com/codespaces> → `⋯` junto al Codespace → **Delete**.

No hagas `git commit`/`git push` desde el Codespace. Si has modificado algún archivo por error: `git status` y `git checkout -- <archivo>`.

---

## Lista final de comprobación

| ✔ | Comprobación | Cómo |
|---|---|---|
| ☐ | Codespace creado sin errores | Terminal final: `Codespace listo` |
| ☐ | Python y dependencias | `python scripts/verificar_entorno.py` → `Entorno coherente` |
| ☐ | Pruebas | `python -B -m unittest discover -s notebooks/tests` → `OK` |
| ☐ | Cuaderno 1 completo | Última celda: `INTEGRIDAD: SIN CAMBIOS en datos/` |
| ☐ | Secretos definidos | Paso 7.3: cinco variables `definida` |
| ☐ | Cuaderno 2 | Casos A–F con su ruta y `INTEGRIDAD: SIN CAMBIOS` al final |
| ☐ | Bonus DevUI | `Ports` → 8091 (privado) muestra el workflow |
| ☐ | Cierre | Codespace detenido |

---

## Anexo A · Para quien administra los secretos

- **Una aplicación dedicada** de Microsoft Entra ID (no credenciales personales) con un **secreto de cliente**. Crea una aplicación solo para esta formación, con la vida del secreto más corta posible, y revócalo al terminar.
- **Permisos mínimos:** a esa aplicación hay que asignarle, sobre el **proyecto/recurso de Foundry**, un rol que permita invocar el modelo (normalmente *Azure AI User*; confírmalo con el equipo de Azure). Sin esto, el Cuaderno 2 devuelve el error de permisos de la tabla 9.3.
- **Visibilidad del secreto:** un *Codespaces secret* a nivel de repositorio llega como variable de entorno a **todas** las personas que abran un Codespace de este repositorio, que podrían leerla. Por eso conviene una aplicación con permisos mínimos y secreto rotado.
- **Antes de la formación:** crea los 5 secretos (paso 7.2) y comprueba con una persona de prueba que `scripts/verificar_entorno.py` los muestra como `definida`.

## Anexo B · Estado de la validación (honestidad)

- ✅ **Verificado en Windows (sin Linux):** pruebas, Cuaderno 1 completo, Cuaderno 2 hasta su construcción del workflow con credenciales *simuladas*, DevUI (autenticación) y la instalación de un conjunto de dependencias equivalente.
- ✅ **Verificado sobre el papel para Linux:** el lock `requirements-codespaces.lock.txt` se resolvió para Linux x86_64 / Python 3.13 con las mismas versiones de Microsoft Agent Framework (ver `docs/CAMBIOS_RESPECTO_AL_ORIGINAL.md`).
- ❌ **Aún NO probado:** la creación real de un Codespace con este `devcontainer`, la instalación del lock en Linux, la ejecución de los cuadernos en Linux, el flujo con GitHub Codespaces Secrets y cualquier llamada real a Foundry. Los resultados del Cuaderno 2 son comportamiento previsto por el diseño.

## Anexo C · Alternativa secundaria: instalación local en Windows

Solo si no puedes usar Codespaces. Necesitas **Python 3.13** y **Git**.

```powershell
git clone https://github.com/Amaia-AI-Experience-Center/entrepinares-formacion-agentes-m5.git
cd entrepinares-formacion-agentes-m5
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-notebook.lock.txt
python scripts\verificar_entorno.py
```
Abre `notebooks/entrepinares_01_fundamentos_offline.ipynb` en VS Code (extensiones *Python* y *Jupyter*) y elige el kernel de `.venv`, o ejecuta `python -m jupyterlab` desde la raíz. Para el Cuaderno 2 define las cinco variables **en esa sesión de PowerShell** (`$env:NOMBRE = "valor"`) antes de abrirlo, sin escribir el secreto en ningún archivo del repositorio; los cuadernos también leen un `.env` local opcional (ignorado por Git), pero es menos seguro.
