# Solicitud de acceso a Microsoft Azure

Nota de sustento para responder a la Mesa de Servicios TIC y escalar la solicitud
al Grupo de Infraestructura de la Oficina de Sistemas y al Gestor de Licenciamiento.

> **Idea central:** no se solicita instalar **Azure CLI**. Se solicita acceso al
> **servicio Microsoft Azure**, que sí está registrado en el catálogo de productos
> autorizados. Azure CLI es una herramienta cliente gratuita y no requiere
> licenciamiento; además, no es necesaria para el proyecto porque la publicación
> se puede gestionar desde el portal de Azure y Azure Cloud Shell.

## 1. Hallazgos en el catálogo

Archivo: `2026-07-10 TI-SENA-ID001-Catálogo Productos Atención Mesa de Servicios Actualizado Vrs 19.xlsx`, hoja `Listado Productos Autorizados`.

| Producto (fila) | Vigencia | Uso en el proyecto | Observación |
|---|---|---|---|
| **Microsoft Azure** (245) | **2024-05-31** | Static Web Apps, Storage privado, API | 257 licencias. Dirección General / Oficina de Sistemas. Requiere autorización del Grupo de Infraestructura. **Confirmar si está vigente o debe renovarse.** |
| **Azure AD Basic for EDU** (262), **P1** (263), **P2** (264), **MFA** (280) | 2027-05-31 | Login con Entra ID, grupos, MFA | Cubre la autenticación de la consulta nominal. |
| **Azure Information Protection P1/P2** (266-267), **Rights Management** (268) | 2027-05-31 | Protección/cifrado | Opcional. |
| **Azure DevOps Server Online/On Premise** (227-228) | 2027-05-31 | CI/CD | 10 licencias; destinadas al Centro de Datos/Infraestructura. No son necesarias para este proyecto. |
| **Power BI Pro** (308) | 2027-05-31 | Plan B: informe con RLS | Solo áreas administrativas; asignación bajo demanda. |
| **SharePoint Plan 2 for EDU** (312) | 2027-05-31 | Plan B: sitio interno/SPFx | Disponible para todos. |
| **Power Apps Premium for EDU** (238) | 2027-05-31 | Plan B: app interna | 390 licencias; restringida al Centro de Datos/Infraestructura. |
| **Microsoft 365 A5** (251-252) | 2027-05-31 | Base de identidad/colaboración | 48.882 profesores / 1.955.280 estudiantes. |
| **Software Libre** (hoja aparte) | — | Node.js, Python, Git, Docker, PostgreSQL, MySQL, Jenkins | Aprobados; son herramientas locales, no un servicio de hosting. |

### Dato crítico: vigencia

La fila de **Microsoft Azure** registra vigencia **2024-05-31**, anterior a la
fecha del catálogo (2026-07-10). El propio catálogo advierte en la hoja
`Instrucciones`:

> "Tener en cuenta la vigencia del producto, ya que todos no se encuentran vigentes."

Por eso la solicitud debe preguntar de forma explícita si la suscripción está
activa o si hay que renovarla. Las filas de Entra ID/MFA y Microsoft 365 sí
están vigentes hasta **2027-05-31**.

## 2. Lectura correcta del catálogo

El catálogo es un **inventario de licencias de software**, no un catálogo de
servicios cloud. Por eso:

- **Azure CLI** no aparece: es una herramienta gratuita de cliente, no un
  producto licenciado. Su ausencia no bloquea el proyecto.
- **Microsoft Azure** sí aparece como producto/servicio bajo el acuerdo
  *Microsoft Enterprise For Education Solutions VLSC*.
- **Azure Cloud Shell** evita instalar el CLI, pero **no sustituye la
  suscripción**: sin suscripción no se pueden crear recursos.
- Para datos personales de aprendices se necesita una **suscripción
  institucional** del SENA. Una cuenta gratuita, Azure for Students o Azure Dev
  Tools sirven para demostración con datos sintéticos, no para PII real.

## 3. Datos que debe entregar TI

| Dato | Uso |
|---|---|
| Tenant ID | Reemplazar `REPLACE_TENANT_ID` y configurar el registro de app. |
| Subscription ID | Seleccionar la suscripción en Azure. |
| Resource group | Crear Storage y Static Web App, o confirmar uno existente. |
| Región | Aproximada a los usuarios; `eastus2` es una referencia. |
| Rol asignado | `Contributor` sobre el resource group. |
| Confirmación de tratamiento de PII | Que la suscripción es institucional y está autorizada para datos de aprendices. |
| Permisos en Entra ID | Si el solicitante puede crear app registrations y grupos, o si lo hace la Oficina de Sistemas. |

Si en lugar de un resource group entregan solo la suscripción con permiso para
crearlo, se ejecuta la Fase 2 del
[checklist de publicación](checklist_publicacion_azure.md).

## 4. Formato y radicación

El catálogo tiene dos formatos relacionados:

| Formato | Nombre | Cuándo usarlo |
|---|---|---|
| `GTI-F-104` | Formato Solicitud y Viabilidad Microsoft Azure Dev Tools (antes Microsoft Imagine) | Programa académico Azure Dev Tools. **No usar para PII real** salvo que la Oficina de Sistemas confirme que la suscripción es la institucional. |
| `GTI-F-112` | Formato Solicitud Centro de Datos | Hosting en servidores del Centro de Datos SENA. No es la ruta recomendada para una página pública con PII. |

Las instrucciones del catálogo indican que el formato debe adjuntarse a la
solicitud de servicio en la herramienta de gestión y escalarse al Gestor de
Licenciamiento. Si el formato aplicable no es ninguno de los dos, la solicitud
debe radicarse como requerimiento general y escalarse al Grupo de Infraestructura
de la Oficina de Sistemas.

## 5. Plan B si no autorizan Azure

| Alternativa | Vigencia | Ventaja | Limitación |
|---|---|---|---|
| **Power BI Pro** (308) | 2027-05-31 | Informe nominal con RLS y grupo de Entra ID; no requiere infraestructura de Azure. | Cambia la entrega de página HTML a informe de Power BI; asignación bajo demanda y solo áreas administrativas. |
| **SharePoint Plan 2 + SPFx** (312) | 2027-05-31 | Se mantiene el portal interno y el control de acceso con Entra ID. | Requiere desarrollo SPFx y aprobación del administrador del tenant. |
| **Power Apps Premium** (238) | 2027-05-31 | App interna con control de acceso. | Restringida al Centro de Datos/Infraestructura; no aplica sin su autorización. |
| **Centro de Datos SENA** (`GTI-F-112`) | — | Infraestructura institucional. | Requiere servidor, red, exposición y aprobaciones de seguridad; no recomendado para página pública con PII. |

## 6. Correo sugerido

```text
Asunto: Solicitud de acceso al servicio Microsoft Azure (no instalación de Azure CLI)
        — Consulta de inasistencias Centro ASTIN

Buen día, equipo de Mesa de Servicios TIC:

Agradezco su respuesta y la revisión del catálogo. Preciso el alcance de mi
solicitud para que pueda escalarse correctamente.

No solicito la instalación de Azure CLI. Es una herramienta cliente gratuita,
no requiere licenciamiento y no es necesaria para el proyecto: la publicación
se puede gestionar desde el portal de Microsoft Azure y Azure Cloud Shell, que
son servicios web.

Lo que necesito es acceso al servicio Microsoft Azure para publicar una página
interna de consulta de inasistencias del Centro ASTIN. En el catálogo adjunto
(Versión 19) encontré:

- Microsoft Azure — 257 licencias — Dirección General / Oficina de Sistemas —
  observación: "Asignación de servicios o suscripciones requiere autorización
  de la Oficina de Sistemas a través de su grupo de Infraestructura" (fila 245).
  La vigencia registrada es 2024-05-31; agradezco confirmar si está vigente o
  si debe renovarse.

- Azure Active Directory Premium P1/P2, Azure AD Basic for EDU y Microsoft
  Azure MFA — vigentes hasta 2027-05-31 (filas 262-264 y 280), que cubren la
  autenticación.

- Power BI Pro y SharePoint Plan 2 for EDU — vigentes hasta 2027-05-31
  (filas 308 y 312), como alternativas si no es posible habilitar una
  suscripción de Azure.

Solicito:

1. Autorización para usar una suscripción de Microsoft Azure del acuerdo
   institucional, o la creación de un resource group para el proyecto.
2. Confirmación de si la licencia de Microsoft Azure (fila 245) está vigente;
   si no, el procedimiento para renovarla o solicitar una nueva suscripción.
3. Los datos de conexión: Tenant ID, Subscription ID, resource group y región,
   o autorización para crearlos.
4. Indicación del formato que debo diligenciar. En el catálogo veo el GTI-F-104
   (Azure Dev Tools) y el GTI-F-112 (Centro de Datos); agradezco confirmar cuál
   aplica o si debo radicar la solicitud por otro medio.
5. Confirmación de si la suscripción es institucional y está autorizada para
   tratar datos personales de aprendices, o si debo escalar el caso a
   privacidad/seguridad.

Contexto: el portal público solo muestra indicadores agregados. La consulta
nominal queda detrás de autenticación con Entra ID y solo la ven las personas
autorizadas por Bienestar/Coordinación Académica. Los datos reales no se
publican en GitHub ni en archivos estáticos; permanecen en un almacenamiento
privado. El repositorio es privado.

Agradezco escalar esta solicitud al Grupo de Infraestructura de la Oficina de
Sistemas y al Gestor de Licenciamiento, según corresponda.

Cordialmente,
Andrés [apellidos]
Centro ASTIN — Regional Valle
[correo institucional] | [teléfono]
```

## 7. Próximos pasos

1. Enviar el correo o radicar la solicitud con el formato que TI indique.
2. Si TI confirma la suscripción, continuar con la Fase 2 del
   [checklist de publicación](checklist_publicacion_azure.md) en Azure Cloud Shell.
3. Si TI confirma que la licencia de Azure está vencida, solicitar renovación o
   evaluar el Plan B con Power BI Pro / SharePoint.
4. No cargar datos reales hasta tener una suscripción institucional autorizada
   para PII.

## Referencias

- Catálogo: `2026-07-10 TI-SENA-ID001-Catálogo Productos Atención Mesa de Servicios Actualizado Vrs 19.xlsx`.
- Runbook: [`checklist_publicacion_azure.md`](checklist_publicacion_azure.md).
- Arquitectura: [`azure_static_web_apps.md`](azure_static_web_apps.md).
