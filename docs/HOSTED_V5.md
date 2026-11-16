# Hosted V5: del workflow local al agente en Foundry

## El ciclo en cinco pasos

```
1. MAF local            2. Despliegue Hosted        3. Consulta remota
   (Cuadernos 1 y 2) ──►  (agente desplegado, v6) ──► scripts/probar_hosted_v5.py
                                                            │
5. Informe persistido   ◄── 4. Lectura KEV en Blob ◄────────┘
   (Blob: informes/<id>)     (puntero activo → paquete verificado)
```

1. **MAF local.** El mismo workflow de tres agentes (Orquestador → Correlación → Criticidad) que ejecutas en el Cuaderno 2.
2. **Despliegue Hosted.** El workflow está empaquetado como agente *Hosted* de Microsoft Foundry (`entrepinares-itot-v5-lab`). La versión publicada es la **v6**. En la formación **no** se despliega nada.
3. **Consulta remota.** `scripts/probar_hosted_v5.py` envía preguntas de solo lectura con tu sesión de `az login`.
4. **Lectura KEV en Azure Blob.** El agente no usa su copia empaquetada: lee el **puntero** `control/version_activa.json`, que indica qué **publicación verificada** (`versiones/<id>/`) está activa, y comprueba sus hashes SHA-256.
5. **Escrituras con aprobación humana (HITL).** Hay dos herramientas que escriben y **siempre** piden aprobación antes de hacerlo:
   - `actualizar_novedades_cisa_controlada`: descarga CISA, publica una nueva versión del KEV en Blob y la **activa** moviendo el puntero.
   - `generar_informes_controlados`: genera los informes Markdown + HTML con el KEV activo y los publica en `informes/<id>/` con un **manifiesto** de trazabilidad.

## Permisos necesarios

| Parte | Permiso (además de `az login`) |
|---|---|
| Consultar el agente Hosted | Rol en el proyecto Foundry que permita invocar agentes (p. ej. *Azure AI User*) |
| Leer el puntero KEV y los manifiestos (`scripts/consultar_kev_blob.py`) | Rol de lectura de datos en la cuenta de almacenamiento (p. ej. *Storage Blob Data Reader*) |
| Que el agente lea y escriba Blob | Conexión del proyecto con SAS (gestión del administrador) |
| Aprobar actualizaciones CISA o informes | Operación administrativa (Playground de Foundry o cliente con HITL) |

`az login` solo te identifica: **no concede ninguno de estos roles**.

## Estado verificado (16/11/2026, comprobaciones de solo lectura)

| Elemento | Estado |
|---|---|
| Versión publicada | **v6**: el 100 % del tráfico está fijado explícitamente a `"6"` (no `@latest`). v1 a v5 se conservan. Para volver atrás, la misma regla con `"4"` |
| Código de la v6 | El de la v4/v5 con dos correcciones: la caché KEV y la protección de informes (ver más abajo). Agentes, instrucciones, herramientas y modelo, sin cambios |
| Conexiones SAS | `entrepinares-v5-sas` (v5, v6) y `entrepinares-v5-sas-21d-20261112` (v4): mismos SAS; lectura `r` y escritura `cw` de contenedor; **caducan el 03/12/2026 15:42 UTC** |
| Catálogo CISA KEV activo | **2026.11.13**, 1781 CVE, publicación activa **`20261116T072220Z-cc181488b7be49688a2b1d280f6621e7`** (activada el 16/11 a las 07:22 UTC) |

> **El catálogo activo es dinámico.** Cambia cada vez que se aprueba una actualización CISA. Consulta siempre el actual con `python scripts\consultar_kev_blob.py` en lugar de dar por fija una versión.

### Actualizaciones CISA del 16/11/2026
Las dos actualizaciones proceden de **pruebas autorizadas del propietario desde el Playground de Foundry**, cada una con aprobación HITL. El agente informó de 17 CVE nuevas, 70 modificadas y 0 retiradas respecto a la referencia histórica fija.

Cronología:
1. **07:12** Primera publicación, `20261116T071235Z-8bc180…`, que pasa a ser la activa.
2. **07:15** Se genera el informe `20261116T071514Z-936bfb65…` con esa publicación.
3. **07:22** Publicación posterior, `20261116T072220Z-cc181488…` (mismo catálogo 2026.11.13), que pasa a ser la activa.

Que el informe cite `8bc180` y el puntero indique hoy `cc181488` es lo esperado: cada informe registra la publicación vigente **cuando se generó**. **No es un error de correlación.**

Los registros de la v6 muestran **dos ejecuciones** de `actualizar_novedades_cisa_controlada`:

| Hora (UTC) | Sesión | Publicación creada y activada |
|---|---|---|
| 07:12:34 (5 s) | `426d1faa…` | `20261116T071235Z-8bc180c7be42430d832639becde64c7b` (2026.11.13) |
| 07:22:19 (5 s) | `f7435e2b…` | `20261116T072220Z-cc181488b7be49688a2b1d280f6621e7` (2026.11.13), **la activa** |

El propietario vio un error en el primer intento. Los registros disponibles no contienen ninguna línea de error en esa sesión: la herramienta terminó, la respuesta acabó con estado 200 y la publicación quedó activa. A las 07:17 hubo una petición de cancelación de una respuesta que devolvió 404. **Causa del error mostrado: desconocida (incidencia transitoria).** No se repitió ninguna operación para investigarla.

### Informe Hosted publicado tras aprobación HITL (16/11/2026)

| Campo | Valor |
|---|---|
| ID | `20261116T071514Z-936bfb65c984419a9c24888ae0742944` (07:15:14 UTC) |
| Aprobación | Solicitud HITL `generar_informes_controlados` aprobada explícitamente por el propietario |
| Archivos | `informe_vulnerabilidades.md` (SHA-256 `dc32863770c3300a…`), `informe_vulnerabilidades.html` (`30637d74226b1cce…`), `manifest.json`. Los hashes del manifiesto coinciden con los archivos |
| `origen_kev` | `azure_blob_verificado` |
| `cisa_catalog_version` | `2026.11.13` |
| `id_publicacion_kev` | `20261116T071235Z-8bc180c7be42430d832639becde64c7b`, la publicación **activa en ese momento** |
| Cribado | `recalculado_offline_desde_blob_verificado` |
| Informes anteriores | Intactos (p. ej. `20261112T122224Z-ef460b…`, mismos hashes antes y después) |

El informe cubre el **inventario ficticio completo** (incluye IT-007) y separa las coincidencias candidatas de las vulnerabilidades confirmadas.

### Enlaces de descarga con SAS (comportamiento aceptado)
Al publicar un informe, el agente devuelve **enlaces de descarga temporales con un SAS de lectura de contenedor**: dan acceso de lectura a **todos** los informes hasta el **03/12/2026 15:42 UTC**.
- **Trata esos enlaces como credenciales**: no los pegues en documentos, chats ni repositorios.
- Este repositorio no contiene ningún SAS ni URL firmada.
- Para leer un informe sin SAS usa `scripts/consultar_kev_blob.py --informe <ID>` con tu `az login` y un rol de lectura en el almacenamiento.

## Defecto de caché corregido en la v6

- **Síntoma (v4 y v5):** las preguntas KEV fallaban si llegaban en los primeros ~15 s de vida del sandbox.
- **Causa:** la caché de `v5_blob_runtime.py` empezaba en `0.0`. En un sandbox recién arrancado `time.monotonic()` es menor que 15, así que se devolvía «sin paquete» **sin leer Blob**. No era un problema de SAS.
- **Corrección:** la caché empieza en `float("-inf")`, de modo que la primera llamada lee Blob. Después de una lectura válida, la caché de 15 s funciona igual que antes.
- **Protección de informes:** con `ENTREPINARES_HABILITAR_KEV_BLOB=1`, si no hay paquete KEV activo verificado (o falla la lectura), `publicar_informes_hosted()` **falla antes de generar o escribir nada**. Nunca publica con el catálogo empaquetado.
- **Pruebas:**
  - Locales: 8 deterministas (`v5_lab/tests/test_hosted_v5_cache_informes.py`) más las 38 anteriores, todas OK.
  - Reales en la v6 (sesiones nuevas, sin esperas): `consultar_cisa` lee Blob desde la primera pregunta, la caché responde en la segunda y la correlación de IT-007 reconoce CVE-2026-124194.

## Comprobaciones de solo lectura (pasos 9-12 de la guía)

```powershell
python scripts\probar_hosted_v5.py                                    # inventario, CISA y correlación
python scripts\consultar_kev_blob.py                                  # publicación KEV activa
python scripts\consultar_kev_blob.py --informe 20261116T071514Z-936bfb65c984419a9c24888ae0742944
```

Resultado del 16/11/2026: inventario IT-004 → 11.1.2; CISA → `azure_blob_verificado`, 2026.11.13, publicación `20261116T072220Z-cc181488…`; correlación IT-007 → CVE-2026-124194 (1 coincidencia solo por fabricante, Office). Todo OK.
