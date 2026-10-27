# Caracterización de Aprendices Centro ASTIN

Solución de analítica académica para caracterizar aprendices y hacer seguimiento a las inasistencias del Centro ASTIN, Regional Valle del Cauca. El informe se entrega como proyecto Power BI (PBIP/PBIR) y el modelo semántico como TMDL.

## Estructura

- `CaracterizacionAprendicesASTIN.pbip`: punto de entrada del proyecto.
- `CaracterizacionAprendicesASTIN.Report`: cinco páginas y visualizaciones PBIR, tema institucional SENA y tipografía Work Sans.
- `CaracterizacionAprendicesASTIN.SemanticModel`: modelo estrella, relaciones, columnas y medidas DAX.
- `outputs/portal_astin.html`: portal HTML estático con Chart.js 4.6.1 y datos agregados incrustados; funciona sin conexión y no consulta servidores externos.
- `C:\Users\capatino\Desktop\Inasistencias\Inasistencias.xls`: archivo Excel de entrada identificado en el equipo. Reemplace este archivo para procesar un nuevo extracto.
- `data/processed`: dimensiones, tabla de hechos y resumen del ETL.
- `data/restricted/DIM_APRENDIZ_PII.csv`: datos personales identificables; no importar ni publicar.
- `scripts/01_etl_modelo_estrella.py`: limpieza, reglas de clasificación, riesgo y generación de tablas.
- `scripts/02_generar_modelo_tmdl.py`: generador del modelo semántico.
- `scripts/03_generar_reporte_pbir.py`: generador del informe PBIR.
- `scripts/04_generar_portal_html.py`: generador del portal HTML autocontenido.
- `tools/chartjs`: distribución de Chart.js y licencia MIT, incorporadas en el HTML al generar el portal.
- `scripts/actualizar_datos.ps1`: comando operativo para reprocesar la fuente.
- `docs`: documentación detallada del modelo y las medidas.

## Tablas y relaciones

| Tabla | Grano / clave | Contenido |
|---|---|---|
| `DIM_CALENDARIO` | Una fila por fecha / `Fecha` | Año, trimestre, mes, semana, día y periodos; se genera para cubrir los años observados en el origen. |
| `DIM_APRENDIZ` | Una fila por aprendiz seudonimizado / `AprendizID` | Indicadores agregados de inasistencia, reincidencia y riesgo. No contiene nombres ni documento en claro. |
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

El tema aplica la paleta institucional SENA y Work Sans. El informe utiliza lienzo 16:9 y navegación entre páginas.

## Indicadores

Total de inasistencias (filas depuradas), horas perdidas, aprendices/fichas/programas afectados, proporción justificada, no justificada y sin información, reincidencia, alertas de deserción y un índice compuesto de riesgo. El índice es una heurística de priorización relativa basada en percentiles, no una probabilidad ni una decisión académica. Sus reglas, pesos y umbrales se detallan en el resumen ETL y el catálogo DAX.

La imputación de una novedad al calendario usa `Fecha Inicio`. Los intervalos conservan `Fecha Fin`, pero no distribuyen las horas por día. Los duplicados exactos se eliminan después de normalizar campos y el archivo de origen nunca se modifica.

## Actualización

En Windows, con Python disponible y las dependencias `pandas` y `xlrd` instaladas:

1. Reemplace `C:\Users\capatino\Desktop\Inasistencias\Inasistencias.xls` manteniendo las columnas y la hoja `Sheet1` que consume el ETL.
2. Desde PowerShell, en la carpeta del proyecto, ejecute el pipeline ETL + modelo + PBIR:

   ```powershell
   .\scripts\actualizar_datos.ps1
   ```

3. Abra `CaracterizacionAprendicesASTIN.pbip` en Power BI Desktop y seleccione **Inicio > Actualizar** para volver a cargar los CSV generados.
4. Revise la página `04 Calidad de Datos` y `data/processed/00_resumen_etl.json` antes de distribuir el informe.

El mismo comando genera `outputs/portal_astin.html`. Abra ese archivo en Edge/Chrome para usar el portal o aloje el HTML en un servidor web institucional. El portal incrusta Chart.js y agrega solo datos por programa, mes, motivo, ficha con muestra suficiente y nivel de riesgo. No incluye identificadores, nombres, documentos, instructores ni textos libres por aprendiz. Aun con datos agregados, trate el portal como información institucional: para distribución interna use alojamiento autenticado y no lo publique en una URL pública sin autorización de datos.

El modelo semántico importa CSV locales. Por eso, reemplazar el Excel requiere reprocesar ETL, modelo e informe antes de actualizar el PBIP; la actualización programada de Power BI Service no ejecuta este script ni puede leer un archivo local del equipo. Para actualización programada en Service, ubique Excel/CSV y salidas ETL en SharePoint/OneDrive o almacenamiento accesible por gateway, migre el origen del modelo a esa ubicación y configure credenciales/gateway. Este paso de despliegue no queda habilitado automáticamente por el PBIP.

El parámetro `RutaDatos` del modelo apunta a `data/processed` del equipo donde se generó. Si se mueve el proyecto a otro equipo, vuelva a ejecutar `python .\scripts\02_generar_modelo_tmdl.py` y abra/refresque el PBIP; revise que Power BI Desktop acepte el origen local.

## Publicación y mantenimiento

Abra el PBIP en Power BI Desktop, actualice y revise los datos, inicie sesión en el espacio de trabajo autorizado y use **Publicar**. En el servicio, establezca credenciales; configure gateway para fuentes locales o migre a SharePoint/OneDrive según el procedimiento institucional; luego configure la programación y valide una actualización manual. Aplique RLS si los usuarios no deben ver la población completa.

Al modificar columnas de origen, actualice primero el ETL, luego la especificación de tablas/columnas del generador TMDL y los visuales que las usan. El pipeline ejecuta ETL, modelo, PBIR y portal en ese orden. No publique `data/restricted`, documentos de identidad ni identificadores en claro. Mantenga respaldos del archivo fuente en repositorio institucional con controles de acceso y retención.

## Fuentes y límites

El equipo contiene `C:\Users\capatino\Desktop\Inasistencias\Inasistencias.xls` y el manual `C:\Users\capatino\Desktop\Inasistencias\Manual de identidad corporativa sena 2024.pdf`; el proyecto incluye además `Diseño dashboards.pdf`. No se encontró un catálogo maestro adicional. El tema del informe aplica identidad SENA disponible en los recursos del proyecto. Jornada, modalidad, estado académico oficial, matrícula oficial y centro de costo maestro no están cubiertos de forma suficiente por el origen; la cobertura y los campos inferidos se marcan en el modelo/resumen, sin presentarlos como datos oficiales. La tabla de PII está separada y excluida del PBIP.
