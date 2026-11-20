# Resumen de actividades de desarrollo — noviembre de 2026

**Periodo:** 1 al 20 de noviembre de 2026  
**Repositorio:** `Dashboard---Inasistencias-Aprendices-Centro-ASTIN` (privado)  
**Rama principal:** `main`  
**Rama de trabajo:** `codex/intervalo-6-horas`  
**Último commit:** `4706df4` — 2026-11-12  
**Elaborado:** 2026-11-20  
**Alcance:** desarrollo de la página 05, API, seguridad de datos, modelo Power BI, documentación y preparación de la publicación en Azure.

## 1. Resumen ejecutivo

- Se completó la página **05 · Consulta semanal** con filtros, KPIs, semáforo y exportación CSV, sin agregar una página nueva al portal.
- Se implementó una **API autenticada** (`/api/consulta` y `/api/roles`) que agrega en el servidor y nunca devuelve registros crudos.
- Se dejó lista la arquitectura de publicación en **Azure Static Web Apps + Blob privado**, con autenticación Entra ID y rol `nominal`, como alternativa sujeta a licenciamiento.
- Se habilitó el **portal local completo** (`outputs/portal_local_completo.html`): un único HTML con las seis vistas, incluida la página 05 nominal, que funciona con doble clic y sin servidor.
- Se corrigió el proyecto **PBIP/PBIR + TMDL** y se generó la exportación real para el Blob privado.
- Se ejecutó la **limpieza de PII** del historial Git y una auditoría de seguridad del repositorio.
- Se documentó la **ruta de licenciamiento ante TI**: la solicitud es por el servicio Microsoft Azure, no por Azure CLI.
- **Estado técnico:** entrega local lista para usar. **Bloqueo de Azure:** falta una suscripción institucional y confirmar la vigencia de la licencia registrada en el catálogo de TI.

## 2. Producto y datos

### Página 05 · Consulta semanal

- Se mantuvieron los **5 dashboards agregados** del portal (00 a 04) y se completó la página 05.
- Filtros por **ficha**, **instructor**, **rango de fechas** y **búsqueda de aprendiz**.
- KPIs de aprendices, inasistencias, horas totales y horas no justificadas.
- Tabla nominal con nombre, ficha, instructor, registros, horas y horas no justificadas.
- Semáforo por peor semana del intervalo:
  - **Verde:** menos de 12 h.
  - **Amarillo:** 12 a 16 h inclusive.
  - **Rojo:** más de 16 h no justificadas.
- Exportación CSV con diálogo de confirmación y advertencia de datos personales.
- Modo demostración automático en `localhost`, `127.0.0.1`, `::1` o `file:`; en Azure usa la API autenticada.

### Agregación y API

- Lógica de agregación compartida entre navegador y servidor:
  - `web/assets/aggregate.js`
  - `api/src/shared/aggregate.js`
- Prueba de sincronización para garantizar que ambas copias producen el mismo resultado.
- Endpoints:
  - `GET /api/consulta`: valida la sesión, lee el Blob privado, agrega y devuelve solo totales.
  - `GET /api/roles`: `rolesSource` de Static Web Apps; asigna el rol `nominal`.
- Autenticación mediante `x-ms-client-principal`; modos `allowlist` y `roles`.
- Caché de consulta con TTL de 300 segundos.

### Datos

- Exportación real generada en `data/private/consulta_web.json`:
  - **16.243 registros**
  - **1.483 aprendices**
  - Periodo **2026-02-02 a 2026-10-30**
  - Tamaño aproximado: **2,78 MB**
  - Archivo ignorado por Git.
- Datos sintéticos de demostración:
  - **453 registros**
  - **72 aprendices**
  - **8 fichas**
  - Sin nombres reales.
- El portal agregado no contiene nombres, documentos, instructores ni textos libres por aprendiz.

### Power BI

- Informe de **6 páginas** (00 a 05); la página 05 usa `DIM_APRENDIZ[NombreCompleto]` en modo local.
- Modelo estrella con 5 tablas reales: `DIM_CALENDARIO`, `DIM_APRENDIZ`, `DIM_FICHA`, `DIM_PROGRAMA` y `FACT_INASISTENCIAS`.
- Se corrigió el error de apertura del PBIP eliminando **7 tablas automáticas de fecha** locales (`LocalDateTable_*.tmdl` y `DateTableTemplate_*.tmdl`) que no tenían relaciones de variación.
- El PBIP abre correctamente en Power BI Desktop y el árbol de trabajo quedó limpio.

## 3. Seguridad y privacidad

- Se detectó y documentó un incidente de exposición de datos personales en el historial Git.
- Se ejecutaron **dos pasadas** de `git-filter-repo`:
  1. Eliminación de todas las rutas `data/`.
  2. Eliminación de `cache.abf` y `localSettings.json`.
- Se hizo **push forzado** de ramas y etiquetas; `main` y `codex/intervalo-6-horas` quedaron sincronizados.
- Se eliminó el artefacto `github-pages` (54 MB) y se deshabilitó GitHub Pages.
- Auditoría de **1.140 archivos versionados**: sin nombres, documentos, IDs de aprendices ni instructores reales.
- Escaneo de secretos en el árbol actual: sin claves, tokens, cadenas de conexión ni SAS.
- Repositorio **privado**, **0 forks**, 1 colaborador, 0 invitaciones, 0 deploy keys, 0 hooks y 0 releases.
- Controles implementados:
  - `data/` excluido de Git.
  - `web/` sin PII.
  - Blob privado; la API lo lee en el servidor.
  - La API nunca devuelve registros crudos.
  - SAS de solo lectura para el modo de API administrada.
- Pendientes de seguridad:
  - Solicitar a GitHub Support la purga de cachés y objetos inaccesibles de commits antiguos.
  - Notificar al contacto de privacidad/seguridad del SENA.
  - Mover o destruir los respaldos con PII que están en `%TEMP%`.

## 4. Publicación y entrega

### Arquitectura preparada

```text
Navegador
   │
   ├── web/index.html          Portal agregado (sin PII)
   └── web/consulta.html       Consulta nominal (rol "nominal")
            │
            │ fetch /api/consulta
            ▼
Azure Static Web Apps (plan Standard)
   ├── Autenticación Entra ID
   ├── /api/roles              rolesSource → rol "nominal"
   └── /api/consulta           agrega en el servidor
            │
            ▼
Azure Blob Storage privado
   └── consulta_web.json       Solo lectura mediante SAS
```

### Componentes implementados

- `web/staticwebapp.config.json`: rutas, CSP, `rolesSource`, proveedor Entra ID y `REPLACE_TENANT_ID` pendiente.
- `web/assets/config.js`: `demoMode` automático en localhost; `requiredRole: "nominal"`.
- `api/src/functions/roles.js`: asigna el rol `nominal` por allowlist, app roles o grupos.
- `api/src/shared/storage.js`: lectura del Blob privado con SAS o identidad administrada.
- `.github/workflows/azure-static-web-apps.yml`: valida y omite el despliegue si falta `AZURE_STATIC_WEB_APPS_API_TOKEN`.
- `scripts/07_exportar_consulta_web.py`: genera la exportación real o sintética.
- `scripts/08_subir_consulta_azure.ps1`: valida, sube el Blob y opcionalmente genera el SAS.
- `scripts/09_limpiar_pii_git.ps1`: purga PII del historial.
- `scripts/10_sincronizar_agregacion.py`: verifica la copia de agregación navegador/API.
- `scripts/11_limpiar_consulta_local.ps1`: borra copias nominales locales.

### Documentación de despliegue

- `docs/azure_static_web_apps.md`: arquitectura, requisitos, Entra ID, variables, despliegue, validación y rollback.
- `docs/checklist_publicacion_azure.md`: runbook por fases (0 a 7) con comandos para Azure Cloud Shell.
- `docs/solicitud_ti_azure.md`: sustento de la solicitud a TI, hallazgos del catálogo, formatos y correo sugerido.

### Modo local principal

- `scripts/12_generar_portal_local.py` integra las seis vistas en un solo HTML y embebe los datos nominales, Chart.js, el logo y la agregación compartida.
- `scripts/actualizar_datos.ps1` ejecuta el generador al final del pipeline, después del ETL y de la sincronización de la agregación.
- El archivo se abre desde `file://` sin `fetch` ni servidor local; los filtros, KPIs, semáforo y CSV de la página 05 funcionan en el mismo documento.
- `outputs/portal_local*.html` está excluido por `.gitignore`; `scripts/11_limpiar_consulta_local.ps1` borra las copias locales.
- Documentación de uso: `docs/portal_local.md`.

### Bloqueos actuales de Azure

- No hay **suscripción, tenant ni resource group** de Azure asignados.
- **Azure CLI no está autorizado** por TI y su instalación local requiere administrador. Se documentó que no es necesario: la publicación se puede gestionar desde el portal y Azure Cloud Shell.
- La suscripción debe ser **institucional del SENA** para tratar PII de aprendices; una cuenta gratuita solo sirve para demostración sintética.
- El catálogo de TI registra **Microsoft Azure** en la fila 245 con **257 licencias**, Dirección General / Oficina de Sistemas, pero con vigencia **2024-05-31**. Hay que confirmar si está vigente o si debe renovarse.
- Las licencias de **Entra ID / MFA** y **Microsoft 365** están vigentes hasta **2027-05-31**.

## 5. Pruebas y validación

| Prueba | Resultado |
|---|---|
| Pruebas de agregación de la API | **6/6 correctas** (`node --test api/test/aggregate.test.js`) |
| Copia navegador/API | Idéntica |
| Semáforo y filtros | Validados |
| Validación local de `consulta.html` | 453 registros sintéticos, 72 aprendices, KPIs y filtros correctos |
| Exportación CSV | Diálogo de confirmación y descarga correcta |
| Consola del navegador | 0 errores |
| Portal `index.html` | 5 secciones, sin errores |
| Exportación real | 16.243 registros, 1.483 aprendices, 2,78 MB |
| PBIP | Abre correctamente; modelo con 5 tablas reales |
| Auditoría de PII | 1.140 archivos, 0 hallazgos |
| Escaneo de secretos | Sin hallazgos en el árbol actual |

Pendiente: validación integral en Azure (login, rol, 401/403, Blob 403/404 y ausencia de PII en DevTools > Network).

## 6. Trazabilidad de commits

| Fecha | Commit | Actividad |
|---|---|---|
| 2026-11-03 | `f6943d5` | Actualiza portal y definiciones del reporte |
| 2026-11-11 | `4016272` | Integra consulta nominal segura y despliegue en Azure (46 archivos) |
| 2026-11-11 | `b46b1f3` | Corrige la ruta con tildes en la limpieza de historial |
| 2026-11-11 | `5e0159a` | Limita la verificación de PII a ramas y etiquetas |
| 2026-11-11 | `577c056` | Registra la limpieza de PII y corrige codificación de PowerShell |
| 2026-11-11 | `18b256e` | Registra el incidente de PII y las plantillas de notificación |
| 2026-11-11 | `714984b` | Añade el escaneo de secretos al registro del incidente |
| 2026-11-11 | `f1e9d24` | Purga la caché local de Power BI del historial |
| 2026-11-11 | `a6d230c` | Documenta la purga de la caché local de Power BI |
| 2026-11-11 | `e4cf8f9` | Corrige el conteo de archivos auditados |
| 2026-11-11 | `3ec3077` | Corrige la nota sobre el plan Free en la configuración web |
| 2026-11-11 | `eae2d77` | Corrige el nombre del PBIP en el README |
| 2026-11-11 | `57d1455` | Documenta la eliminación del artefacto de Pages |
| 2026-11-11 | `70ddb66` | Omite el despliegue cuando falta el token de Azure |
| 2026-11-11 | `4ea21e6` | Alinea la documentación con GitHub Pages deshabilitado |
| 2026-11-11 | `a6e3efc` | Actualiza el commit final en la documentación |
| 2026-11-11 | `aa288ab` | Evita referencias obsoletas al commit en la documentación |
| 2026-11-12 | `747b494` | Agrega runbook de publicación en Azure |
| 2026-11-12 | `4706df4` | Documenta la solicitud de acceso a Azure ante TI |

**Total:** 19 commits en el periodo, aproximadamente 9.724 líneas agregadas y 169 eliminadas. El commit principal (`4016272`) concentra 46 archivos y 9.069 inserciones.

## 7. Estado y próximos pasos

### Estado

| Área | Estado |
|---|---|
| Página 05 y API | Completas y probadas |
| Modelo Power BI / PBIP | Corregido y operativo |
| Seguridad del repositorio | PII purgada y auditoría limpia; quedan acciones externas |
| Portal local completo | Generado y validado con datos reales y sintéticos |
| Publicación en Azure | Preparada, bloqueada por suscripción y licenciamiento |
| Documentación | Runbook, arquitectura, solicitud a TI y modo local disponibles |

### Próximos pasos

1. Usar el portal local completo como entrega principal: regenerarlo con cada descarga y borrarlo al terminar la revisión.
2. Enviar el correo o radicar la solicitud ante la Mesa de Servicios TIC, citando la fila 245 del catálogo.
3. Confirmar si la licencia de Microsoft Azure está vigente o si debe renovarse.
4. Si TI aprueba la suscripción, ejecutar la Fase 2 del runbook en Azure Cloud Shell.
5. Crear el registro de app y el grupo en Entra ID; configurar secreto, SAS y variables de la Static Web App.
6. Reemplazar `REPLACE_TENANT_ID`, configurar `AZURE_STATIC_WEB_APPS_API_TOKEN` y desplegar.
7. Ejecutar la validación de seguridad de la Fase 6.
8. Si no se autoriza Azure, mantener el modo local o evaluar **Power BI Pro** / **SharePoint Plan 2**.
9. Completar las acciones pendientes del incidente de PII (GitHub Support, notificación interna y respaldos).

## 8. Notas

- El catálogo de TI se analizó como archivo local y **no se versionó** en el repositorio.
- La trazabilidad se basa en los commits del periodo y en las sesiones de validación locales; las fechas de actividades no versionadas son aproximadas.
- No se incluyeron nombres, documentos, correos ni registros individuales de aprendices en este resumen.
- Las cifras de datos son agregadas y provienen de la exportación real y del conjunto sintético de demostración.
- El portal local completo contiene PII y no debe publicarse; Azure sigue siendo la alternativa para una publicación institucional autorizada.

## Referencias

- [`README.md`](../README.md)
- [`docs/portal_local.md`](portal_local.md)
- [`docs/azure_static_web_apps.md`](azure_static_web_apps.md)
- [`docs/checklist_publicacion_azure.md`](checklist_publicacion_azure.md)
- [`docs/solicitud_ti_azure.md`](solicitud_ti_azure.md)
- [`docs/incidente_pii_2026-11-11.md`](incidente_pii_2026-11-11.md)
- [`docs/modelo_datos.md`](modelo_datos.md)
- [`docs/medidas_dax.md`](medidas_dax.md)
