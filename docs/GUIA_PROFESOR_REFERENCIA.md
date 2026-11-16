# Guía del profesor · Referencia técnica · Entrepinares M5

Material de **referencia exhaustivo**, celda a celda, para preparar el Módulo 5: agentes con Microsoft Agent Framework (MAF), el workflow de tres agentes y su despliegue *Hosted* en Microsoft Foundry.

> Para dar la clase usa el guion operativo **`docs/GUIA_PROFESOR.md`**. Este documento recoge las explicaciones técnicas, los detalles de implementación y las respuestas completas a las preguntas de los alumnos.

- **Para quién:** quien imparte la sesión, no el alumno.
- **Qué complementa:** la instalación y los comandos paso a paso están en `docs/GUIA_INSTALACION_Y_EJECUCION.md` (la «guía IKEA», 12 pasos). Aquí no se repiten: se citan por número de paso.
- **De dónde salen los resultados:** del código actual del repositorio y de ejecuciones reales:
  - Cuadernos 1 y 2: clon limpio del 16/11/2026, commit `2e67587`.
  - Hosted: comprobaciones de solo lectura del 16/11/2026.
  - Cuando un resultado depende del modelo de lenguaje, se indica que **puede variar**.

> **Dos catálogos CISA KEV distintos, y conviene repetirlo durante la sesión:**
> - **Catálogo histórico del repositorio** (`datos/cisa_kev_cache.json`): versión **2026.10.30**, 1766 CVE. Es fijo y lo usan los Cuadernos 1 y 2, DevUI y los informes locales.
> - **Catálogo activo en Azure Blob**: dinámico. Solo lo usa el agente **Hosted**. El 16/11/2026 era la versión **2026.11.13**, 1781 CVE, publicación `20261116T072220Z-cc181488…`. Cambia cada vez que un administrador aprueba una actualización CISA.

---

## Índice

1. [Preparación de la sesión](#1-preparación-de-la-sesión)
2. [Agenda y tiempos](#2-agenda-y-tiempos)
3. [Apertura: el caso de uso IT/OT](#3-apertura-el-caso-de-uso-itot)
4. [Parte A · Fundamentos y Cuaderno 1](#4-parte-a--fundamentos-y-cuaderno-1)
5. [Parte B · MAF y Cuaderno 2](#5-parte-b--maf-y-cuaderno-2)
6. [Parte C · Hosted V6](#6-parte-c--hosted-v6)
7. [Si algo falla durante la sesión](#7-si-algo-falla-durante-la-sesión)
8. [Preguntas frecuentes de los alumnos](#8-preguntas-frecuentes-de-los-alumnos)
9. [Mensajes clave para el cierre](#9-mensajes-clave-para-el-cierre)
10. [Anexo: mapa del código](#10-anexo-mapa-del-código)

---

## 1. Preparación de la sesión

### 1.1 Prerrequisitos que debes comprobar (la víspera)

| Comprobación | Cómo | Resultado esperado |
|---|---|---|
| Entorno instalado en una ruta corta | Guía IKEA, pasos 1-4 | `Entorno coherente`, `Ran 21 tests … OK` |
| Cuaderno 1 completo | Run All | `INTEGRIDAD: SIN CAMBIOS en datos/` |
| Sesión de Azure y `.env` | Guía IKEA, paso 6 | `az account show` muestra el tenant de la formación |
| **Permiso sobre el modelo** | Cuaderno 2, caso A | Ruta `AgenteOrquestador -> RespuestaFinal` y versión 11.1.2 |
| **Permiso para invocar Hosted** | `python scripts\probar_hosted_v5.py` | `Versión  : 6` y `Resultado: sin incidencias` |
| **Permiso de lectura en Blob** | `python scripts\consultar_kev_blob.py` | `Publicación activa` y `validado=True` |
| SAS del agente vigente | Fecha | Caduca el **03/12/2026 15:42 UTC**. Después, Hosted no puede leer el KEV hasta que se renueve |

`az login` no concede permisos: si una comprobación da 401/403, pide el rol antes de la sesión. Los roles están en el paso 6 de la guía IKEA.

### 1.2 Copias de respaldo con resultados (recomendado)

Los cuadernos del repositorio se guardan **sin salidas**. Para tener un plan B si falla la red, genera la víspera una copia HTML ejecutada en `salidas\`, que Git ignora:

```powershell
python -m jupyter nbconvert --to html --execute notebooks\entrepinares_01_fundamentos_offline.ipynb --output-dir salidas
python -m jupyter nbconvert --to html --execute notebooks\entrepinares_02_workflow_foundry.ipynb --output-dir salidas
```

- El primero no usa red.
- El segundo llama al modelo, con un coste bajo.
- Ninguno modifica los cuadernos, que siguen sin salidas.

Guarda también la salida de `probar_hosted_v5.py` en un archivo de texto dentro de `salidas\`.

### 1.3 Ventanas y archivos preparados

| Ventana | Contenido |
|---|---|
| VS Code (1) | Cuaderno 1 abierto, kernel `.venv` seleccionado y salidas limpias |
| VS Code (2) | Cuaderno 2 abierto con el kernel `.venv` |
| VS Code, pestañas de código | `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` (líneas clave en el [anexo](#10-anexo-mapa-del-código)), `correlacion.py`, `datos/inventario_demo.csv` |
| PowerShell A | Raíz del repositorio, `(.venv)` activo, para Hosted y Blob |
| PowerShell B | Lista para DevUI (`$env:DEVUI_AUTH_TOKEN` ya definido) |
| Navegador | `salidas\informe_vulnerabilidades.html` (tras el Cuaderno 1) y, si das el bonus, `http://127.0.0.1:8091` |
| Documento | `docs/HOSTED_V5.md`, con las evidencias de Hosted |

### 1.4 Qué ejecutar en directo y qué mostrar con resultados ya verificados

| Bloque | En directo | Con resultados verificados |
|---|---|---|
| Cuaderno 1 | **Todo**: no usa red y tarda segundos | — |
| Cuaderno 2, apartados 1-3 | Sí | — |
| Cuaderno 2, casos A–F | Sí; como mínimo A, C y F | El resto, si vas justo de tiempo |
| Cuaderno 2, variabilidad | Sí: el resultado varía y eso es lo que se enseña | — |
| DevUI | Opcional | Capturas, si no hay tiempo |
| Hosted: cliente de lectura | Sí: `probar_hosted_v5.py` y `consultar_kev_blob.py` | — |
| Hosted: actualización CISA, HITL e informe | **Nunca en directo** | Evidencias del 16/11/2026 (`docs/HOSTED_V5.md`) |

---

## 2. Agenda y tiempos

| Bloque | Contenido | Tiempo |
|---|---|---|
| Apertura | Caso de uso IT/OT, objetivos y reglas del juego | 10 min |
| **Parte A** | Cuaderno 1: datos, herramientas, contrato, grafo, evidencias, informe e integridad | 60 min |
| Descanso | | 10 min |
| **Parte B** | Conceptos de MAF (15 min), Cuaderno 2 (50 min) y DevUI (10 min) | 75 min |
| Descanso | | 10 min |
| **Parte C** | Hosted V6: arquitectura, Blob, HITL, informes, cliente y defecto de caché | 40 min |
| Cierre | Preguntas y mensajes clave | 15 min |
| **Total** | | **≈ 3 h 40 min** |

**Versión reducida (2 h):**
- Parte A: 35 min, solo apartados 2, 3, 4, 6, 9 y 11.
- Parte B: 50 min, casos A, C, F y variabilidad; sin DevUI.
- Parte C: 25 min, cliente en directo más la cronología del 16/11.
- Cierre: 10 min.

---

## 3. Apertura: el caso de uso IT/OT

**Objetivo didáctico.** Que el alumno sepa qué problema resuelve la demo y qué **no** pretende resolver.

**Qué explicar.**
- **El problema.** Entrepinares es una empresa real, pero el inventario de prácticas es **ficticio**: no corresponde a sus equipos. En la demo, la empresa tiene activos IT, como servidores de impresión y firewalls, y OT, como pasarelas industriales Siemens y controladores. Quiere saber qué vulnerabilidades **explotadas activamente** podrían afectarles.
- **CISA KEV** (*Known Exploited Vulnerabilities*). Es el catálogo público de la agencia estadounidense CISA con las CVE que se sabe que se están explotando. Es una fuente de **priorización**, no un escáner.
- **El flujo de la demo:**
  1. Leer el inventario.
  2. Cruzar fabricante y producto con KEV (cribado).
  3. Aplicar reglas deterministas a tres CVE concretas (criticidad).
  4. Explicar el resultado con agentes.
- **Lo que NO es:** no escanea equipos, no se conecta a sistemas reales y el inventario es ficticio. Una coincidencia con KEV es una **candidata**, no una vulnerabilidad confirmada.

**Guion oral sugerido.**
> «Imaginad que sois el equipo de seguridad de una planta industrial. Cada semana CISA publica nuevas vulnerabilidades que se están explotando de verdad. La pregunta es: ¿alguna nos toca? Vamos a construir un sistema que lo responda con tres agentes de IA. Pero antes de dar a la IA la palabra, vamos a ver qué parte del trabajo hace código normal y predecible, porque esa es la parte en la que podemos confiar.»

**Qué enseñar.** `datos/inventario_demo.csv` (11 filas) y el `README.md`.

**Preguntas para los alumnos.**
- *¿Por qué no basta con que un LLM lea el catálogo y diga qué nos afecta?* → Porque puede inventar o mezclar datos. Las comprobaciones deben ser deterministas y trazables; el LLM decide qué herramienta usar y redacta el resultado.

**Tiempo.** 10 min.

---

## 4. Parte A · Fundamentos y Cuaderno 1

Cuaderno: `notebooks/entrepinares_01_fundamentos_offline.ipynb`. Tiene 32 celdas, 15 de ellas de código. Se ejecuta sin red ni credenciales, en unos segundos.

### A.0 Introducción al cuaderno (celda de texto inicial)

- **Objetivo didáctico.** Fijar las condiciones: sin red, sin Azure, sin modificar datos.
- **Qué explicar.** El cuaderno usa los **módulos originales** del proyecto (`inventario.py`, `agente_multiherramienta.py`, `correlacion.py`…) a través de un adaptador pequeño, `notebooks/entrepinares_utils.py`. Las herramientas se llaman **directamente**, sin LLM.
- **Guion oral sugerido.** «Este cuaderno no gasta ni un céntimo ni necesita Azure. Vamos a abrir el capó: veremos las piezas que luego usarán los agentes.»
- **Tiempo.** 2 min.

### A.1 Preparación segura (apartado 1, celda de código 1)

- **Objetivo didáctico.** Entender que lo primero es **proteger los datos** y que la demo es de solo lectura.
- **Qué explicar.** La celda:
  1. Localiza la raíz del repositorio buscando `datos/inventario_demo.csv`.
  2. Calcula la huella SHA-256 de los 8 archivos de `datos/` con `u.huellas_datos()`.
  3. Carga el módulo del workflow con `u.preparar_entorno(cargar_env=False)`, que llama a `bloquear_descargas_cisa()`.
  4. Comprueba el bloqueo intentando `fuente_kev.descargar_catalogo()`.

  ¿Por qué hace falta bloquear? `fuente_kev.obtener_catalogo()` **descarga y reescribe** `datos/cisa_kev_cache.json` si la copia tiene más de 24 h (`DURACION_CACHE`). `bloquear_descargas_cisa()` sustituye la función de descarga por una que lanza un error.

  Es un parche de módulo, **no** un control de seguridad: afecta a todo el proceso Python y no cubre otros módulos que usen la red directamente. El *docstring* de la función lo dice así.
- **Guion oral sugerido.** «Antes de tocar nada, hacemos una foto de los datos con SHA-256 y desconectamos la descarga de CISA. ¿Por qué? Porque el código original, si ve el catálogo viejo, lo descarga y lo sobrescribe. Hoy no queremos que nada cambie sin que lo decidamos.»
- **Qué ejecutar.** Celda de código 1.
- **Resultado esperado.**
  ```
  Descarga de CISA bloqueada ✔  -> Descarga CISA desactivada en el workflow experimental.
  Archivos de datos protegidos: 8
  Módulo del workflow cargado : orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION
  Modelo configurado          : gpt-4.1-mini
  ```
- **Qué observar.** El modelo aparece configurado, pero **no se usa** en este cuaderno.
- **Preguntas para los alumnos.**
  - *¿Qué pasaría sin el bloqueo?* → Con la caché caducada, la primera consulta CISA intentaría descargar el catálogo y reescribir `datos/cisa_kev_cache.json`, con lo que la comprobación final de integridad fallaría.
- **Problemas habituales.**
  - `StopIteration`: el cuaderno no está dentro del repositorio clonado.
  - `ModuleNotFoundError`: el kernel no es el del `.venv`.
- **Tiempo.** 4 min.

### A.2 El inventario ficticio (apartado 2, celda de código 2)

- **Objetivo didáctico.** Conocer los datos de entrada y los campos que se cruzan con KEV.
- **Qué explicar.**
  - `leer_inventario()` devuelve 11 activos.
  - Los campos que importan para el cruce son `fabricante`, `producto` y `version`.
  - Hay dos campos más que la tabla no muestra pero que usan las reglas: `configuracion`, con valores como `globalprotect_si`, `servidor_aplicacion` o `snmp_desconocido`, y `criticidad`.
  - La **criticidad del activo** es un atributo del inventario (cuánto importa el equipo), no la gravedad de una CVE.
- **Guion oral sugerido.** «Fijaos en IT-004, IT-005 e IT-006: los tres son firewalls PAN-OS de la misma rama, pero IT-006 tiene un *hotfix*, `-h3`. Y hay versiones `desconocida`. Esas diferencias van a dar resultados distintos más adelante.»
- **Qué ejecutar.** Celda de código 2. Opcionalmente, abre `datos/inventario_demo.csv` para enseñar la columna `configuracion`.
- **Resultado esperado.** Una tabla de 11 filas y `11 activos`:
  - IT-001 a IT-003: PaperCut.
  - IT-004 a IT-006: PAN-OS.
  - IT-007: Windows Server 2022.
  - OT-001 a OT-003: SIMATIC CP 1543-1.
  - OT-004: SIMATIC S7-1500.
- **Qué observar.** IT-003 y OT-003 tienen la versión `desconocida`: las reglas no pueden confirmar nada sobre ellos.
- **Preguntas para los alumnos.**
  - *¿Qué diferencia hay entre «criticidad alta» y «CVE grave»?* → La primera dice cuánto importa el activo para el negocio; la segunda es una propiedad de la vulnerabilidad. La prioridad las combina.
- **Problemas habituales.** Ninguno frecuente.
- **Tiempo.** 4 min.

### A.3 Las herramientas: `consultar_activo` (apartado 3.1, celda de código 3)

- **Objetivo didáctico.** Entender qué es una **herramienta**: código Python determinista que un agente puede invocar.
- **Qué explicar.**
  - Las herramientas están decoradas con `@tool` de MAF en `agente_multiherramienta.py`. El decorador añade nombre, descripción y esquema de parámetros, que es lo que «ve» el LLM.
  - `.func(...)` llama a la función original **sin** pasar por el modelo.
  - La línea `>>> HERRAMIENTA … EJECUTADA` la imprime la propia herramienta y servirá de traza en el Cuaderno 2.
- **Guion oral sugerido.** «Esto es una herramienta: una función normal. El agente no sabe leer el CSV, pero sabe que existe `consultar_activo` y cuándo le conviene llamarla. Si pido un activo que no existe, la herramienta no se inventa nada: lo dice.»
- **Qué ejecutar.** Celda de código 3.
- **Resultado esperado.**
  - IT-004: `"encontrado": true`, PAN-OS `11.1.2`, `"configuracion": "globalprotect_si"`.
  - IT-999: `"encontrado": false`, `"mensaje": "No existe en el inventario."`
- **Qué observar.** La respuesta es JSON: los agentes trabajan mejor con datos estructurados que con texto libre.
- **Preguntas para los alumnos.**
  - *¿Quién decide llamar a esta función en el Cuaderno 2?* → El LLM del Orquestador, según su instrucción («si mencionan un identificador de activo, llama SIEMPRE a consultar_activo»).
- **Tiempo.** 4 min.

### A.4 Correlación y cribado: `consultar_cribado` (apartado 3.2, celda de código 4)

- **Objetivo didáctico.** Distinguir una **coincidencia candidata** de una **vulnerabilidad confirmada**, y diferenciar la categoría (A) de la (B).
- **Qué explicar.**
  - El cribado compara **fabricante y producto o familia** del activo con el catálogo KEV. **No valida la versión instalada.**
  - El resultado se separa en dos grupos:
    - **(A)** Candidatas del producto o la familia del activo.
    - **(B)** CVE del mismo fabricante pero de **otro producto** (p. ej. Expedition, otro producto de Palo Alto). **No se suman** a (A).
  - En el Cuaderno 1 el cribado **no se recalcula**: se lee el guardado en `datos/cribado_kev.json`, generado con el catálogo histórico 2026.10.30.
  - El *wrapper* `consultar_cribado` del módulo del workflow reorganiza la salida original en esos dos apartados y añade `metodo` y `advertencia`.
- **Guion oral sugerido.** «Trece CVE de PAN-OS aparecen en KEV. ¿Significa que nuestro firewall tiene trece vulnerabilidades? No. Significa que hay trece candidatas que alguien tiene que revisar, porque el cribado solo mira el nombre del producto, no la versión. Y las tres de Expedition ni siquiera son de nuestro producto: van aparte.»
- **Qué ejecutar.** Celda de código 4.
- **Resultado esperado.**
  ```
  (A) candidatas del producto : 13  | desglose: {'PAN-OS': 13}
  (B) solo fabricante (otro)  : 3  | desglose: {'Expedition': 3}
  Advertencia  : Son coincidencias de fabricante o producto. No son vulnerabilidades confirmadas.
  ```
  Las primeras candidatas de (A) son CVE-2017-15944, CVE-2019-1579 y CVE-2020-2021.
- **Qué observar.** El campo `metodo` dice explícitamente que **no** se ha validado la versión.
- **Preguntas para los alumnos.**
  - *¿Por qué no se suman (A) y (B)?* → Porque (B) no son candidatas de nuestro producto: sumarlas inflaría el riesgo.
  - *¿Qué limitación tiene comparar por familia?* → Puede ser muy amplia. Ejemplo verificado: IT-007 (Windows Server 2022) tiene **175** candidatas (A) y **215** (B), y la lista sale recortada (`desglose` = `None`). Coincidir por familia no equivale a estar afectado.
- **Tiempo.** 6 min.

### A.5 Evaluación de criticidad: `evaluar_activo` (apartado 3.3, celda de código 5)

- **Objetivo didáctico.** Ver cómo se pasa de «candidata» a un **estado** y una **prioridad** mediante reglas deterministas, y conocer sus límites.
- **Qué explicar.**
  - Solo hay reglas para **tres CVE** (`correlacion.py`):
    - **CVE-2023-27350**, PaperCut MF/NG: corregida desde la versión 22.0.9; entre 22.0.0 y 22.0.8 se considera confirmada si `configuracion = servidor_aplicacion`.
    - **CVE-2024-3400**, PAN-OS 11.1.2: con hotfix `-h3` o posterior, `no_aplicable`. Sin él, depende de la configuración: con `globalprotect_si` se considera confirmada, con `globalprotect_no` no aplica, y en otro caso queda `posible`.
    - **CVE-2016-8562**, SIMATIC CP 1543-1: firmware anterior a 2.0.28, confirmada; 2.0.28 o posterior, `no_aplicable`.
  - La **prioridad** la calcula `priorizacion.calcular_prioridad()`:
    - `no_aplicable` da `sin_prioridad`.
    - Si la CVE está en KEV, es `alta` cuando el activo es de criticidad alta u OT, y `media` en otro caso.
  - Cuando el código dice «confirmada», significa **confirmada por nuestra regla sobre datos ficticios**, no comprobada en un equipo real.
- **Guion oral sugerido.** «IT-006 tiene el hotfix h3. Nuestra regla, basada en el aviso del fabricante, dice que con h3 la CVE-2024-3400 está corregida: no aplica y no tiene prioridad. Ojo: esto no significa que el firewall esté limpio de todo. Solo evaluamos tres CVE.»
- **Qué ejecutar.** Celda de código 5.
- **Resultado esperado.**
  ```
  >>> CISA: cache_desactualizada | Versión: 2026.10.30
  Activo: IT-006 - PAN-OS 11.1.2-h3
  CVE-2024-3400: estado=no_aplicable | prioridad=sin_prioridad | en KEV=True
    Justificación: Versión 11.1.2-h3 o hotfix posterior de esta rama: vulnerabilidad corregida.
  ```
- **Qué observar.** `evaluar_activo` comprueba también la vigencia del catálogo, y por eso aparece la línea `CISA: cache_desactualizada`.
- **Preguntas para los alumnos** (resultados verificados con el código actual).
  - *¿Qué saldría con IT-004?* → CVE-2024-3400 `confirmada`, prioridad `alta` (11.1.2 sin hotfix y `globalprotect_si`).
  - *¿Y con IT-005?* → `posible`, prioridad `alta`: la configuración de GlobalProtect es desconocida.
  - *¿Y con OT-002?* → CVE-2016-8562 `no_aplicable` (firmware 2.0.28).
- **Problemas habituales.** Si alguien espera ver las 13 CVE del cribado evaluadas: solo se evalúan las tres con regla.
- **Tiempo.** 6 min.

### A.6 Catálogo CISA y sus limitaciones: `consultar_cisa` (apartado 3.4, celda de código 6)

- **Objetivo didáctico.** Entender la **vigencia** del catálogo y por qué la copia local está desactualizada a propósito.
- **Qué explicar.**
  - `consultar_cisa_solo_lectura` llama a la herramienta original con `forzar_actualizacion=False`.
  - Como la descarga está bloqueada, `obtener_catalogo()` devuelve la caché con `modo = cache_desactualizada` y un aviso.
- **Guion oral sugerido.** «El catálogo es del 30 de octubre. En la vida real lo actualizaríamos cada día. Aquí está congelado a propósito: así todos vemos los mismos números y nada cambia sin permiso.»
- **Qué ejecutar.** Celda de código 6.
- **Resultado esperado.**
  ```
  modo             : cache_desactualizada
  version_catalogo : 2026.10.30
  total_cves       : 1766
  ultima_descarga  : 2026-11-03T07:34:50.191996+00:00
  aviso            : La actualización ha fallado. Se utiliza la última copia válida. Motivo: Descarga CISA desactivada en el workflow experimental.
  ```
- **Qué observar.** El texto «ha fallado» procede del código original. Aquí no es un error, sino el bloqueo intencionado del apartado 1. Aclarad este punto, porque suele generar dudas.
- **Preguntas para los alumnos.**
  - *¿Es grave trabajar con un catálogo antiguo?* → Puede faltar alguna CVE añadida después. Por eso el sistema lo **declara** en el aviso en lugar de ocultarlo. En Hosted el catálogo se actualiza con aprobación humana (Parte C).
- **Tiempo.** 3 min.

### A.7 El contrato `DecisionOrquestador` (apartado 4, celda de código 7)

- **Objetivo didáctico.** Entender por qué el primer agente devuelve un **objeto tipado** y no texto.
- **Qué explicar.**
  - `DecisionOrquestador` es un modelo Pydantic definido en el módulo del workflow. Sus campos:
    - `ruta`: `Literal["respuesta_directa", "correlacion", "analisis_avanzado"]`.
    - `asset_id`, `cve_id`.
    - `accion_explicita`: `Literal["ninguna", "actualizar_novedades", "generar_informes"]`.
    - `respuesta_directa`, `motivo`.
  - El agente se crea con `default_options={"response_format": DecisionOrquestador}`, así que el modelo está obligado a producir JSON con esa forma.
  - El enrutamiento lee **campos**, no interpreta frases: una ruta inventada se rechaza.
  - **Decisión de diseño:** la comprobación de que `respuesta_directa` tenga texto se hace en `RespuestaFinal`, no en el modelo. Hacerla en el modelo interrumpiría el cliente antes de entrar en el grafo y no habría recuperación segura (ver el comentario del código).
- **Guion oral sugerido.** «Si el Orquestador respondiera "creo que habría que mirar la correlación", tendríamos que adivinar qué ha querido decir. En cambio, nos devuelve un formulario con casillas cerradas. Y si intenta rellenar una casilla con un valor que no existe, Pydantic lo rechaza.»
- **Qué ejecutar.** Celda de código 7.
- **Resultado esperado.** Los seis campos con sus valores permitidos, un JSON de ejemplo válido y el rechazo de la ruta inventada:
  ```
  Una ruta no permitida se rechaza ✔ -> Input should be 'respuesta_directa', 'correlacion' or 'analisis_avanzado'
  ```
- **Preguntas para los alumnos.**
  - *¿Qué ventaja tiene un contrato tipado frente a pedir «responde solo con la palabra correlacion»?* → Validación automática, campos adicionales (activo, CVE, acción) y errores detectables en lugar de cadenas ambiguas.
- **Tiempo.** 5 min.

### A.8 Los tres agentes y sus herramientas (apartado 5, celda de código 8)

- **Objetivo didáctico.** Ver la **separación de responsabilidades**: cada agente tiene solo las herramientas que necesita.
- **Qué explicar.**
  - `u.construir_workflow_sin_conexion(m)` crea un `FoundryChatClient` con un endpoint ficticio que **nunca se usa**, y llama a `construir_workflow(cliente, acciones_interactivas=False)`.
  - Con `acciones_interactivas=False`, las dos herramientas de escritura (`actualizar_novedades_cisa_controlada` y `generar_informes_controlados`) **ni siquiera se registran**. Además, AgenteCorrelacion recibe una instrucción adicional: «MODO DEVUI / SOLO LECTURA».
  - **Mínimo privilegio:** el Orquestador solo puede consultar el inventario.
- **Guion oral sugerido.** «El Orquestador es el recepcionista: solo puede mirar la ficha del activo. Correlación es quien sabe de CISA. Criticidad es quien aplica las reglas. Nadie tiene herramientas que escriban. No es que les pidamos que no escriban: es que no tienen con qué.»
- **Qué ejecutar.** Celda de código 8.
- **Resultado esperado.**
  ```
  AgenteOrquestador   herramientas: ['consultar_activo']
  AgenteCorrelacion   herramientas: ['consultar_cribado', 'consultar_novedades_kev', 'consultar_historial_novedades_kev', 'consultar_cisa']
  AgenteCriticidad    herramientas: ['evaluar_activo', 'consultar_nvd_piloto', 'analizar_inventario']
  ¿Alguna herramienta de escritura registrada? False
  ```
- **Preguntas para los alumnos.**
  - *¿Qué es más seguro: decirle al agente «no escribas» o no darle la herramienta?* → No darle la herramienta. Una instrucción se puede ignorar; una herramienta inexistente no se puede llamar.
- **Tiempo.** 4 min.

### A.9 El grafo y sus aristas condicionales (apartado 6, celda de código 9)

- **Objetivo didáctico.** Leer el grafo de 4 nodos y saber **qué condición** activa cada arista.
- **Qué explicar.**
  - Se construye con `WorkflowBuilder` y cinco `add_edge`, cuatro de ellos con `condition=`.
  - Las condiciones son funciones Python **deterministas** que leen la decisión tipada:
    - `va_a_correlacion` sigue a Correlación si la ruta es `correlacion` o `analisis_avanzado`, el activo existe (o no se indicó ninguno) y `accion_explicita = ninguna`. Con una acción explícita, solo continúa si `acciones_interactivas` es verdadero, y en esta formación es falso.
    - `va_directo_a_final` es su negación.
    - `va_a_criticidad` continúa si la ruta era `analisis_avanzado`.
    - De Criticidad se va siempre a `RespuestaFinal`.
  - `RespuestaFinal` es un `Executor` propio, no un agente: es el **único punto de salida**.
- **Guion oral sugerido.** «Las líneas discontinuas significan "depende". El LLM rellena el formulario, pero quien abre o cierra cada puerta es código Python normal. El LLM propone; el grafo dispone.»
- **Qué ejecutar.** Celda de código 9. Si el diagrama no se dibuja, enseña el texto Mermaid.
- **Resultado esperado.** `flowchart TD` con `AgenteOrquestador (Start)`, cuatro aristas `-. conditional .->` y una arista fija `AgenteCriticidad --> RespuestaFinal`.
- **Qué observar.** No hay ninguna arista de Orquestador a Criticidad: no se puede evaluar la prioridad sin pasar antes por la correlación.
- **Preguntas para los alumnos.**
  - *¿Por qué una pregunta sencilla no llama a los especialistas?* → Porque el Orquestador elige `respuesta_directa` y la arista hacia Correlación no se activa. Así se ahorran llamadas, latencia y coste.
- **Problemas habituales.** El visor no renderiza Mermaid (lo indica la nota del cuaderno). JupyterLab 4.1 o posterior sí lo hace.
- **Tiempo.** 5 min.

### A.10 Cómo viaja la decisión: filtros de contexto (apartado 7, celdas de código 10 y 11)

- **Objetivo didáctico.** Entender que los agentes **no comparten variables** y que la decisión viaja dentro del mensaje.
- **Qué explicar.**
  - `AgentExecutor` admite `context_mode="custom"` y un `context_filter`: una función que transforma la conversación antes de pasarla al agente.
  - `_contexto_correlacion` busca en el historial el JSON del Orquestador y construye un mensaje de control:
    - La primera línea es `CONTEXTO_CONTROLADO_ENTREPINARES_V1`.
    - Le siguen `DECISION_ORQUESTADOR_JSON=…`, `PREGUNTA_USUARIO_JSON=…` y la tarea, según `accion_explicita`.
  - `_contexto_criticidad` **solo** acepta ese mensaje de control con `ruta = analisis_avanzado` y `accion_explicita = ninguna`. En otro caso devuelve `ERROR DE CONTEXTO`, para que el agente no ejecute herramientas.
  - **Decisión de diseño:** el nombre del módulo, «sin puentes», se refiere a que antes había ejecutores intermedios (`PrepararCorrelacion`, `PuenteCorrelacion`). Se sustituyeron por estos filtros para dejar el grafo en 4 nodos visibles.
- **Guion oral sugerido.** «Correlación no lee la mente del Orquestador. Le llega un mensaje con un sello, la marca de control, la decisión en JSON y la pregunta original. Y Criticidad comprueba el sello: si la ruta no era análisis avanzado, se niega a trabajar.»
- **Qué ejecutar.** Celdas de código 10 y 11.
- **Resultado esperado.**
  - Celda 10: el bloque que empieza por `CONTEXTO_CONTROLADO_ENTREPINARES_V1` y termina con `… No confirmes afectacion ni asignes prioridad a las candidatas. El inventario es ficticio. No cambies de ruta ni ejecutes otras acciones.`
  - Celda 11: `PETICION DEL USUARIO: …`, la salida de Correlación etiquetada como **candidatas** y, con ruta `correlacion`:
    ```
    ERROR DE CONTEXTO: ruta de Criticidad no validada. No ejecutes herramientas ni inventes resultados.
    ```
- **Qué observar.** Ese «ERROR» es **el comportamiento correcto**, no un fallo: es la barrera funcionando.
- **Preguntas para los alumnos.**
  - *¿Por qué no usar una variable global con la decisión?* → Porque se mezclaría entre ejecuciones concurrentes o sucesivas. Llevar la decisión en el propio mensaje la hace trazable y aislada.
- **Tiempo.** 6 min.

### A.11 Respuesta directa verificada (apartado 8, celda de código 12)

- **Objetivo didáctico.** Ver el mecanismo de respaldo **que no inventa**.
- **Qué explicar.**
  - Si el Orquestador elige `respuesta_directa` pero no aporta texto, `RespuestaFinal` llama a `_respuesta_inventario_verificada()`.
  - Esa función lee el inventario con la herramienta y comprueba que el identificador coincide. Si algo falla, lo dice en lugar de presentar un dato dudoso.
- **Guion oral sugerido.** «Plan B: si el modelo se olvida de escribir la respuesta, no rellenamos el hueco con imaginación. Volvemos a la fuente.»
- **Qué ejecutar.** Celda de código 12.
- **Resultado esperado.**
  - IT-004: `Datos verificados del inventario ficticio para IT-004: {…}`.
  - IT-999: `El activo IT-999 no existe en el inventario ficticio.`
- **Tiempo.** 3 min.

### A.12 Evidencias y trazabilidad (apartado 9, celda de código 13)

- **Objetivo didáctico.** Toda conclusión debe poder rastrearse hasta **qué datos y qué versión** se usaron.
- **Qué explicar.** `u.evidencias_datos()` muestra:
  - La versión y la fecha de obtención del catálogo.
  - La fuente: `cisagov/kev-data` en GitHub.
  - El resumen del cribado guardado.
  - Las huellas SHA-256.

  Son el mismo tipo de evidencias que, en Hosted, permiten saber qué publicación de Blob se usó (Parte C).
- **Guion oral sugerido.** «Si mañana un auditor pregunta "¿con qué datos dijisteis esto?", aquí está la respuesta: versión, fecha, fuente y huella de cada archivo.»
- **Qué ejecutar.** Celda de código 13.
- **Resultado esperado.**
  - `versión 2026.10.30 | 1766 CVE | obtenido 2026-11-03T07:34:50…`
  - Resumen del cribado: `total_activos: 11`, `cves_candidatas: 194`, `pares_activo_cve_candidatos: 232` (`producto` 39, `familia` 193), `cves_pendientes_por_fabricante: 220`.
  - 8 huellas.
- **Qué observar.** El cribado guardado indica `ultima_descarga` **2026-11-02**, y la caché del catálogo **2026-11-03**, con la misma versión 2026.10.30: el cribado se calculó con una descarga anterior del mismo catálogo. Es un buen ejemplo de por qué conviene registrar fechas y versiones.
- **Preguntas para los alumnos.**
  - *¿Para qué sirve la huella SHA-256?* → Para demostrar que un archivo no ha cambiado ni un byte.
- **Tiempo.** 4 min.

### A.13 Informe local Markdown y HTML (apartado 10, celda de código 14)

- **Objetivo didáctico.** Ver la generación de informes y cómo se aísla la salida.
- **Qué explicar.**
  - `u.generar_informe_local()` usa los **módulos originales** `generar_informe.py` y `generar_html.py`, y solo redirige temporalmente sus rutas de salida a `salidas/`, que Git ignora. Al terminar, el bloque `finally` restaura las rutas originales.
  - El informe usa el catálogo histórico y las reglas de las tres CVE.
- **Guion oral sugerido.** «Mismo código de informes que el proyecto original, pero escribiendo en una carpeta de prácticas. Abrid el HTML: es lo que recibiría un responsable.»
- **Qué ejecutar.** Celda de código 14. Después abre `salidas\informe_vulnerabilidades.html`.
- **Resultado esperado.**
  - Las rutas `salidas\informe_vulnerabilidades.md` y `.html`, con su tamaño. En la validación fueron unos 12 KB y 25 KB; varían ligeramente con la fecha.
  - La cabecera incluye `Activos inventariados: 11`, `CVE con reglas de correlación: 3` y `Versión de la selección fija: 2026.10.28`.
- **Qué observar.** El informe es **local y de ejercicio**. No es el informe Hosted publicado en Blob (Parte C).
- **Preguntas para los alumnos.**
  - *¿Por qué no se escribe en `informes/`?* → Para no sobrescribir nada del proyecto. La carpeta `salidas/` está en `.gitignore`.
- **Tiempo.** 4 min.

### A.14 Seguridad e integridad (apartado 11, celda de código 15)

- **Objetivo didáctico.** Cerrar el ciclo: demostrar con datos que **nada ha cambiado**.
- **Qué explicar.** Se recalculan las huellas y se comparan con las del inicio. Un `assert` detiene el cuaderno si algo difiere.
- **Guion oral sugerido.** «Prometimos solo lectura. Lo comprobamos.»
- **Qué ejecutar.** Celda de código 15.
- **Resultado esperado.** `Archivos en datos/: 8` e `INTEGRIDAD: SIN CAMBIOS en datos/`.
- **Problemas habituales.** `AssertionError: ¡Algún dato ha cambiado!`: alguien editó `datos/`. Se arregla con `git checkout -- datos`.
- **Tiempo.** 2 min.

### A.15 Resumen y ejercicios del Cuaderno 1

Respuestas orientativas, verificadas con el código actual (catálogo histórico 2026.10.30):

1. **Cribado de IT-001 y OT-001.**
   - IT-001: (A) **5** (`NG/MF` 4, `MF/NG` 1) y (B) **0**.
   - OT-001: (A) **1** (`SIMATIC CP`) y (B) **1** (`Software Center`).

   Los totales cambian porque dependen del fabricante y el producto de cada activo.
2. **`evaluar_activo("IT-001")`.** Solo tiene regla CVE-2023-27350: PaperCut MF 22.0.8 con `servidor_aplicacion` da `confirmada`, prioridad `alta`. Las tres CVE con regla son CVE-2023-27350, CVE-2024-3400 y CVE-2016-8562.
3. **`accion_explicita="actualizar_novedades"` en el apartado 7.** AgenteCorrelacion recibiría `ACCION EXPLICITA: actualizar_novedades. Llama SOLO a la herramienta actualizar_novedades_cisa_controlada para pedir aprobacion humana…`. En el workflow real eso **no llega a ocurrir**: con `acciones_interactivas=False`, `va_a_correlacion` devuelve falso, el flujo va directo a `RespuestaFinal` y, además, la herramienta no está registrada. El caso F del Cuaderno 2 lo demuestra.

**Tiempo.** 5 min.

---

## 5. Parte B · MAF y Cuaderno 2

### B.0 Conceptos de Microsoft Agent Framework (antes del cuaderno, unos 15 min)

**Objetivo didáctico.** Que el alumno sepa qué aporta MAF y cómo se mapea cada concepto en nuestro código.

**Qué explicar**, con el código del módulo del workflow abierto (líneas en el [anexo](#10-anexo-mapa-del-código)):

| Concepto MAF | Qué es | En nuestro código |
|---|---|---|
| `Agent` | Un LLM con instrucciones, descripción y herramientas | `construir_agentes()`: Orquestador, Correlación y Criticidad |
| `@tool` | Función Python que el agente puede invocar; MAF genera su esquema | `agente_multiherramienta.py` y los *wrappers* `consultar_cribado` y `consultar_cisa` |
| `approval_mode` | `never_require`, o `always_require`, que pide aprobación humana (HITL) | Lectura: `never_require`. Escritura: `always_require`, pero **no se registra** en la formación |
| `response_format` | Salida estructurada | `DecisionOrquestador` en el Orquestador |
| `AgentExecutor` | Envuelve un agente como nodo del grafo; admite `context_filter` | Los tres agentes; Correlación y Criticidad con filtro propio |
| `Executor` + `@handler` | Nodo de código propio | `RespuestaFinal` |
| `WorkflowBuilder` | Grafo de nodos y aristas con condiciones | `construir_workflow()` |
| `FoundryChatClient` | Cliente del modelo desplegado en Foundry | `crear_cliente()`, con `AzureCliCredential` (tu `az login`) |

**Por qué elegimos esta arquitectura:**
- **Agente frente a herramienta:** el agente **decide y redacta**; la herramienta **calcula**. Los números salen siempre de herramientas deterministas.
- **Tres agentes y no uno:** cada uno tiene instrucciones cortas, herramientas mínimas y responsabilidad clara. Así es más fácil de probar y de auditar, y se pueden saltar pasos innecesarios.
  - **Orquestación** clasifica y dirige; no analiza.
  - **Correlación** busca candidatas; no confirma afectación ni asigna prioridad.
  - **Criticidad** aplica las reglas y distingue entre candidatas, reglas y limitaciones.
- **Un nodo final único:** todas las rutas terminan en el mismo sitio, que además aplica las salvaguardas: activo inexistente, acción no ejecutada y respuesta vacía.
- **Enrutamiento por campos tipados:** el LLM propone la ruta, pero las condiciones del grafo son código.

**Limitaciones del enrutamiento** (decirlas abiertamente):
- La **clasificación** depende del LLM y puede variar en preguntas ambiguas (apartado 6 del cuaderno).
- El grafo garantiza que no se salta ningún control, pero **no** que la clasificación sea la mejor posible.
- Si el Orquestador elige mal (p. ej. `respuesta_directa` para una pregunta de riesgos), la respuesta será más pobre, pero no peligrosa: nunca se ejecuta una escritura.

**Guion oral sugerido.**
> «MAF nos da las piezas: agentes, herramientas, nodos y aristas. Nuestro trabajo de diseño ha sido decidir qué parte es inteligencia, y por tanto variable, y qué parte es código, y por tanto predecible. El LLM elige el camino y redacta; el código calcula, valida y pone las barreras.»

**Integración con GPT-4.1-mini en Foundry.**
- `crear_cliente()` lee `FOUNDRY_PROJECT_ENDPOINT` y `AZURE_AI_MODEL_DEPLOYMENT_NAME` (por defecto `gpt-4.1-mini`) y autentica con `AzureCliCredential`, sin claves.
- Cada pregunta hace de 2 a 4 llamadas al modelo.

**Preguntas para los alumnos.**
- *¿Dónde está la «inteligencia» y dónde el «control»?* → La inteligencia está en la clasificación y la redacción del LLM; el control, en las herramientas deterministas, el contrato tipado, las aristas condicionales, los filtros de contexto y el nodo final.

**Tiempo.** 15 min.

Cuaderno: `notebooks/entrepinares_02_workflow_foundry.ipynb`. Tiene 28 celdas, 13 de ellas de código. Las llamadas al modelo empiezan en el apartado 4.

### B.1 Preparación y diagnóstico (apartado 1, celda de código 1)

- **Objetivo didáctico.** Comprobar la configuración **sin** llamar a la red.
- **Qué explicar.** `u.preparar_entorno()` carga `.env` sin pisar variables ya definidas y bloquea CISA. `comprobar_configuracion()` solo informa.
- **Qué ejecutar.** Celda de código 1.
- **Resultado esperado.** `Archivo .env : ✔ existe`, `FOUNDRY_PROJECT_ENDPOINT : ✔ <host>`, `gpt-4.1-mini`, el tenant y `Azure CLI (az) en el PATH : ✔`.
- **Problemas habituales.**
  - `✘ NO definido` aunque el `.env` esté relleno: el archivo puede estar guardado **con BOM** (guía IKEA, paso 6).
  - Tras editar `.env`, hay que reiniciar el kernel.
- **Tiempo.** 2 min.

### B.2 Sesión de Azure CLI (apartado 2, celda de código 2)

- **Objetivo didáctico.** Separar **autenticación** de **autorización**.
- **Qué explicar.** `probar_credencial()` pide un token para `https://ai.azure.com/.default` y solo muestra su caducidad, **nunca el token**.
- **Guion oral sugerido.** «Tener sesión es tener el carné. Que te dejen entrar en el edificio es otra cosa: eso lo veremos en el caso A.»
- **Resultado esperado.** `{'token_obtenido': True, 'el_token_caduca_utc': '…'}`.
- **Tiempo.** 2 min.

### B.3 Construir el workflow (apartado 3, celda de código 3)

- **Objetivo didáctico.** Ver que construir el workflow no es ejecutarlo.
- **Qué explicar.** `m.construir_workflow(acciones_interactivas=False)` crea el cliente real, pero no llama al modelo hasta que se ejecuta.
- **Resultado esperado.** Las mismas herramientas y el mismo grafo que en el Cuaderno 1 (A.8 y A.9).
- **Tiempo.** 2 min.

### B.4 Ejecutar y leer la traza (apartado 4, celda de código 4)

- **Objetivo didáctico.** Saber **leer una traza**.
- **Qué explicar.**
  - `preguntar()` llama a `u.ejecutar_consulta()`, que construye un workflow **nuevo** por pregunta para que no se arrastre estado.
  - Recorre los eventos de MAF:
    - `executor_invoked` da la **RUTA**.
    - La decisión tipada del Orquestador da la **DECISIÓN**.
    - Los mensajes con llamadas a funciones dan las **HERRAMIENTAS**.
  - Si el workflow pidiera una aprobación, la traza lo avisaría y no la concedería.
  - La traza muestra las herramientas que aparecen **en los eventos**. Si sale `(ninguna visible en los eventos)`, no prueba por sí sola que no se llamaran; pero la línea `>>>` de cada herramienta es una segunda evidencia.
- **Qué ejecutar.** Celda de código 4: solo define la función y no imprime nada.
- **Tiempo.** 3 min.

### B.5 Casos A–F (apartado 4, celdas de código 5 a 10)

Los resultados son los del 16/11/2026. **La ruta y la redacción pueden variar** entre ejecuciones; los números que vienen de herramientas no deberían variar.

#### Caso A · «¿Qué versión tiene IT-004?» (celda de código 5)
- **Objetivo didáctico.** Ruta mínima: un solo agente.
- **Resultado observado.**
  - `RUTA: AgenteOrquestador -> RespuestaFinal`, `ruta: respuesta_directa`.
  - Herramienta `[AgenteOrquestador] consultar_activo({"asset_id":"IT-004"})`.
  - Respuesta con PAN-OS 11.1.2, en unos 8,6 s.
- **Qué observar.** La respuesta sale de `consultar_activo`, no de la «memoria» del modelo.
- **Guion oral sugerido.** «Una pregunta, un agente, una herramienta. Si este caso funciona, tenemos permisos sobre el modelo.»
- **Problemas habituales.**
  - 401/403: el usuario no tiene el rol en el proyecto Foundry.
  - 404: el nombre del despliegue no coincide.
  - 429: cuota; esperar un minuto.
- **Tiempo.** 3 min.

#### Caso B · «¿Qué CVE candidatas aparecen para IT-004 en CISA KEV?» (celda de código 6)
- **Objetivo didáctico.** Correlación sin criticidad.
- **Resultado observado.**
  - `RUTA: AgenteOrquestador -> AgenteCorrelacion -> RespuestaFinal`.
  - Herramientas `consultar_activo` y `consultar_cribado({"asset_id":"IT-004"})`.
  - La respuesta separa (A) **13** de PAN-OS y (B) **3** de Expedition, y dice que no son vulnerabilidades confirmadas.
- **Qué observar.** El agente reproduce los totales exactos de la herramienta y la separación (A)/(B) que exige `GUIA_CRIBADO`.
- **Pregunta para los alumnos.** *¿Por qué no aparece Criticidad?* → Porque la ruta es `correlacion` y `va_a_criticidad` exige `analisis_avanzado`.
- **Tiempo.** 4 min.

#### Caso C · «Analiza las vulnerabilidades y la prioridad de IT-004.» (celda de código 7)
- **Objetivo didáctico.** Recorrido completo por los tres agentes.
- **Resultado observado.**
  - `RUTA: AgenteOrquestador -> AgenteCorrelacion -> AgenteCriticidad -> RespuestaFinal`.
  - Herramientas `consultar_activo`, `consultar_cribado` y `evaluar_activo`, en unos 18 s.
  - La respuesta separa los datos del activo, las candidatas (A) 13 y (B) 3, la evaluación por reglas (CVE-2024-3400 confirmada, prioridad alta) y las limitaciones.
- **Qué explicar.** «Confirmada» procede de **nuestra regla** (11.1.2 sin hotfix y `globalprotect_si` en el inventario ficticio), no de una comprobación en un equipo real. Las otras 12 candidatas **no** están evaluadas.
- **Qué observar.** Si en alguna ejecución el texto presenta la confirmación como absoluta, aprovéchalo para matizarla: es un buen ejemplo de por qué el profesor debe leer críticamente la redacción del LLM.
- **Tiempo.** 5 min.

#### Caso D · «¿Qué versión tiene IT-999?» (celda de código 8)
- **Objetivo didáctico.** Un activo inexistente corta el flujo.
- **Resultado observado.**
  - `ruta: respuesta_directa`.
  - `consultar_activo` devuelve `encontrado: false`.
  - Respuesta: `El activo IT-999 no existe en el inventario (ficticio). No se ha realizado ningun analisis.`
- **Qué explicar.** Ese texto lo genera **`RespuestaFinal`** (`_existe_activo` devuelve falso), no el modelo: es una salvaguarda determinista. Aunque el LLM hubiera elegido `correlacion`, `va_a_correlacion` habría devuelto falso.
- **Tiempo.** 3 min.

#### Caso E · «¿Está afectado IT-006 por CVE-2024-3400? ¿Qué otros riesgos podrían existir?» (celda de código 9)
- **Objetivo didáctico.** Pregunta sobre una CVE concreta y activo con hotfix.
- **Resultado observado.**
  - Tres agentes; `cve_id: CVE-2024-3400`.
  - Herramientas `consultar_cribado({"asset_id":"IT-006","cve_id":"CVE-2024-3400"})` y `evaluar_activo`.
  - Respuesta: `no_aplicable`, `sin_prioridad`, por la versión 11.1.2-h3.
- **Qué observar** (punto didáctico importante). Como el cribado se filtró **por esa CVE**, la herramienta solo devolvió 1 candidata. En la ejecución del 16/11 el modelo concluyó que «no se reportan otras coincidencias candidatas adicionales», lo cual es **incompleto**: sin filtro, IT-006 tiene las mismas 13 candidatas PAN-OS que IT-004. Explícalo así: **un filtro estrecha la vista, y el LLM puede generalizar de más**. La respuesta correcta sería: «Según las reglas, CVE-2024-3400 no aplica. Las demás candidatas no se han evaluado.»
- **Pregunta para los alumnos.** *¿Cómo reformularías la pregunta para ver todos los riesgos?* → Separar las dos preguntas, o pedir explícitamente «todas las candidatas de IT-006».
- **Tiempo.** 5 min.

#### Caso F · «Actualiza ahora las novedades de CISA KEV.» (celda de código 10)
- **Objetivo didáctico.** Una petición de escritura en un workflow de solo lectura.
- **Resultado observado.**
  - `RUTA: AgenteOrquestador -> RespuestaFinal`, con `accion_explicita: actualizar_novedades` y `ruta: correlacion`.
  - `HERRAMIENTAS LLAMADAS: (ninguna visible en los eventos)`.
  - Respuesta: `La operacion solicitada (actualizar las novedades de CISA KEV) no se ha ejecutado. En DevUI esta version funciona solo en modo lectura…`
- **Qué explicar.**
  - Hay **tres barreras independientes**:
    1. `va_a_correlacion` devuelve falso con una acción explícita y `acciones_interactivas=False`.
    2. La herramienta no está registrada.
    3. `RespuestaFinal` emite `_mensaje_accion_no_ejecutada()`.
  - El texto menciona «DevUI» porque el mensaje es común a DevUI y al cuaderno, que comparten modo. Aclarad que en el cuaderno ocurre lo mismo.
- **Qué observar.** No se ejecuta ni se intenta ninguna herramienta, y no aparece ninguna línea `>>>`.
- **Guion oral sugerido.** «Le pedimos algo que escribe. El Orquestador lo entiende perfectamente, pero el grafo no deja pasar la petición, y aunque la dejara, no hay herramienta. En Hosted veremos la versión adulta: la herramienta existe, pero exige que una persona la apruebe.»
- **Tiempo.** 4 min.

### B.6 Comparativa (apartado 5, celda de código 11)

- **Objetivo didáctico.** Ver de un vistazo coste y complejidad por tipo de pregunta.
- **Resultado observado** (16/11/2026; los tiempos varían):

  | Consulta | Ruta | Agentes | Herramientas | s |
  |---|---|---|---|---|
  | IT-004 versión | respuesta_directa | 1 | 1 | 8,63 |
  | Candidatas IT-004 | correlacion | 2 | 2 | 13,01 |
  | Análisis IT-004 | analisis_avanzado | 3 | 3 | 17,83 |
  | IT-999 | respuesta_directa | 1 | 1 | 5,73 |
  | IT-006 + CVE | analisis_avanzado | 3 | 3 | 15,63 |
  | Actualizar CISA | correlacion | 1 | 0 | 6,57 |
- **Qué observar.** En el caso F, la ruta dice `correlacion` pero solo interviene 1 agente: la arista no dejó pasar la petición.
- **Tiempo.** 2 min.

### B.7 Variabilidad del LLM (apartado 6, celda de código 12)

- **Objetivo didáctico.** Asumir que el enrutamiento **no es determinista**.
- **Qué explicar.** La misma pregunta de frontera («Dame una visión de los riesgos del firewall IT-004.») se repite 3 veces (`REPETICIONES = 3`).
- **Resultado observado.**
  - El 16/11/2026: ejecución 1, `respuesta_directa`; ejecuciones 2 y 3, `analisis_avanzado`. **Hubo variabilidad.**
  - En la validación del 14/11 salió siempre `analisis_avanzado`.
  - Puede salir cualquiera de los dos resultados: el cuaderno lo indica en su conclusión.
- **Guion oral sugerido.** «"Visión de los riesgos": ¿es una pregunta de ficha o de análisis? Ni nosotros lo tenemos claro, y el modelo tampoco. Lo importante es que ninguna de las rutas es peligrosa: solo cambia la profundidad de la respuesta.»
- **Preguntas para los alumnos.**
  - *¿Cómo reducirías la variabilidad?* → Instrucciones más precisas con ejemplos, `temperature` baja o reglas previas para ciertas palabras. Pero nunca se elimina del todo, y por eso las barreras están en el código.
- **Tiempo.** 5 min.

### B.8 Integridad (apartado 7, celda de código 13)

- **Resultado esperado.** `INTEGRIDAD: SIN CAMBIOS en datos/`.
- **Qué observar.** Ni con el modelo real ha cambiado un solo archivo.
- **Tiempo.** 1 min.

> **Nota sobre el resumen del cuaderno.** La celda de texto final remite a los **pasos 9-12** de la guía para Hosted.

### B.9 Bonus · DevUI en el puerto 8091

- **Objetivo didáctico.** Ver el mismo workflow con una interfaz web y sus eventos en vivo.
- **Qué explicar.**
  - `scripts/lanzar_devui.py` arranca DevUI solo en `127.0.0.1` y en modo **solo lectura**.
  - Con token Bearer por defecto, o con `--sin-auth` solo para una demo local.
  - Usa tu `az login` y consume llamadas al modelo.
- **Qué ejecutar.** Guía IKEA, paso 8 (en la terminal B). Después, la pregunta `¿Qué versión tiene IT-004?`.
- **Resultado esperado.**
  - En consola: `DevUI en http://127.0.0.1:8091 (solo localhost)` y `DevUI: SOLO LECTURA; acciones de escritura NO disponibles`.
  - En la web: el workflow `WorkflowEntrepinaresSinPuentes` y el grafo de 4 nodos.
  - Validación del 16/11: sin token la API responde 401; con token, 200.
- **Qué observar.** En DevUI se ve el **JSON de la decisión** del Orquestador como mensaje visible: es justo lo que leen los filtros de contexto (A.10).
- **Problemas habituales.**
  - `Address already in use`: usa `--puerto 8092`.
  - Si las preguntas fallan, los errores son los mismos que en el Cuaderno 2.
- **Tiempo.** 10 min.

---

## 6. Parte C · Hosted V6

**Fuente de evidencias:** `docs/HOSTED_V5.md` y las comprobaciones de solo lectura del 16/11/2026. El código Hosted **no forma parte de este repositorio**: vive en el proyecto original de Entrepinares. Aquí se explica a partir de su comportamiento verificado.

> **Nombres:** el agente se llama `entrepinares-itot-v5-lab`. «V5» es la generación de la arquitectura, con KEV en Blob; **v6** es el número de versión desplegada que recibe el 100 % del tráfico. Por eso conviven «Hosted V5» y «v6».

### C.1 Local frente a Hosted

- **Objetivo didáctico.** Saber qué cambia al pasar del portátil a Foundry.
- **Qué explicar:**

  | | Local (cuadernos, DevUI) | Hosted V6 |
  |---|---|---|
  | Dónde se ejecuta | Tu ordenador | Contenedor gestionado por Foundry |
  | Identidad | Tu `az login` (`AzureCliCredential`) | Identidad del agente (`DefaultAzureCredential`) |
  | Catálogo KEV | Histórico fijo 2026.10.30 (`datos/`) | **Activo en Azure Blob**, dinámico |
  | Cribado | Leído de `datos/cribado_kev.json` | Paquete verificado de la publicación activa |
  | Escritura | Imposible: herramientas no registradas | Dos herramientas con **aprobación humana obligatoria** |
  | Entrada | `workflow.run(pregunta)` | Protocolo *Responses* de OpenAI (`POST /responses`) |
- **Guion oral sugerido.** «El mismo cerebro de tres agentes, pero viviendo en la nube, leyendo un catálogo que se puede actualizar y con permiso para escribir, siempre que una persona apruebe cada escritura.»
- **Tiempo.** 5 min.

### C.2 Qué desplegamos realmente

- **Objetivo didáctico.** Desmitificar el despliegue.
- **Qué explicar.**
  - Un paquete de código con un `main.py` que arranca un `ResponsesHostServer` de `agent_framework_foundry_hosting`.
  - **Cada solicitud** construye un workflow, agentes y cliente nuevos, con los mismos cuatro nodos y el mismo contrato `DecisionOrquestador`.
  - Para retomar el flujo tras una aprobación, el servidor guarda puntos de control (*checkpoints*) y solo admite el tipo `DecisionOrquestador`.
  - El enrutamiento de versiones está **fijado explícitamente** a la versión 6 (no `@latest`), al 100 %. Volver a una versión anterior consiste en cambiar esa regla.
- **Qué enseñar.** El ciclo en cinco pasos de `docs/HOSTED_V5.md`.
- **Pregunta para los alumnos.** *¿Por qué fijar la versión en lugar de usar «la última»?* → Para que publicar una versión nueva no cambie lo que reciben los usuarios hasta que se decida promoverla.
- **Tiempo.** 5 min.

### C.3 CISA KEV activo en Blob: versiones y puntero

- **Objetivo didáctico.** Entender el **versionado inmutable** con un **puntero** de activación.
- **Qué explicar.**
  - En el contenedor `entrepinares-kev`:
    - `versiones/<id>/` guarda cada publicación: catálogo, cribado, novedades y `manifest_local.json` con los hashes SHA-256. Nunca se sobrescribe.
    - `control/version_activa.json` es el **puntero**: indica qué publicación está activa.
  - El agente lee el puntero, carga esa publicación y **verifica los hashes** antes de usarla.
  - Si hay puntero pero algo falla (integridad, red, credenciales), el error se propaga: **nunca presenta un catálogo antiguo como si fuera el actual**.
- **Guion oral sugerido.** «Cada versión del catálogo es una caja sellada con su lista de hashes. Un cartel en la puerta, el puntero, dice cuál es la vigente. Cambiar de versión es solo mover el cartel, y las cajas antiguas siguen ahí para auditoría.»
- **Qué ejecutar en directo.** `python scripts\consultar_kev_blob.py` (guía IKEA, paso 10).
- **Resultado del 16/11/2026** (el catálogo es dinámico: el día de la sesión puede ser otro):
  ```
  Publicación activa   : 20261116T072220Z-cc181488b7be49688a2b1d280f6621e7
  Catálogo (puntero)   : 2026.11.13
  Catálogo (manifiesto): 2026.11.13 | validado=True
  Fuente               : https://raw.githubusercontent.com/cisagov/kev-data/…
  Archivos publicados  : ['cisa_kev_cache.json', 'cribado_kev.json', 'novedades_kev.json']
  ```
- **Tiempo.** 6 min.

### C.4 Actualización CISA con aprobación humana (HITL)

- **Objetivo didáctico.** Ver el patrón *human-in-the-loop* aplicado a una escritura real.
- **Qué explicar.**
  - `actualizar_novedades_cisa_controlada` tiene `approval_mode="always_require"`. El agente **se detiene** y devuelve una solicitud `mcp_approval_request`, y solo continúa si alguien responde con `mcp_approval_response` y `approve: true`.
  - Al aprobarse:
    1. Descarga CISA.
    2. Prepara y publica la versión en `versiones/<id>/`.
    3. **La vuelve a leer y la verifica.**
    4. Solo entonces mueve el puntero, con control optimista por ETag: si otro escritor cambió el puntero, se aborta.
  - Las novedades se calculan frente a una **referencia histórica fija**, no frente a la versión anterior.
- **Evidencia real del 16/11/2026.** Pruebas autorizadas del propietario desde el Playground de Foundry. El agente informó de 17 CVE nuevas, 70 modificadas y 0 retiradas frente a la referencia.

  | Hora (UTC) | Operación aprobada | Resultado |
  |---|---|---|
  | 07:12 | Actualización CISA | Publicación `20261116T071235Z-8bc180…` (2026.11.13), activa |
  | 07:15 | Generación de informes | Informe `20261116T071514Z-936bfb65…`, generado con `8bc180…` |
  | 07:22 | Actualización CISA | Publicación `20261116T072220Z-cc181488…` (2026.11.13), que pasa a ser la activa |

  En el primer intento el propietario vio un error en pantalla, pero los registros muestran que la operación terminó correctamente. La causa del error mostrado es desconocida (incidencia transitoria). No la atribuyas a carga ni a límites de Azure.
- **Qué NO hacer en clase.** No aprobar actualizaciones en directo. El cliente `probar_hosted_v5.py` **nunca aprueba** nada.
- **Pregunta para los alumnos.** *¿Por qué verificar antes de mover el puntero?* → Para que el agente nunca apunte a una publicación incompleta o corrupta.
- **Tiempo.** 7 min.

### C.5 Correlación con el catálogo activo

- **Objetivo didáctico.** Comprobar que Hosted usa el catálogo de Blob y no la copia empaquetada.
- **Qué explicar.** La prueba `correlacion` del cliente pregunta si **CVE-2026-124194** aparece en el cribado de **IT-007**:
  - **No** está en el catálogo histórico del repositorio. Verificado: el cribado local de IT-007 no la contiene.
  - Tampoco está en la copia empaquetada en el agente (2026.11.09).
  - Solo aparece si el cribado se hace con el catálogo activo de Blob.
  - Es una coincidencia **solo por fabricante** (Microsoft, producto Office frente a Windows Server): una candidata de tipo (B), **no** una vulnerabilidad de IT-007.
- **Qué ejecutar en directo.** `python scripts\probar_hosted_v5.py` (guía IKEA, paso 9).
- **Resultado del 16/11/2026:**
  - `Versión : 6`.
  - `[inventario]` OK (11.1.2).
  - `[cisa]`: `Version: 2026.11.13`, `Origen: azure_blob_verificado` y `Publicacion Blob: 20261116T072220Z-cc181488…`, OK.
  - `[correlacion]`: CVE-2026-124194 reconocida, OK.
  - `Resultado: sin incidencias`.
  - Cada pregunta tarda unos 10-15 s.
- **Qué observar.** La publicación que dice el agente **coincide** con la del puntero de Blob (C.3).
- **Tiempo.** 6 min.

### C.6 Informes con aprobación humana: publicación y manifiesto

- **Objetivo didáctico.** Ver la trazabilidad completa de un informe.
- **Qué explicar.**
  - `generar_informes_controlados` también exige HITL.
  - En la v6, si no hay un KEV activo verificado, **falla antes de generar o escribir nada**: nunca publica con el catálogo empaquetado.
  - Publica `informe_vulnerabilidades.md`, `.html` y `manifest.json` en `entrepinares-informes/informes/<id>/`, con un id nuevo cada vez. Nunca sobrescribe.
- **Qué ejecutar en directo.** `python scripts\consultar_kev_blob.py --informe 20261116T071514Z-936bfb65c984419a9c24888ae0742944` (guía IKEA, paso 12).
- **Resultado verificado:**
  ```
  Verificación completa: True
  Catálogo CISA usado  : 2026.11.13
  Origen KEV           : azure_blob_verificado
  Publicación KEV usada: 20261116T071235Z-8bc180c7be42430d832639becde64c7b
  Cribado              : recalculado_offline_desde_blob_verificado
  ```
- **Punto clave.** El informe cita `8bc180…`, que era la publicación activa **cuando se generó**. La activa hoy es `cc181488…`, posterior. **No es un error de correlación**: es trazabilidad. Para saber qué usará una ejecución nueva se mira el puntero, no un informe antiguo.
- **Enlaces SAS.** Al publicar, el agente devuelve enlaces de descarga con un SAS de lectura válido hasta el 03/12/2026 15:42 UTC, que da acceso a **todos** los informes. **No los proyectes ni los compartas**: trátalos como credenciales. Para leer un informe en clase usa `consultar_kev_blob.py`, que funciona con tu `az login` y sin SAS.
- **Tiempo.** 6 min.

### C.7 Invocar Hosted desde Python

- **Objetivo didáctico.** Saber llamar a un agente desplegado.
- **Qué explicar** (`scripts/probar_hosted_v5.py`):
  1. Conecta con `AIProjectClient(endpoint, credential=AzureCliCredential())`.
  2. Lee la versión que recibe el tráfico con `agents.get(...)`.
  3. Crea **una sesión fijada a esa versión** con `create_session(version_indicator=VersionRefIndicator(...))`.
  4. Obtiene el cliente con `get_openai_client(agent_name=…)` y llama a `responses.create(input=…, extra_body={"agent_session_id": …})`.
  5. Si la respuesta trae una solicitud de aprobación, **avisa y no aprueba**.
  6. Oculta cualquier `sig=`/`se=` y cualquier token.
- **Guion oral sugerido.** «Para el cliente, el agente Hosted es un endpoint compatible con la API *Responses* de OpenAI. Lo interesante es lo que no hace: no aprueba nada y no imprime nada sensible.»
- **Tiempo.** 3 min.

### C.8 Lo que aprendimos del defecto de caché

- **Objetivo didáctico.** Un caso real de depuración en la nube.
- **Qué explicar.**
  - **Síntoma (v4 y v5):** las preguntas KEV fallaban si llegaban en los primeros ~15 s de vida del contenedor.
  - **Causa:** la caché empezaba con `momento = 0.0`. En un contenedor recién arrancado, `time.monotonic()` vale menos de 15, así que la condición «caché fresca» era verdadera y se devolvía «sin paquete» **sin leer Blob**.
  - **Corrección en la v6:** `momento = float("-inf")`, para que la primera llamada lea siempre Blob.
  - **Lecciones:**
    - Un primer diagnóstico (SAS vacío) resultó **falso**: se descartó con un experimento.
    - `time.monotonic()` no tiene un origen fijo.
    - Las pruebas deben cubrir el «primer segundo» de vida del proceso.
    - Se añadió además la protección de informes (C.6).
- **Guion oral sugerido.** «El código funcionaba en el portátil y fallaba en la nube, pero solo a veces. La causa era una línea: un cero que debía ser menos infinito. La lección: comprobad las hipótesis con experimentos, no con intuiciones.»
- **Tiempo.** 2 min.

---

## 7. Si algo falla durante la sesión

| Fallo | Síntoma | Alternativa |
|---|---|---|
| Sin red / Foundry caído | Errores de conexión en el Cuaderno 2 | El Cuaderno 1 sigue funcionando entero. Para el 2, abre la copia HTML de `salidas\` (1.2) y usa los resultados de esta guía (B.5-B.7) |
| 401/403 en el Cuaderno 2 | `…no tiene permisos en el proyecto Foundry` | Explica la diferencia entre autenticar y autorizar (B.2) y sigue con la copia HTML |
| 429 cuota | `Límite de cuota (429)` | Espera un minuto y baja `REPETICIONES` a 1 |
| Variabilidad «inesperada» | Otra ruta distinta de la de esta guía | No es un fallo: úsala como ejemplo (B.7) |
| Hosted no responde o da 403 | Error en `probar_hosted_v5.py` | Muestra las evidencias de `docs/HOSTED_V5.md` (tablas del 16/11) |
| SAS del agente caducado (desde el 03/12/2026) | `[cisa]` dice que no hay puntero o menciona el SAS | Explícalo como dependencia operativa: hay que renovar el SAS, y es tarea del administrador. Usa las evidencias documentadas |
| Sin rol de lectura en Blob | 403 en `consultar_kev_blob.py` | Usa las salidas documentadas de C.3 y C.6 |
| DevUI ocupado | `Address already in use` | `--puerto 8092` |
| Mermaid no se dibuja | Solo se ve texto | El texto describe el mismo grafo; usa la tabla del apartado 6 del Cuaderno 1 |

---

## 8. Preguntas frecuentes de los alumnos

| Pregunta | Respuesta orientativa |
|---|---|
| ¿Una CVE en KEV significa que estamos afectados? | No. Es una **candidata**. Hace falta comprobar versión, configuración y componente. Nuestras reglas solo lo hacen para tres CVE. |
| ¿Por qué hay 13 candidatas para PAN-OS y solo una evaluada? | El cribado compara productos; la evaluación necesita una regla específica por CVE, y solo hay tres. |
| ¿El LLM puede inventarse un número de CVE? | Las instrucciones lo prohíben y los números salen de herramientas, pero la **redacción** puede generalizar de más (caso E). Hay que leer la traza. |
| ¿Por qué el Cuaderno 1 dice 2026.10.30 y Hosted 2026.11.13? | Son **dos catálogos distintos**: el histórico fijo del repositorio y el activo dinámico de Blob. |
| ¿Puede el workflow local actualizar CISA? | No. En el cuaderno y en DevUI las herramientas de escritura no se registran y el grafo desvía la petición (caso F). Solo Hosted tiene escritura, y siempre con aprobación humana. |
| ¿Qué pasa si alguien aprueba por error? | Se crea una publicación nueva verificada y el puntero se mueve. Las versiones anteriores siguen en Blob. Volver atrás exige mover el puntero; no hay restauración automática. |
| ¿Por qué tres agentes y no uno con todas las herramientas? | Por menos herramientas por agente, instrucciones más cortas, rutas más baratas para preguntas sencillas y responsabilidades auditables. |
| ¿Se puede hacer determinista el enrutamiento? | Se puede reducir la variabilidad, pero no eliminarla con un LLM. Por eso las barreras están en el código. |
| ¿Qué datos salen a Azure? | En el Cuaderno 2 y DevUI, las preguntas y las salidas de las herramientas van al modelo de Foundry. El inventario es ficticio. |
| ¿Por qué `az login` y no una clave? | `FoundryChatClient` usa identidades de Entra ID; no hay claves en el código ni en `.env`. |

---

## 9. Mensajes clave para el cierre

1. **El LLM decide y redacta; el código calcula y controla.** Todos los números salen de herramientas deterministas.
2. **Candidata no es igual a vulnerabilidad confirmada.** El cribado KEV compara productos; solo las reglas específicas evalúan la afectación, y solo para tres CVE.
3. **Contrato tipado y aristas condicionales:** la ruta es un dato validado, no una frase interpretada.
4. **Mínimo privilegio:** lo más seguro es no dar la herramienta. En local no hay herramientas de escritura.
5. **El enrutamiento varía:** se diseña para que todas las rutas sean seguras, no para que sean siempre iguales.
6. **Trazabilidad:** versión del catálogo, fuente, hashes y manifiesto. Un informe registra la publicación vigente cuando se generó.
7. **Hosted:** catálogo activo en Blob con versiones inmutables y puntero, escrituras con aprobación humana y versión fijada.
8. **Dos catálogos:** el histórico del repositorio (2026.10.30) y el activo dinámico de Blob.

---

## 10. Anexo: mapa del código

Módulo del workflow: `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py`.

| Elemento | Dónde (aprox.) |
|---|---|
| `DecisionOrquestador` | líneas 116-148 |
| `_mensaje_accion_no_ejecutada` (caso F) | 155-166 |
| Herramientas con escritura (`always_require`) | 244-355 (no se registran con `acciones_interactivas=False`) |
| *Wrapper* `consultar_cribado` (A)/(B) | 358-415 |
| `bloquear_descargas_cisa` | 428-452 |
| Instrucciones: `REGLAS_COMUNES`, Orquestador, `GUIA_CRIBADO`, Correlación, Criticidad | 459-572 |
| Marcadores y filtros `_contexto_correlacion` / `_contexto_criticidad` | 583-742 |
| `_respuesta_inventario_verificada` | 745-774 |
| `RespuestaFinal` | 777-818 |
| `crear_credencial` / `crear_cliente` | 830-854 |
| `construir_agentes` | 857-910 |
| `construir_workflow`: condiciones y `WorkflowBuilder` | 913-993 |

Otros archivos:

| Archivo | Para qué |
|---|---|
| `agente_multiherramienta.py` | Herramientas originales (`consultar_activo`, `evaluar_activo`, `consultar_cisa`…) |
| `correlacion.py` | Reglas de las tres CVE |
| `priorizacion.py` | `calcular_prioridad` |
| `fuente_kev.py` | Caché CISA, vigencia de 24 h, descarga (bloqueada en la formación) |
| `cribado_kev.py` | Cómo se calculó el cribado guardado (fabricante y producto o familia) |
| `notebooks/entrepinares_utils.py` | Adaptador de los cuadernos: preparación, trazas, informe local e integridad |
| `scripts/probar_hosted_v5.py` | Cliente Hosted de solo lectura |
| `scripts/consultar_kev_blob.py` | Lectura del puntero KEV y de manifiestos de informes, sin SAS |
| `scripts/lanzar_devui.py` | DevUI 8091 en solo lectura |
