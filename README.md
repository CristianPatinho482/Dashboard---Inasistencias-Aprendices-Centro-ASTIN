# Caracterización de Aprendices Centro ASTIN

Solución de analítica académica para caracterizar aprendices y hacer seguimiento a las inasistencias del Centro ASTIN, Regional Valle del Cauca. El informe se entrega como proyecto Power BI (PBIP/PBIR) y el modelo semántico como TMDL.

## Estructura

- `CaracterizacionAprendicesASTIN.pbip`: punto de entrada del proyecto.
- `CaracterizacionAprendicesASTIN.Report`: seis páginas y visualizaciones PBIR, tema institucional SENA y tipografía Work Sans.
- `CaracterizacionAprendicesASTIN.SemanticModel`: modelo estrella, relaciones, columnas y medidas DAX.
- `outputs/portal_astin.html`: portal HTML estático con Chart.js 4.6.1 y datos agregados incrustados; funciona sin conexión y no consulta servidores externos.
- `outputs/consulta_interna.html`: vista local interactiva con identidad de aprendices, filtros de ficha/instructor/fechas y semáforo semanal. Está excluida de Git y no debe copiarse al sitio público.
- `github-pages/index.html`: copia publicable del portal; se regenera automáticamente junto con el portal.
- `C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\Equipo ASTIN-DESAROLLOS POWER-BI - RAPS ASTIN 2026\Inasistencias.xls`: Excel que el bot sobrescribe en OneDrive.
- `data/processed`: dimensiones, tabla de hechos y resumen del ETL.
- `data/restricted/DIM_APRENDIZ_PII.csv`: fuente local restringida. El PBIR incorpora solo `NombreCompleto` a `DIM_APRENDIZ` para la página de consulta interna; nunca debe publicarse en el portal ni incluirse en exportaciones compartidas sin controles de acceso.
- `scripts/01_etl_modelo_estrella.py`: limpieza, reglas de clasificación, riesgo y generación de tablas.
- `scripts/02_generar_modelo_tmdl.py`: generador del modelo semántico.
- `scripts/03_generar_reporte_pbir.py`: generador del informe PBIR.
- `scripts/04_generar_portal_html.py`: generador del portal HTML autocontenido.
- `scripts/05_generar_consulta_interna.py`: generador de la vista nominal local; la salida se actualiza con `actualizar_datos.ps1` y no se publica.
- `tools/chartjs`: distribución de Chart.js y licencia MIT, incorporadas en el HTML al generar el portal.
- `scripts/actualizar_datos.ps1`: comando operativo para reprocesar la fuente.
- `scripts/06_preparar_salidas_sharepoint.py`: prepara una lista permitida de salidas ETL para SharePoint y vacía campos identificables.
- `config/sharepoint.example.json`: ejemplo de configuración sin credenciales; `config/sharepoint.json` es local y está excluido de Git.
- `docs`: documentación detallada del modelo y las medidas.

## Tablas y relaciones

| Tabla | Grano / clave | Contenido |
|---|---|---|
| `DIM_CALENDARIO` | Una fila por fecha / `Fecha` | Año, trimestre, mes, semana, lunes de semana, día y periodos; se genera para cubrir los años observados en el origen. |
| `DIM_APRENDIZ` | Una fila por aprendiz / `AprendizID` | Indicadores agregados de inasistencia, reincidencia y riesgo. Para consulta interna, el nombre se combina desde la fuente restringida; el documento permanece excluido. |
| `DIM_FICHA` | Una fila por ficha / `FichaID` | Programa, jornada/modalidad disponibles, centro de costo y riesgo agregado. |
| `DIM_PROGRAMA` | Una fila por programa / `ProgramaID` | Catálogo, línea y nivel formativo derivado cuando es posible. |
| `FACT_INASISTENCIAS` | Una fila por novedad depurada / `InasistenciaID` | Fechas, horas, claves, clasificación, soporte y banderas de análisis. |

Relaciones uno a muchos y filtro unidireccional desde cada dimensión a `FACT_INASISTENCIAS`: Calendario por `Fecha`; Aprendiz por `AprendizID`; Ficha por `FichaID`; Programa por `ProgramaID`. La ficha también se relaciona directamente con programa para permitir análisis de estructura académica.

Las carpetas de medidas son `00 KPIs`, `01 Inasistencias`, `02 Riesgo`, `03 Aprendices` y `04 Tendencias`. Ver [documentación del modelo](docs/modelo_datos.md) y [catálogo DAX](docs/medidas_dax.md).

## Páginas y visualizaciones

1. `00 Inicio`: resumen ejecutivo, KPI, navegación y foco operativo.
2. `01 Caracterización Aprendices`: distribución de aprendices, programas y características disponibles.
3. `02 Fichas y Programas en Riesgo`: rankings, riesgo por ficha/programa, evolución temporal y justificación.
4. `03 Análisis Detallado`: desagregación para analizar patrones y casos.
5. `04 Calidad de Datos`: cobertura, registros dudosos, duplicados y reglas de depuración.
6. `05 Consulta semanal`: filtro por ficha, instructor e intervalo de fechas; lista aprendices, cuenta registros y suma horas. El semáforo aplica los umbrales de horas no justificadas a la peor semana del intervalo.

El tema aplica la paleta institucional SENA y Work Sans. El informe utiliza lienzo 16:9 y navegación entre páginas.

## Indicadores

Total de inasistencias (filas depuradas), horas perdidas, aprendices/fichas/programas afectados, proporción justificada, no justificada y sin información, reincidencia, alertas de deserción y un índice compuesto de riesgo. El índice es una heurística de priorización relativa basada en percentiles, no una probabilidad ni una decisión académica. Sus reglas, pesos y umbrales se detallan en el resumen ETL y el catálogo DAX.

La imputación de una novedad al calendario usa `Fecha Inicio`. Los intervalos conservan `Fecha Fin`, pero no distribuyen las horas por día. Los duplicados exactos se eliminan después de normalizar campos y el archivo de origen nunca se modifica.

## Actualización

En Windows, con Python disponible y las dependencias `pandas` y `xlrd` instaladas:

1. El bot sobrescribe `C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\Equipo ASTIN-DESAROLLOS POWER-BI - RAPS ASTIN 2026\Inasistencias.xls`, manteniendo las columnas y la hoja `Sheet1` que consume el ETL.
2. Desde PowerShell, en la carpeta del proyecto, ejecute el pipeline ETL + modelo + PBIR:

   ```powershell
   .\scripts\actualizar_datos.ps1
   ```

3. Abra `CaracterizacionAprendicesASTIN.pbip` en Power BI Desktop y seleccione **Inicio > Actualizar** para volver a cargar los CSV generados. La fecha “Última descarga” corresponde a la modificación del Excel sincronizado; el corte analítico sigue siendo la máxima `Fecha Fin` encontrada en sus datos.
4. Revise la página `04 Calidad de Datos` y `data/processed/00_resumen_etl.json` antes de distribuir el informe.

El mismo comando genera `outputs/portal_astin.html`, `github-pages/index.html` y la raíz `index.html`, que es la entrada del sitio actual de GitHub Pages. Para publicar una actualización del portal, envíe el nuevo `index.html` a `main`; GitHub Pages no consulta OneDrive por sí solo. No suba datos fuente ni carpetas restringidas. El portal agrega datos por programa, mes, motivo, ficha con muestra suficiente y nivel de riesgo. No incluye nombres, documentos, instructores ni textos libres por aprendiz. Aun con datos agregados, trátelo como información institucional y publique solo con autorización. Consulte [la guía de GitHub Pages](docs/publicacion_github_pages.md) y [la guía de automatización](docs/automatizacion.md).

Por defecto el modelo importa CSV locales. Se agregó un modo SharePoint configurable para que el modelo lea las salidas ETL desde el sitio institucional. La automatización prepara solo una lista permitida, omite `DIM_APRENDIZ_PII.csv` y vacía nombre, iniciales y documento enmascarado antes de copiar. No se suben credenciales al repositorio. El modo cloud requiere crear una carpeta de salidas, completar la configuración local, regenerar el PBIP y validar credenciales en Power BI Desktop y Service.

En modo local, `RutaDatos` y `RutaDatosRestringidos` apuntan a `data/processed` y `data/restricted`. En modo SharePoint, `SitioSharePoint` y `RutaDatosSharePoint` apuntan al sitio y a la carpeta de CSV aprobados. La página de consulta semanal cambia de nombre a código seudónimo; el modelo cloud no importa PII. El identificador seudónimo y los eventos individuales siguen siendo información institucional sensible y requieren permisos apropiados. El portal de GitHub Pages sigue siendo agregado. Consulte [configuración de SharePoint](docs/automatizacion.md#salidas-etl-en-sharepoint).

## Publicación y mantenimiento

Abra el PBIP en Power BI Desktop, actualice y revise los datos, inicie sesión en el espacio de trabajo autorizado y use **Publicar**. En el servicio, establezca credenciales; configure gateway para fuentes locales o migre a SharePoint/OneDrive según el procedimiento institucional; luego configure la programación y valide una actualización manual. Aplique RLS si los usuarios no deben ver la población completa.

Al modificar columnas de origen, actualice primero el ETL, luego la especificación de tablas/columnas del generador TMDL y los visuales que las usan. El pipeline ejecuta ETL, modelo, PBIR y portal en ese orden. No publique `data/restricted`, documentos de identidad ni identificadores en claro. Mantenga respaldos del archivo fuente en repositorio institucional con controles de acceso y retención.

## Fuentes y límites

El archivo de entrada se lee de la carpeta OneDrive descrita arriba; el manual visual disponible se localizó previamente en `C:\Users\capatino\Desktop\Inasistencias\Manual de identidad corporativa sena 2024.pdf`, junto con `Diseño dashboards.pdf` en el proyecto. No se encontró un catálogo maestro adicional. El tema del informe aplica identidad SENA disponible en los recursos del proyecto. Jornada, modalidad, estado académico oficial, matrícula oficial y centro de costo maestro no están cubiertos de forma suficiente por el origen; la cobertura y los campos inferidos se marcan en el modelo/resumen, sin presentarlos como datos oficiales. La tabla restringida conserva el documento; solo el nombre se importa al modelo para el uso interno solicitado. El modelo PBIP no es por sí mismo un control de acceso: publique la vista nominal únicamente en un espacio institucional con permisos/RLS apropiados. El portal GitHub Pages no es adecuado para esta vista porque su sitio actual es público.
