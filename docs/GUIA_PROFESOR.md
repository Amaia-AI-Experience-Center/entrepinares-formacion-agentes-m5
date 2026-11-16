# Guion del profesor · Entrepinares M5

Guion para dar la clase compartiendo pantalla. Cada ejercicio indica qué ejecutar, qué decir, qué mirar y con qué idea debe quedarse el grupo.

- **Instalación y comandos completos:** `docs/GUIA_INSTALACION_Y_EJECUCION.md` (la «guía IKEA», 12 pasos).
- **Explicaciones técnicas a fondo, celda a celda:** `docs/GUIA_PROFESOR_REFERENCIA.md`.

> **Contexto.** Entrepinares es una empresa real. El **inventario de prácticas es ficticio**: no son sus equipos ni hay conexión con sus sistemas.

> **Dos catálogos CISA KEV. Repítelo varias veces:**
> - **Histórico**, en el repositorio: `2026.10.30`, 1766 CVE. Fijo. Lo usan los cuadernos y DevUI.
> - **Activo**, en Azure Blob: dinámico. Solo lo usa Hosted. El 16/11/2026 era el `2026.11.13`.

---

## 1. Antes de la clase

**La víspera** (guía IKEA, pasos 1-10):

- [ ] El repositorio está clonado en una ruta corta (`C:\Proyectos\…`) y `verificar_entorno.py` responde `Entorno coherente`.
- [ ] Las 21 pruebas terminan en `OK`.
- [ ] El Cuaderno 1 completo termina con `INTEGRIDAD: SIN CAMBIOS en datos/`.
- [ ] El caso A del Cuaderno 2 funciona, lo que confirma el permiso sobre el modelo.
- [ ] `python scripts\probar_hosted_v5.py` responde `Resultado: sin incidencias`, lo que confirma el permiso sobre Hosted.
- [ ] `python scripts\consultar_kev_blob.py` muestra `validado=True`, lo que confirma la lectura de Blob.
- [ ] El SAS del agente sigue vigente: caduca el **03/12/2026 15:42 UTC**.
- [ ] Hay copias HTML de respaldo con salidas, en `salidas\` (Git la ignora):
  ```powershell
  python -m jupyter nbconvert --to html --execute notebooks\entrepinares_01_fundamentos_offline.ipynb --output-dir salidas
  python -m jupyter nbconvert --to html --execute notebooks\entrepinares_02_workflow_foundry.ipynb --output-dir salidas
  ```

**Media hora antes, ten abierto:**

| Ventana | Para qué |
|---|---|
| VS Code: Cuaderno 1 y Cuaderno 2 (kernel `.venv`, salidas limpias) | Partes A y B |
| VS Code: `datos/inventario_demo.csv` y el módulo `orquestacion_entrepinares_sin_puentes_PROPUESTA_CORRECCION.py` | Enseñar datos e instrucciones |
| PowerShell A, en la raíz del repositorio con `(.venv)` | Hosted y Blob |
| PowerShell B, con `$env:DEVUI_AUTH_TOKEN` definido | DevUI (opcional) |
| `docs/HOSTED_V5.md` | Evidencias de Hosted |

---

## 2. Agendas

| Bloque | 2 h | 3 h 40 min |
|---|---|---|
| Apertura: caso de uso | 5 min | 10 min |
| **Parte A**, Cuaderno 1 | 35 min (A1, A2, A3, A4, A6) | 60 min (todo) |
| Descanso | — | 10 min |
| **Parte B**, Cuaderno 2 | 50 min (B0 breve, casos A, C, E y F, variabilidad) | 75 min (todo y DevUI) |
| Descanso | — | 10 min |
| **Parte C**, Hosted V6 | 25 min (C2, C3, C4 y C5) | 40 min (todo) |
| Cierre | 5 min | 15 min |

**Qué ejecutar en directo y qué no:**
- **En directo:** el Cuaderno 1 completo, el Cuaderno 2 y las consultas de lectura a Hosted y Blob.
- **Solo con evidencias:** la actualización CISA y la generación de informes en Hosted. El anexo indica cómo hacerlo en directo, siempre con autorización expresa.

---

## Apertura · El caso de uso (5-10 min)

**Decir:**
> «Imaginad el equipo de seguridad de una planta. CISA publica cada semana vulnerabilidades que se están explotando de verdad. La pregunta es sencilla: ¿alguna nos toca? Vamos a responderla con tres agentes de IA. Pero antes veremos qué parte hace código normal, porque esa es la parte en la que podemos confiar.»

**Enseñar:** `datos/inventario_demo.csv`, con 11 activos IT y OT ficticios.

**Idea clave:** la demo no escanea equipos. Cruza un inventario con un catálogo y explica el resultado.

---

## 3. Parte A · Cuaderno 1: fundamentos (sin red)

`notebooks/entrepinares_01_fundamentos_offline.ipynb` tiene 15 celdas de código y no necesita Azure.

### A1 · Preparación segura e inventario · 8 min

| | |
|---|---|
| **Ejecutar** | Apartado 1 (celda de código 1) y apartado 2 (celda 2) |
| **Decir** | «Antes de tocar nada hacemos una foto de los datos con SHA-256 y desconectamos la descarga de CISA. El código original, si ve el catálogo viejo, lo descarga y lo sobrescribe, y hoy no queremos que nada cambie sin decidirlo nosotros.» |
| **Observar** | `Descarga de CISA bloqueada ✔`, `Archivos de datos protegidos: 8` y la tabla de **11 activos**. Señala IT-004, IT-005 e IT-006: los tres son PAN-OS 11.1.2, pero IT-006 tiene el hotfix `-h3` |
| **Idea clave** | Primero se protege y se mide; después se ejecuta |

### A2 · Herramientas deterministas: candidatas frente a confirmadas · 18 min

| | |
|---|---|
| **Ejecutar** | Apartado 3, celdas 3 a 6: `consultar_activo`, `consultar_cribado`, `evaluar_activo` y `consultar_cisa` |
| **Decir** | «Una herramienta es una función normal. El agente no sabe leer el CSV, pero sabe que existe `consultar_activo` y cuándo le conviene llamarla.» |
| **Decir (cribado)** | «Trece CVE de PAN-OS aparecen en KEV. ¿Tiene el firewall trece vulnerabilidades? No: son trece **candidatas**. El cribado solo compara fabricante y producto; no mira la versión. Y las tres de Expedition son de otro producto: van aparte.» |
| **Decir (evaluación)** | «Solo tenemos reglas para tres CVE. IT-006 lleva el hotfix h3, así que la regla dice que la CVE-2024-3400 no aplica. Eso no significa que el firewall esté limpio de todo.» |
| **Observar** | IT-999 devuelve `encontrado: false`, sin inventar nada. El cribado da **(A) 13 PAN-OS** y **(B) 3 Expedition**, con la advertencia «no son vulnerabilidades confirmadas». IT-006 sale `no_aplicable` / `sin_prioridad`. CISA aparece como `cache_desactualizada`, versión `2026.10.30` |
| **Ojo** | El aviso «La actualización ha fallado» del apartado 3.4 no es un error: es el bloqueo del apartado 1 |
| **Idea clave** | **Candidata ≠ vulnerabilidad confirmada.** Y aun «confirmada» significa «según nuestra regla sobre datos ficticios» |

Si preguntan qué pasa con otros activos (resultados verificados):
- IT-004 sale `confirmada` / `alta`: no tiene hotfix y tiene GlobalProtect activo.
- IT-005 sale `posible`, porque su configuración es desconocida.
- IT-007 (Windows Server) tiene 175 candidatas por familia. Es un buen ejemplo de lo amplio que llega a ser el cribado.

### A3 · El contrato `DecisionOrquestador` · 5 min

| | |
|---|---|
| **Ejecutar** | Apartado 4 (celda 7) |
| **Decir** | «El Orquestador no contesta "creo que habría que mirar la correlación". Rellena un formulario con casillas cerradas, y si pone un valor que no existe, se rechaza.» |
| **Observar** | Los campos `ruta` (`respuesta_directa`, `correlacion`, `analisis_avanzado`), `asset_id`, `cve_id`, `accion_explicita` (`ninguna`, `actualizar_novedades`, `generar_informes`), `respuesta_directa` y `motivo`. La ruta «inventada» se rechaza con `Input should be 'respuesta_directa', 'correlacion' or 'analisis_avanzado'` |
| **Idea clave** | El enrutamiento se basa en **datos tipados**, no en interpretar frases |

### A4 · Tres agentes, cuatro nodos y sus aristas · 9 min

| | |
|---|---|
| **Ejecutar** | Apartado 5 (celda 8) y apartado 6 (celda 9) |
| **Decir** | «El Orquestador es el recepcionista: solo mira la ficha del activo. Correlación sabe de CISA y Criticidad aplica las reglas. Nadie tiene herramientas que escriban. No es que les pidamos que no escriban: es que no tienen con qué.» |
| **Decir (grafo)** | «Las líneas discontinuas significan "depende". El LLM rellena el formulario, pero las puertas las abre código Python. El LLM propone y el grafo dispone.» |
| **Observar** | `¿Alguna herramienta de escritura registrada? False`. El grafo tiene cuatro nodos: Orquestador, Correlación, Criticidad y RespuestaFinal. No hay arista de Orquestador a Criticidad: para evaluar hay que pasar antes por la correlación |
| **Idea clave** | **Mínimo privilegio.** Las preguntas sencillas no despiertan a los especialistas |

### A5 · Filtros de contexto y respuesta verificada · 8 min

| | |
|---|---|
| **Ejecutar** | Apartado 7 (celdas 10 y 11) y apartado 8 (celda 12) |
| **Decir** | «Los agentes no comparten variables. A Correlación le llega un mensaje con un sello, la decisión en JSON y la pregunta original. Criticidad comprueba el sello: si la ruta no era análisis avanzado, se niega a trabajar.» |
| **Observar** | El bloque `CONTEXTO_CONTROLADO_ENTREPINARES_V1` y el mensaje `ERROR DE CONTEXTO: ruta de Criticidad no validada…`. Ese «error» **es la barrera funcionando**. En el apartado 8, si falta el texto, la respuesta se reconstruye desde el inventario, no desde la imaginación del modelo |
| **Idea clave** | La decisión **viaja en el mensaje** y cada agente valida lo que recibe |

### A6 · Evidencias, informe local e integridad · 8 min

| | |
|---|---|
| **Ejecutar** | Apartados 9, 10 y 11 (celdas 13 a 15). Después abre `salidas\informe_vulnerabilidades.html` |
| **Decir** | «Si mañana un auditor pregunta con qué datos dijimos esto, aquí están la versión, la fecha, la fuente y la huella de cada archivo. Y prometimos solo lectura: lo comprobamos.» |
| **Observar** | Catálogo `2026.10.30`, 1766 CVE, y 8 huellas. El informe se escribe en `salidas\`, que Git ignora, y usa los módulos originales de informes. Final: `INTEGRIDAD: SIN CAMBIOS en datos/` |
| **Idea clave** | **Trazabilidad**: toda conclusión se puede rastrear hasta sus datos |

**Ejercicios del cuaderno** (respuestas en la referencia, A.15):
- IT-001 tiene (A) 5 y (B) 0 candidatas; OT-001, (A) 1 y (B) 1.
- IT-001 sale con CVE-2023-27350 `confirmada` / `alta`.
- Con `accion_explicita="actualizar_novedades"`, Correlación recibiría la orden de pedir aprobación, pero en el workflow real esa petición no llega a ella (caso F).

---

## 4. Parte B · Cuaderno 2: MAF y agentes

### B0 · Qué aporta MAF (sin cuaderno) · 10 min

Enséñalo en el código, sin diapositivas:

| Pieza | En nuestro código |
|---|---|
| `Agent`: LLM con instrucciones y herramientas | Los tres agentes de `construir_agentes()` |
| `@tool`: función que el agente puede llamar | `consultar_activo`, `consultar_cribado`, `evaluar_activo`… |
| `response_format`: salida estructurada | `DecisionOrquestador` |
| `AgentExecutor` + `context_filter` | Cómo recibe su contexto cada agente |
| `WorkflowBuilder` + `add_edge(condition=…)` | Las aristas del grafo |
| `FoundryChatClient` | `gpt-4.1-mini` en Foundry, con tu `az login` |

**Decir:**
> «MAF nos da las piezas. Nuestro trabajo de diseño ha sido decidir qué es inteligencia, y por tanto variable, y qué es código, y por tanto predecible. El LLM elige el camino y redacta; el código calcula y pone las barreras.»

### B1 · Preparación y trazas · 5 min

| | |
|---|---|
| **Ejecutar** | Apartados 1 a 4 (celdas 1 a 4). No llaman al modelo |
| **Decir** | «Tener sesión es tener el carné; que te dejen entrar es otra cosa. Eso lo veremos en el caso A.» |
| **Observar** | `.env ✔`, `token_obtenido: True` (el token nunca se imprime) y las mismas herramientas que en el Cuaderno 1. Explica las cuatro partes de la traza: RUTA, DECISIÓN, HERRAMIENTAS y RESPUESTA |
| **Idea clave** | Autenticar no es autorizar |

### B2 · Casos A a D: rutas distintas · 12 min

| Caso | Pregunta | Ruta observada (16/11) | Qué señalar |
|---|---|---|---|
| A | ¿Qué versión tiene IT-004? | Orquestador → Final | Un agente y una herramienta. Si funciona, hay permisos |
| B | ¿Qué CVE candidatas aparecen para IT-004…? | + Correlación | Reproduce (A) 13 y (B) 3, como candidatas |
| C | Analiza las vulnerabilidades y la prioridad de IT-004 | Los tres agentes | «Confirmada» procede de **nuestra regla**; las otras 12 candidatas no se han evaluado |
| D | ¿Qué versión tiene IT-999? | Orquestador → Final | El texto «no existe» lo genera `RespuestaFinal`, no el modelo |

**Decir:** «Una pregunta, un agente. Una pregunta de análisis, tres. El coste y el tiempo crecen con la ruta: entre 6 y 18 segundos.»

**Idea clave:** cada pregunta recorre **solo lo necesario**.

### B3 · Caso E: una conclusión incompleta del LLM · 6 min

| | |
|---|---|
| **Ejecutar** | Celda 9: «¿Está afectado IT-006 por CVE-2024-3400? ¿Qué otros riesgos podrían existir?» |
| **Decir** | «Fijaos en la llamada: `consultar_cribado` con `cve_id=CVE-2024-3400`. Ese filtro estrecha la vista a una sola CVE. Y luego el modelo dice "no hay otras candidatas"… pero IT-006 tiene las mismas 13 de PAN-OS que IT-004.» |
| **Observar** | Para la CVE preguntada, `no_aplicable` / `sin_prioridad` es correcto. La parte de «otros riesgos» generaliza de más. (Ocurrió el 16/11; la redacción puede variar) |
| **Pregunta al grupo** | «¿Cómo lo preguntaríais para ver todos los riesgos?» → En dos preguntas, o pidiendo «todas las candidatas de IT-006» |
| **Idea clave** | **Lee la traza, no solo la respuesta.** Un filtro por CVE no equivale a analizar todas las candidatas del activo |

### B4 · Caso F: escrituras bloqueadas · 5 min

| | |
|---|---|
| **Ejecutar** | Celda 10: «Actualiza ahora las novedades de CISA KEV.» |
| **Decir** | «El Orquestador entiende perfectamente lo que le pedimos. Pero la arista no deja pasar la petición, y aunque la dejara, la herramienta no existe aquí. En Hosted veremos la versión adulta: la herramienta existe, pero una persona tiene que aprobarla.» |
| **Observar** | `accion_explicita: actualizar_novedades`, `HERRAMIENTAS LLAMADAS: (ninguna…)` y ninguna línea `>>>`. El mensaje menciona «DevUI» porque es común a DevUI y al cuaderno: aquí ocurre exactamente lo mismo |
| **Idea clave** | Hay **tres barreras independientes**: la arista, la herramienta no registrada y el nodo final |

### B5 · Comparativa, variabilidad e integridad · 8 min

| | |
|---|---|
| **Ejecutar** | Apartados 5, 6 y 7 (celdas 11 a 13) |
| **Decir** | «"Dame una visión de los riesgos del firewall IT-004": ¿es una pregunta de ficha o de análisis? Ni nosotros lo tenemos claro, y el modelo tampoco. Lo importante es que ninguna ruta es peligrosa: solo cambia la profundidad.» |
| **Observar** | El 16/11 salió `respuesta_directa` una vez y `analisis_avanzado` dos. El 14/11 salieron las tres iguales. Si hoy sale estable, dilo: puede variar en otra sesión. En la comparativa, el caso F tiene ruta `correlacion` pero 1 solo agente |
| **Idea clave** | **El enrutamiento varía.** Se diseña para que todas las rutas sean seguras, no para que siempre sean iguales |

### B6 · Bonus: DevUI en el puerto 8091 · 10 min

| | |
|---|---|
| **Ejecutar** | Guía IKEA, paso 8, en PowerShell B. Pregunta: «¿Qué versión tiene IT-004?» |
| **Decir** | «El mismo workflow con una interfaz de desarrollo. Mirad el JSON de la decisión: es justo lo que leen los filtros de contexto.» |
| **Observar** | `DevUI en http://127.0.0.1:8091 (solo localhost)`, `SOLO LECTURA` y el grafo de cuatro nodos |
| **Idea clave** | DevUI es para **ver** el workflow, no para operar |

---

## 5. Parte C · Hosted V6: CISA, Blob, HITL e informes

El agente se llama `entrepinares-itot-v5-lab`. «V5» es la arquitectura, con KEV en Blob; **v6** es la versión desplegada, con el 100 % del tráfico fijado. Las evidencias completas están en `docs/HOSTED_V5.md`.

### C1 · Local frente a Hosted · 8 min

| | Local | Hosted V6 |
|---|---|---|
| Catálogo | Histórico `2026.10.30` | Activo en Blob, dinámico |
| Escritura | Los agentes no tienen herramientas de escritura administrativa (CISA, Blob). El Cuaderno 1 sí genera un informe de ejercicio en `salidas\`, ignorado por Git | Dos herramientas, siempre con aprobación humana |
| Identidad | Tu `az login` | Identidad del agente |

**Decir:** «El mismo cerebro de tres agentes, pero viviendo en la nube, leyendo un catálogo que se puede actualizar y con permiso para escribir, siempre que una persona apruebe cada escritura. Cada petición construye un workflow nuevo, con los mismos cuatro nodos y el mismo contrato.»

**Idea clave:** la versión está **fijada** (`"6"`, no «la última»). Publicar una versión nueva no cambia nada hasta que se promueve.

### C2 · Catálogo activo en Blob: versiones y puntero · 7 min

| | |
|---|---|
| **Ejecutar** | `python scripts\consultar_kev_blob.py` |
| **Decir** | «Cada versión del catálogo es una caja sellada con su lista de hashes. Un cartel en la puerta, el puntero, dice cuál es la vigente. Cambiar de versión es mover el cartel, y las cajas antiguas se quedan para auditoría.» |
| **Observar** | `Publicación activa`, `Catálogo (puntero)` y `validado=True`. El 16/11: `20261116T072220Z-cc181488…`, `2026.11.13`. Hoy puede ser otra |
| **Idea clave** | Las versiones son **inmutables** y se activan con un puntero. Si algo no cuadra, el agente falla en lugar de usar un catálogo viejo |

### C3 · Actualización CISA con HITL: la cronología del 16/11 · 8 min

Enséñalo con evidencias; no lo ejecutes (ver el anexo). Fueron pruebas autorizadas del propietario desde el Playground:

| Hora (UTC) | Operación aprobada | Resultado |
|---|---|---|
| 07:12 | Actualización CISA | Publicación `…8bc180…` (2026.11.13), activa |
| 07:15 | Generación de informes | Informe `…936bfb65…`, generado con `8bc180` |
| 07:22 | Actualización CISA | Publicación `…cc181488…`, que pasa a ser la activa |

**Decir:** «La herramienta pide permiso y el agente se para. Solo sigue si una persona aprueba. Entonces descarga, publica una caja nueva, la vuelve a leer para verificarla y, solo después, mueve el cartel.»

**Idea clave:** **HITL**. La escritura existe, pero no ocurre sin una persona.

### C4 · Correlación con el catálogo activo · 7 min

| | |
|---|---|
| **Ejecutar** | `python scripts\probar_hosted_v5.py`. Tarda unos 40 s en total |
| **Decir** | «Preguntamos por la CVE-2026-124194 en IT-007. No existe en el catálogo del repositorio ni en la copia empaquetada en el agente. Si el agente la encuentra, es que está leyendo el catálogo de Blob.» |
| **Observar** | `Versión : 6`, `Origen: azure_blob_verificado` y la misma publicación que mostró `consultar_kev_blob.py`. La CVE aparece como coincidencia **solo por fabricante** (Microsoft, otro producto): es una candidata (B), no una vulnerabilidad de IT-007 |
| **Idea clave** | Lo que dice el agente **coincide** con el puntero de Blob |

### C5 · Informe publicado y manifiesto · 6 min

| | |
|---|---|
| **Ejecutar** | `python scripts\consultar_kev_blob.py --informe 20261116T071514Z-936bfb65c984419a9c24888ae0742944` |
| **Decir** | «El informe cita la publicación `8bc180`, que era la activa cuando se generó. Hoy la activa es otra, y no es un error: es trazabilidad. Para saber qué usará una ejecución nueva, se mira el puntero.» |
| **Observar** | `Verificación completa: True`, `Origen KEV: azure_blob_verificado`, `Publicación KEV usada: …8bc180…` y las huellas del `.md` y el `.html` |
| **Ojo** | Los enlaces de descarga que devuelve el agente llevan SAS: **no los proyectes ni los compartas**. Para enseñar un informe, usa este comando, que no necesita SAS |
| **Idea clave** | Cada informe registra **con qué datos** se hizo |

### C6 · El defecto de caché y su solución · 4 min

**Decir:**
> «En la v4 y la v5, las preguntas KEV fallaban si llegaban en los primeros 15 segundos de vida del contenedor. Primero sospechamos del SAS, y un experimento lo descartó. La causa era una línea: la caché empezaba en cero, y en un contenedor recién arrancado el reloj `monotonic` vale menos de 15. El código creía tener una caché fresca y no leía Blob. En la v6 empieza en menos infinito. Además, si no hay un catálogo verificado, el informe falla antes de escribir nada.»

**Idea clave:** **verificar hipótesis con experimentos**, y probar el primer segundo de vida de un proceso.

---

## 6. Si algo falla

| Problema | Qué hacer |
|---|---|
| Sin red o Foundry caído | El Cuaderno 1 funciona igual. Para el 2, abre la copia HTML de `salidas\` y comenta los resultados de esta guía |
| 401/403 en el Cuaderno 2 | Explica autenticación frente a autorización y sigue con la copia HTML |
| 429, cuota | Espera un minuto y baja `REPETICIONES` a 1 |
| Ruta distinta de la esperada | No es un fallo: úsalo como ejemplo de variabilidad |
| Hosted da error o 403 | Muestra las tablas de `docs/HOSTED_V5.md` |
| SAS caducado (desde el 03/12/2026) | `[cisa]` no puede leer Blob. Explica la dependencia operativa; renovarlo es tarea del administrador |
| 403 en `consultar_kev_blob.py` | Falta el rol de lectura en el almacenamiento: muestra las salidas documentadas |
| DevUI: `Address already in use` | Usa `--puerto 8092` |
| `Falta FOUNDRY_PROJECT_ENDPOINT` con el `.env` relleno | El `.env` está guardado con BOM: guía IKEA, paso 6 |

---

## 7. Mensajes para el cierre

1. **El LLM decide y redacta; el código calcula y controla.** Los números salen de herramientas deterministas.
2. **Candidata no es lo mismo que vulnerabilidad confirmada.** Y «confirmada», aquí, es «según nuestra regla sobre un inventario ficticio».
3. **Contrato tipado y aristas condicionales:** la ruta es un dato validado, y el grafo pone las barreras.
4. **El enrutamiento varía, y el LLM puede generalizar de más:** leed la traza, no solo la respuesta.
5. **Mínimo privilegio y HITL:** en local los agentes no tienen herramientas de escritura administrativa (solo se genera el informe de ejercicio en `salidas\`); en Hosted las hay, pero solo con aprobación humana.
6. **Trazabilidad:** hay un catálogo histórico y uno activo con versiones y puntero, y cada informe dice con qué datos se hizo.

---

## Anexo · Demostración real en el Playground (opcional)

> ⚠️ **Por defecto, la clase NO hace escrituras.** Se enseñan las evidencias del 16/11 (C3 y C5).
>
> Hacer esta demostración exige la **autorización expresa** del responsable del entorno, por escrito y antes de la clase. Los cambios son **persistentes**:
> - Una actualización CISA crea una publicación nueva en Blob y **mueve el puntero**. Afecta a todo el que consulte el agente, y no hay restauración automática.
> - Cada informe se publica en Blob y se queda allí.
> - El agente devuelve enlaces con SAS: **deja de compartir pantalla** antes de mostrar la respuesta, o recórtala.

**Antes:** anota la publicación activa con `python scripts\consultar_kev_blob.py`.

**1. Actualización CISA con HITL**
1. En el portal de Foundry, abre el agente `entrepinares-itot-v5-lab` (versión 6) en el Playground.
2. Escribe: `Actualiza ahora las novedades de CISA KEV.`
3. El agente se detiene y muestra la solicitud de aprobación de `actualizar_novedades_cisa_controlada`. Explica que **nada se ha escrito todavía**.
4. Apruébala. La respuesta debe incluir el éxito, la versión del catálogo, el identificador de la nueva publicación y las novedades frente a la referencia.
5. Comprueba en PowerShell: `python scripts\consultar_kev_blob.py`. La publicación activa debe ser la nueva.

**2. Informe con HITL**
1. En el Playground: `Genera ahora los informes HTML y Markdown de vulnerabilidades del inventario ficticio.`
2. Aprueba la solicitud de `generar_informes_controlados`.
3. Copia el identificador del informe que devuelve el agente (formato `AAAAMMDDTHHMMSSZ-` seguido de 32 caracteres hexadecimales). No copies los enlaces.
4. Comprueba el manifiesto. Por ejemplo, con el informe del 16/11:
   ```powershell
   python scripts\consultar_kev_blob.py --informe 20261116T071514Z-936bfb65c984419a9c24888ae0742944
   ```
   Sustituye el identificador por el que acabas de obtener. El campo `Publicación KEV usada` debe coincidir con la publicación activa en ese momento.

**Después:** apunta en `docs/HOSTED_V5.md`, o en el registro del entorno, qué publicaciones e informes se crearon, a qué hora y con qué autorización.
