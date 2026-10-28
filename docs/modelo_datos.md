# Modelo de datos

## Diseño dimensional

El modelo usa `FACT_INASISTENCIAS` como tabla de hechos con una fila por registro de novedad depurado. Las claves de aprendiz, ficha, programa y fecha conectan el hecho con dimensiones de consulta mediante relaciones uno a muchos y filtro de dimensión a hecho. `DIM_FICHA` se vincula también a `DIM_PROGRAMA`, de modo que los filtros de programa alcanzan las fichas y el hecho.

`DIM_CALENDARIO` cubre desde el primer día del año de la primera novedad hasta el último día del año que contiene la fecha de corte observada. La fecha analítica de la novedad es `Fecha Inicio`; `Fecha Fin` queda disponible para detalle y duración del intervalo.

## Fuentes, claves y privacidad

El proceso lee `C:\Users\capatino\OneDrive - Servicio Nacional de Aprendizaje\Equipo ASTIN-DESAROLLOS POWER-BI - RAPS ASTIN 2026\Inasistencias.xls`, hoja `Sheet1`, y crea cinco CSV en `data/processed`. Se puede cambiar la ruta mediante la variable de entorno `INASISTENCIAS_SOURCE`. El archivo Excel es un extracto transaccional, no una fuente maestra para estado académico o matrícula. `DIM_APRENDIZ` contiene una clave seudonimizada y agregados. Nombres y documentos en claro se mantienen aparte en `data/restricted/DIM_APRENDIZ_PII.csv` y nunca se cargan al modelo.

La clave de aprendiz es un hash estable derivado de la identificación disponible; la clave de novedad es hash de los atributos normalizados del evento. Una identificación ausente puede producir una clave heurística basada en datos de contexto y no equivale a una identidad oficial. Programa y centro de costo se normalizan/derivan de los campos disponibles. El resumen ETL señala las inferencias y métricas de cobertura.

## Reglas ETL

- Se invalidan filas con fecha inicial/final inválida o rango invertido.
- Se eliminan duplicados exactos tras normalizar texto, fechas y horas.
- Las horas vacías o no numéricas se convierten a cero; revisar en calidad cuando corresponda.
- La categoría de justificación usa reglas explícitas con prioridad para negaciones, salud/familia y permisos. Texto ambiguo se conserva como `Sin información` y se marca para revisión.
- Los casos de deserción son alertas textuales/operativas, no diagnóstico.
- Los outliers de horas y el índice de riesgo son señales para revisión humana.

## Riesgo

Las fichas/programas elegibles para comparación tienen al menos cinco aprendices y cien horas. El índice compuesto pondera percentiles de intensidad de horas por aprendiz (40%), frecuencia de novedades por aprendiz (25%), porcentaje de horas no justificadas (20%) y volumen de horas (15%). Bajo: menor a 45; medio: 45–69,9; alto: 70 o superior. Son umbrales relativos al conjunto observado. Para aprendices, se aplica 70% a faltas no justificadas (con tope de 20) y 30% a horas (tope de 100), con los mismos cortes. No debe interpretarse como probabilidad de retiro.

La alerta de posible deserción resulta de texto explícito relacionado con retiro/deserción o un patrón reciente definido por la regla ETL. Úsese como cola de acompañamiento y validación, no para sancionar o concluir una deserción.

## Calidad y límites conocidos

El extracto no contiene suficiente información oficial para caracterizar jornada, modalidad, estado académico ni total de matrícula. El centro de costo es inferido. Estas dimensiones no deben comunicarse como cobertura institucional confirmada. La clasificación del motivo tiene una categoría `Sin información` y un indicador `RequiereRevision`; una muestra de textos debe ser auditada por el equipo académico antes de decisiones.

El reporte PBIR requiere Power BI Desktop compatible con proyectos PBIP/PBIR y TMDL. Para Service, las fuentes locales necesitan gateway y credenciales, o deben migrarse a SharePoint/OneDrive o almacenamiento accesible al servicio. El refresco del servicio no ejecuta el ETL Python del equipo.
