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
2. **Despliegue Hosted (ya hecho).** El workflow está empaquetado como agente *Hosted* de Microsoft Foundry (`entrepinares-itot-v5-lab`). **No se vuelve a desplegar** en esta formación.
3. **Consulta remota.** `scripts/probar_hosted_v5.py` envía preguntas al agente con tu sesión de `az login` (protocolo *responses*).
4. **Lectura KEV en Azure Blob.** En Hosted, el catálogo CISA KEV no sale de la copia empaquetada: el agente lee un **puntero** (`control/version_activa.json`) que indica qué **publicación verificada** (`versiones/<id>/`) está activa, y comprueba sus hashes SHA-256.
5. **Informe persistido.** Cuando un administrador lo aprueba explícitamente (aprobación humana), el agente genera los informes Markdown + HTML y los guarda en Blob (`informes/<id>/`) con un **manifiesto** que registra qué catálogo y qué publicación KEV se usaron.

## Qué necesitas para cada parte

| Parte | Permiso necesario (además de `az login`) |
|---|---|
| Consultar el agente Hosted | Rol en el proyecto Foundry que permita invocar agentes (p. ej. *Azure AI User*) |
| Leer el puntero KEV y los manifiestos (`scripts/consultar_kev_blob.py`) | Rol de lectura de datos en la cuenta de almacenamiento (p. ej. *Storage Blob Data Reader*) |
| Que el **agente** lea Blob | La conexión del proyecto con SAS de lectura vigentes (gestión del administrador) |
| Publicar KEV o informes | Operación administrativa con aprobación humana: **fuera** del recorrido didáctico |

`az login` solo te identifica: **no concede ninguno de estos roles**.

## Estado verificado (14/11/2026, solo lectura)

| Comprobación | Resultado |
|---|---|
| Agente Hosted | `entrepinares-itot-v5-lab`, **versión 4** activa; el endpoint enruta el 100 % del tráfico a `@latest` (v4). Versiones 1-3 siguen existiendo |
| Conexión SAS que usa la v4 | `entrepinares-v5-sas-21d-20261112`: lectura `r` y escritura `cw`, de contenedor, **vigentes hasta el 03/12/2026 15:42 UTC** |
| Conexión anterior | `entrepinares-v5-sas`: los cuatro SAS **caducaron el 13/11/2026 11:54 UTC** (solo la usaban las versiones 2 y 3) |
| Puntero KEV activo en Blob | Publicación `20261113T135058Z-17735c10705a4565baae8926ee9e9966`, catálogo **2026.11.10**, 1779 CVE, activada el 13/11/2026 13:51 UTC; hashes SHA-256 verificados |
| Informe publicado consultado | `20261112T122224Z-ef460b7657ca4e2ab756c478c722ff5a`: catálogo 2026.11.10, origen `azure_blob_verificado`, publicación KEV **`20261112T122111Z-d4ec…`** (una publicación **anterior** a la activa, con la misma versión de catálogo) |
| Inventario vía Hosted | ✅ Responde correctamente (IT-004 → 11.1.2) |
| `consultar_cisa` vía Hosted | ❌ «No ha sido posible leer/verificar el catálogo KEV activo» |
| Correlación vía Hosted (IT-007 / CVE-2026-124194, que solo existe en el catálogo activo) | ❌ «el catálogo KEV activo no está disponible en Blob» |

**Conclusión:** el puntero y el paquete KEV son legibles y válidos desde fuera con el **mismo** SAS de lectura que referencia la v4, pero **el agente desplegado no consigue leerlos**. Por diseño, el agente **no** recurre en silencio a su copia empaquetada: devuelve el error. Que un informe antiguo usara 2026.11.10 **no** demuestra que una ejecución nueva use el catálogo activo actual.

**Causa probable (sin confirmar):** el contenedor de la v4 no recibe el SAS de lectura (`ENTREPINARES_KEV_READ_SAS` vacío), porque la referencia a la conexión no se resuelve en tiempo de ejecución. Para confirmarlo hace falta revisar los registros del contenedor de la v4, que puede contener datos sensibles: requiere autorización y revisión previa.

**Acciones posibles (requieren autorización; no se ha hecho ninguna):**
1. Revisar los registros de la v4 en el portal de Foundry.
2. Comprobar en el portal que la conexión `entrepinares-v5-sas-21d-20261112` es accesible para la identidad del agente.
3. Si se confirma la causa: nueva versión del agente con el mismo código (redespliegue) o ajuste de la conexión. Ambas son operaciones administrativas.

## Cómo comprobarlo tú (pasos 12-14 de la guía)

```powershell
python scripts\probar_hosted_v5.py --esperar-version 2026.11.10     # inventario, CISA, correlación
python scripts\consultar_kev_blob.py                                 # publicación KEV activa
python scripts\consultar_kev_blob.py --informe 20261112T122224Z-ef460b7657ca4e2ab756c478c722ff5a
```

Mientras el bloqueo siga, las pruebas `cisa` y `correlacion` del cliente salen **NO SUPERADA**. Es el resultado real y esperado, no un fallo del cliente.
