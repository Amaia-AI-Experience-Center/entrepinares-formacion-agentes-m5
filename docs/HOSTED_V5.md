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
| Versiones del agente | 1-4 sin cambios. **Versión 5** creada el 14/11 con **el mismo código que la v4** (mismo `content_hash`); solo cambian las 4 referencias SAS |
| Enrutamiento | **Fijado en la versión 4 (100 %)** de forma temporal. Antes era `@latest`. La v5 **no** está promocionada |
| Conexión de la v4 | `entrepinares-v5-sas-21d-20261112`: 4 SAS vigentes hasta el **03/12/2026 15:42 UTC** (lectura `r`, escritura `cw`) |
| Conexión de la v5 (y de v2-v3) | `entrepinares-v5-sas`: actualizada el 14/11 con **los mismos 4 SAS vigentes** (vencían el 13/11); mismos campos y metadatos |
| KEV activo en Blob | Publicación `20261113T135058Z-17735c10705a4565baae8926ee9e9966`, catálogo **2026.11.10**, 1779 CVE |

**Resultados reales por el endpoint habitual (v4), con `scripts/probar_hosted_v5.py`:**

| Prueba | Resultado |
|---|---|
| Inventario | ✅ IT-004 → 11.1.2 |
| `consultar_cisa` | ✅ `azure_blob_verificado`, 2026.11.10, publicación `20261113T135058Z-17735c10…` (lectura de Blob de ~1,5 s en el log) |
| Correlación IT-007 / CVE-2026-124194 (solo existe en el catálogo activo) | ✅ La reconoce (1 coincidencia solo por fabricante) |

## Defecto conocido (causa confirmada)

**Síntoma:** las preguntas sobre KEV fallan («No ha sido posible leer/verificar el catálogo KEV activo» / «el catálogo KEV activo no está disponible en Blob») **si llegan en los primeros ~15 s de vida del sandbox**. Ocurre en v4 y v5 por igual. Como cada consulta suelta abre un sandbox nuevo, la primera pregunta KEV de una sesión suele fallar.

**Causa:** en `hosted_v5_lab/v5_blob_runtime.py` la caché empieza con `_CACHE = {"momento": 0.0, ...}` y la función `paquete_activo()` devuelve el valor en caché (`None`) si `time.monotonic() - momento < 15`. En un sandbox recién arrancado `time.monotonic()` vale pocos segundos, así que devuelve «sin paquete» **sin intentar leer Blob** (en el log la herramienta dura ~2 ms en lugar de ~1,5 s).

**Evidencia:** en la misma sesión, una pregunta KEV a los 5 s falla y la misma pregunta pasados más de 15 s funciona, tanto en v4 como en v5. Esto **corrige** el diagnóstico inicial, que atribuía el fallo a la inyección del SAS: la conexión de la v4 sí se resolvía.

**Riesgo para los informes:** `publicar_informes_hosted()` usa el mismo `paquete_activo()` y, si recibe `None`, genera el informe con el catálogo empaquetado (2026.11.09) sin fallar (el manifiesto no llevaría `origen_kev`). No se ha generado ningún informe para comprobarlo.

**Corrección propuesta (requiere autorización; no aplicada):**
1. `v5_blob_runtime.py`: inicializar la caché como `"momento": float("-inf")`, para que la primera llamada lea siempre Blob.
2. `v5_blob_operaciones.publicar_informes_hosted()`: si `ENTREPINARES_HABILITAR_KEV_BLOB=1` y `paquete_activo()` es `None`, fallar en lugar de usar el catálogo empaquetado.
3. Nueva versión con ese código, validada con sesiones fijadas a la versión antes de promocionarla.

**Solución provisional en esta formación:** `scripts/probar_hosted_v5.py` usa **una sola sesión**: primero pregunta el inventario (arranca el sandbox), espera 20 s y después hace las preguntas KEV. Con `--espera 0` se reproduce el defecto.

## Cómo comprobarlo tú (pasos 12-14 de la guía)

```powershell
python scripts\probar_hosted_v5.py --esperar-version 2026.11.10     # inventario, CISA y correlación
python scripts\probar_hosted_v5.py --espera 0                        # reproduce el defecto conocido
python scripts\consultar_kev_blob.py                                 # publicación KEV activa
python scripts\consultar_kev_blob.py --informe 20261112T122224Z-ef460b7657ca4e2ab756c478c722ff5a
```

El objetivo completo (que Hosted use el KEV activo también para **informes**) queda pendiente: requiere la corrección anterior y una prueba de escritura autorizada.
