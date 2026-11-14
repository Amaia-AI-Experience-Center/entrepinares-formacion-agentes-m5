# Hosted V5: del workflow local al agente en Foundry

## El ciclo en cinco pasos

```
1. MAF local            2. Despliegue Hosted        3. Consulta remota
   (Cuadernos 1 y 2) ──►  (agente ya desplegado) ──►  scripts/probar_hosted_v5.py
                                                            │
5. Informe persistido   ◄── 4. Lectura KEV en Blob ◄────────┘
   (Blob: informes/<id>)     (puntero activo → paquete verificado)
```

1. **MAF local.** El mismo workflow de tres agentes (Orquestador → Correlación → Criticidad) que ejecutas en el Cuaderno 2.
2. **Despliegue Hosted (ya hecho).** El workflow está empaquetado como agente *Hosted* de Microsoft Foundry (`entrepinares-itot-v5-lab`). No se despliega en esta formación.
3. **Consulta remota.** `scripts/probar_hosted_v5.py` envía preguntas al agente con tu sesión de `az login` (protocolo *responses*).
4. **Lectura KEV en Azure Blob.** En Hosted, el catálogo CISA KEV no sale de la copia empaquetada: el agente lee un **puntero** (`control/version_activa.json`) que indica qué **publicación verificada** (`versiones/<id>/`) está activa y comprueba sus hashes SHA-256.
5. **Informe persistido.** Cuando un administrador lo aprueba (aprobación humana), el agente genera los informes Markdown + HTML y los guarda en Blob (`informes/<id>/`) con un **manifiesto** que registra qué catálogo y qué publicación KEV se usaron.

## Qué necesitas para cada parte

| Parte | Permiso necesario (además de `az login`) |
|---|---|
| Consultar el agente Hosted | Rol en el proyecto Foundry que permita invocar agentes (p. ej. *Azure AI User*) |
| Leer el puntero KEV y los manifiestos (`scripts/consultar_kev_blob.py`) | Rol de lectura de datos en la cuenta de almacenamiento (p. ej. *Storage Blob Data Reader*) |
| Que el **agente** lea Blob | Conexión del proyecto con SAS de lectura vigentes (gestión del administrador) |
| Publicar KEV o informes | Operación administrativa con aprobación humana, **fuera** del recorrido didáctico |

`az login` solo te identifica: **no concede ninguno de estos roles**.

## Estado verificado (14/11/2026)

| Elemento | Estado |
|---|---|
| Versiones del agente | v1-v4 sin cambios. **v5** (14/11): mismo código que la v4; solo cambian las 4 referencias SAS. **v6** (14/11): código de la v4/v5 con **dos archivos corregidos** (`v5_blob_runtime.py`, `v5_blob_operaciones.py`); los otros 31 archivos son idénticos a la v4 |
| Enrutamiento | **Fijado en la v4 (100 %)**; antes era `@latest`. La **v6 está validada pero pendiente de promoción** (requiere confirmación) |
| Conexión de la v4 | `entrepinares-v5-sas-21d-20261112`: 4 SAS vigentes hasta el **03/12/2026 15:42 UTC** (lectura `r`, escritura `cw`) |
| Conexión de la v5 y v6 (y de v2-v3) | `entrepinares-v5-sas`: actualizada el 14/11 con **los mismos 4 SAS vigentes**, mismos campos y metadatos; caduca también el **03/12/2026 15:42 UTC** |
| KEV activo en Blob | Publicación `20261113T135058Z-17735c10705a4565baae8926ee9e9966`, catálogo **2026.11.10**, 1779 CVE |

## Defecto de caché (causa real) y corrección

**Síntoma (v4 y v5):** las preguntas sobre KEV fallaban («No ha sido posible leer/verificar el catálogo KEV activo» / «el catálogo KEV activo no está disponible en Blob») **cuando llegaban en los primeros ~15 s de vida del sandbox**. Como cada consulta suelta abre un sandbox nuevo, la primera pregunta KEV solía fallar.

**Causa:** en `v5_blob_runtime.py` la caché empezaba con `_CACHE = {"momento": 0.0, ...}` y `paquete_activo()` devuelve el valor en caché si `time.monotonic() - momento < 15`. En un sandbox recién arrancado `time.monotonic()` vale pocos segundos, así que devolvía `None` («sin paquete») **sin leer Blob** (la herramienta tardaba ~2 ms en el log). No era un problema de SAS: con la misma conexión, la misma pregunta funcionaba pasados 15 s.

**Corrección aplicada en la v6:**
1. `v5_blob_runtime.py`: la caché empieza en `float("-inf")`, así que la primera llamada lee Blob siempre; después de una lectura válida, la caché de 15 s funciona igual que antes.
2. `v5_blob_operaciones.publicar_informes_hosted()`: **protección de informes**. Si `ENTREPINARES_HABILITAR_KEV_BLOB=1` y no hay paquete KEV activo verificado (o falla la lectura de Blob), lanza un error **antes** de generar o escribir nada. Ya no puede publicarse un informe basado en el catálogo empaquetado. Con Blob deshabilitado expresamente, el comportamiento es el de antes.

**Pruebas locales** (`v5_lab/tests/test_hosted_v5_cache_informes.py`, módulos reales, sin red): 8/8 OK. Primera lectura inmediata tras arrancar, uso de la caché dentro del TTL, nueva lectura al expirar, error de Blob propagado sin «envenenar» la caché, bloqueo de informes sin paquete activo, ausencia de escrituras en ese caso y comportamiento conservado con Blob deshabilitado. Las 38 pruebas anteriores siguen OK.

**Validación real de la v6** (sesiones nuevas fijadas a la v6, **sin esperas**):

| Prueba | Resultado |
|---|---|
| `consultar_cisa` como primera pregunta | ✅ `azure_blob_verificado`, 2026.11.10, publicación `20261113T135058Z-17735c10…` |
| Segunda consulta en la misma sesión | ✅ mismo resultado; en el log la herramienta tarda 0,0002 s (caché) |
| Correlación IT-007 como primera pregunta | ✅ reconoce CVE-2026-124194; `consultar_cribado` tarda **1,55 s** a los ~10 s del arranque del sandbox (lectura real de Blob; antes fallaba en ~2 ms) |
| Inventario | ✅ IT-004 → 11.1.2 |
| Protección de informes | ✅ comprobada con pruebas locales; **no** se ha generado ningún informe remoto |

## Cómo comprobarlo tú (pasos 12-14 de la guía)

```powershell
python scripts\probar_hosted_v5.py --esperar-version 2026.11.10     # inventario, CISA y correlación
python scripts\probar_hosted_v5.py --version 6 --espera 0            # la v6, sin espera
python scripts\consultar_kev_blob.py                                 # publicación KEV activa
python scripts\consultar_kev_blob.py --informe 20261112T122224Z-ef460b7657ca4e2ab756c478c722ff5a
```

Mientras el endpoint siga en la v4, el cliente mantiene por defecto una espera de 20 s (solución provisional). Tras promocionar la v6 ya no hará falta (`--espera 0`).

**Pendiente:** promocionar la v6 y, después, la prueba completa de generación de informes con aprobación humana (autorización aparte).