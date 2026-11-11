# Caracterización de Aprendices Centro ASTIN

Solución de analítica académica para caracterizar aprendices y hacer seguimiento a las inasistencias del Centro ASTIN, Regional Valle del Cauca. Incluye un proyecto Power BI (PBIP/PBIR + TMDL), un portal agregado y una consulta nominal protegida para la página **05 · Consulta semanal**.

> **Datos personales:** `data/` está excluido de Git y la cache local del modelo (`.pbi/cache.abf`) tampoco se versiona. El repositorio debe permanecer privado y el portal público nunca debe contener nombres, documentos, justificaciones ni registros individuales. La consulta nominal se publica solo en Azure Static Web Apps con autenticación Entra ID y un Blob privado. Consulte [la guía de Azure](docs/azure_static_web_apps.md). Si el repositorio estuvo público con datos, consulte el [registro del incidente](docs/incidente_pii_2026-11-11.md).

## Estructura

- `Reporte_Inasistencias_ASTIN _V_3.0.pbip`: punto de entrada del proyecto Power BI.
- `CaracterizacionAprendicesASTIN.Report`: seis páginas y visualizaciones PBIR, tema SENA y tipografía Work Sans.
- `CaracterizacionAprendicesASTIN.SemanticModel`: modelo estrella, relaciones, columnas y medidas DAX.
- `web/index.html`: portal agregado autocontenido para Azure Static Web Apps; no incluye PII.
- `web/consulta.html`: página nominal con filtros, KPIs, semáforo y exportación CSV; requiere el rol `nominal`.
- `web/assets/`: estilos, lógica de consulta, configuración y agregación compartida con la API.
- `web/data/demo_consulta.json`: 453 registros sintéticos para la demostración local; no corresponde a aprendices reales.
- `api/`: Azure Functions v4 (Node.js 20) con `/api/consulta` y `/api/roles`.
- `api/src/shared/aggregate.js`: fuente única de la agregación semanal y el semáforo; se copia a `web/assets/aggregate.js`.
- `data/processed`: dimensiones, hechos y resumen del ETL. **No versionado.**
- `data/restricted/DIM_APRENDIZ_PII.csv`: fuente local con nombres y documentos. **No versionada.**
- `data/private/consulta_web.json`: exportación nominal para el Blob privado. **No versionada.**
- `outputs/portal_astin.html`: portal agregado local; `outputs/consulta_interna.html` es la vista nominal local y está excluida de Git.
- `scripts/01_etl_modelo_estrella.py`: limpieza, reglas de clasificación, riesgo y tablas.
- `scripts/02_generar_modelo_tmdl.py`: generador del modelo semántico (modo `Local` o `SharePoint`).
- `scripts/03_generar_reporte_pbir.py`: generador del informe PBIR.
- `scripts/04_generar_portal_html.py`: generador del portal agregado; escribe `outputs/`, `github-pages/`, `index.html` y `web/index.html`.
- `scripts/05_generar_consulta_interna.py`: vista nominal local de apoyo; no se publica.
- `scripts/06_preparar_salidas_sharepoint.py`: copia solo salidas aprobadas y vacía campos identificables.
- `scripts/07_exportar_consulta_web.py`: exportación nominal real a `data/private/` o datos sintéticos con `--demo`.
- `scripts/08_subir_consulta_azure.ps1`: valida y sube el archivo al Blob privado; opcionalmente genera un SAS de lectura.
- `scripts/09_limpiar_pii_git.ps1`: respalda y purga `data/`, `.pbi/cache.abf` y `.pbi/localSettings.json` del historial Git; requiere `git-filter-repo`.
- `scripts/10_sincronizar_agregacion.py`: sincroniza la agregación API/navegador; use `--check` en CI.
- `scripts/11_limpiar_consulta_local.ps1`: borra las copias nominales locales.
- `tools/chartjs`: distribución local de Chart.js y licencia MIT.
- `docs/azure_static_web_apps.md`: despliegue, autenticación, Blob privado, roles y validación.
- `docs/automatizacion.md`: operación del ETL, portal, Power BI y SharePoint.

## Tablas y relaciones

| Tabla | Grano / clave | Contenido |
|---|---|---|
| `DIM_CALENDARIO` | Una fila por fecha / `Fecha` | Año, trimestre, mes, semana, lunes de semana, día y periodos. |
| `DIM_APRENDIZ` | Una fila por aprendiz / `AprendizID` | Indicadores agregados, reincidencia, riesgo y `NombreCompleto` en modo local. |
| `DIM_FICHA` | Una fila por ficha / `FichaID` | Programa, jornada/modalidad disponibles, centro de costo y riesgo agregado. |
| `DIM_PROGRAMA` | Una fila por programa / `ProgramaID` | Catálogo, línea y nivel formativo derivado cuando es posible. |
| `FACT_INASISTENCIAS` | Una fila por novedad depurada / `InasistenciaID` | Fechas, horas, claves, clasificación, soporte y banderas de análisis. |

Relaciones uno a muchos y filtro unidireccional desde cada dimensión a `FACT_INASISTENCIAS`: Calendario por `Fecha`; Aprendiz por `AprendizID`; Ficha por `FichaID`; Programa por `ProgramaID`. La ficha también se relaciona con programa para el análisis de estructura académica.

Las carpetas de medidas son `00 KPIs`, `01 Inasistencias`, `02 Riesgo`, `03 Aprendices` y `04 Tendencias`. Ver [documentación del modelo](docs/modelo_datos.md) y [catálogo DAX](docs/medidas_dax.md).

## Páginas y visualizaciones

1. `00 Inicio`: resumen ejecutivo, KPI, navegación y foco operativo.
2. `01 Caracterización Aprendices`: distribución de aprendices, programas y características.
3. `02 Fichas y Programas en Riesgo`: rankings, riesgo por ficha/programa, evolución y justificación.
4. `03 Análisis Detallado`: desagregación para analizar patrones y casos.
5. `04 Calidad de Datos`: cobertura, registros dudosos, duplicados y reglas de depuración.
6. `05 Consulta semanal`: filtros por ficha, instructor e intervalo; lista aprendices por nombre, cuenta registros y suma horas. El semáforo usa la peor semana del intervalo: **Verde < 12 h**, **Amarillo 12–16 h inclusive**, **Rojo > 16 h** no justificadas.

El tema aplica la paleta institucional SENA y Work Sans. El informe usa lienzo 16:9 y navegación entre páginas.

## Indicadores

Total de inasistencias, horas perdidas, aprendices/fichas/programas afectados, proporción justificada/no justificada/sin información, reincidencia, alertas de deserción e índice compuesto de riesgo. El índice es una heurística de priorización relativa basada en percentiles; no es una probabilidad ni una decisión académica.

La imputación de una novedad al calendario usa `Fecha Inicio`. Los intervalos conservan `Fecha Fin`, pero no distribuyen las horas por día. Los duplicados exactos se eliminan después de normalizar campos y el archivo de origen nunca se modifica.

## Actualización

En Windows, con Python y las dependencias `pandas` y `xlrd` instaladas:

1. El bot sobrescribe `Inasistencias.xls` en la carpeta OneDrive configurada.
2. Ejecute el pipeline:

   ```powershell
   .\scripts\actualizar_datos.ps1
   ```

3. Abra `Reporte_Inasistencias_ASTIN _V_3.0.pbip` en Power BI Desktop y use **Inicio > Actualizar**.
4. Revise `04 Calidad de Datos` y `data/processed/00_resumen_etl.json`.
5. Para la consulta nominal, genere y suba el archivo privado:

   ```powershell
   python .\scripts\07_exportar_consulta_web.py
   .\scripts\08_subir_consulta_azure.ps1 -StorageAccount <cuenta>
   ```

El comando genera `outputs/portal_astin.html`, `github-pages/index.html`, `index.html` y `web/index.html`. El portal agrega por programa, mes, motivo, ficha con muestra suficiente y nivel de riesgo; no incluye nombres, documentos, instructores ni textos libres por aprendiz.

No suba `data/`, `data/private/`, `outputs/consulta_interna.html` ni el JSON nominal. El `.gitignore` los excluye, pero la protección real es no publicar el repositorio ni el sitio equivocado.

## Consulta nominal en Azure

La página `web/consulta.html` funciona en dos modos:

- **Demostración local:** se activa en `localhost`, `127.0.0.1`, `::1` o `file:`. Carga `web/data/demo_consulta.json` con nombres sintéticos.
- **Azure:** obtiene el principal desde `/.auth/me`, exige el rol `nominal`, llama a `/api/consulta` y recibe solo agregados. La API valida `x-ms-client-principal`, lee un Blob privado y nunca devuelve registros crudos.

Pasos resumidos (detalle en [docs/azure_static_web_apps.md](docs/azure_static_web_apps.md)):

1. Haga privado el repositorio y purgue cualquier PII del historial.
2. Cree una Static Web App **Standard** y una cuenta de almacenamiento con contenedor privado.
3. Registre una app en Entra ID, cree el grupo `ASTIN-Inasistencias-Nominal` y configure el secreto.
4. Reemplace `REPLACE_TENANT_ID` en `web/staticwebapp.config.json`.
5. Configure `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `ENTRA_NOMINAL_GROUPS`, `NOMINAL_ROLE=nominal`, `AUTH_MODE=roles` y el acceso al Blob (`BLOB_SAS_URL` o identidad administrada con Function App propia).
6. Publique con `.github/workflows/azure-static-web-apps.yml` y valide los casos autorizado/denegado.

**Limitación:** las funciones administradas de Static Web Apps no tienen identidad administrada. Para evitar SAS, vincule una Function App propia con identidad administrada; requiere plan Standard. El código soporta ambos modos.

## Modo SharePoint

Por defecto el modelo usa `Local`. Para volver a SharePoint, cambie `mode` a `SharePoint` en `config/sharepoint.json` (archivo local, excluido de Git) y regenere el modelo. En ese modo el modelo no importa PII y la página 05 muestra un código seudónimo; el código sigue siendo información sensible y requiere permisos institucionales.

La automatización prepara solo una lista permitida, omite `DIM_APRENDIZ_PII.csv` y vacía nombre, iniciales y documento enmascarado antes de copiar. No se suben credenciales al repositorio. Consulte [configuración de SharePoint](docs/automatizacion.md#salidas-etl-en-sharepoint).

## Publicación y mantenimiento

Abra el PBIP en Power BI Desktop, actualice y revise los datos, inicie sesión en el espacio de trabajo autorizado y use **Publicar**. En el servicio, configure credenciales o gateway según el origen; programe la actualización y valide una actualización manual. Aplique RLS si los usuarios no deben ver la población completa.

Al modificar columnas de origen, actualice primero el ETL, luego la especificación de tablas/columnas del generador TMDL y los visuales que las usan. El pipeline ejecuta ETL, modelo, PBIR y portal en ese orden. No publique `data/restricted`, documentos de identidad ni identificadores en claro. Mantenga respaldos del archivo fuente en un repositorio institucional con controles de acceso y retención.

## Fuentes y límites

El archivo de entrada se lee de la carpeta OneDrive descrita en `actualizar_datos.ps1`. El manual visual disponible se localizó previamente en el escritorio del equipo, junto con `Diseño dashboards.pdf`. No se encontró un catálogo maestro adicional. El tema aplica la identidad SENA disponible en los recursos del proyecto.

Jornada, modalidad, estado académico oficial, matrícula oficial y centro de costo maestro no están cubiertos de forma suficiente por el origen; la cobertura y los campos inferidos se marcan en el modelo/resumen, sin presentarlos como datos oficiales. La tabla restringida conserva el documento; solo el nombre se importa al modelo local para el uso interno solicitado. El PBIP no es un control de acceso: publique la vista nominal solo en un espacio institucional con permisos/RLS apropiados. El portal agregado tampoco es adecuado para nombres.
