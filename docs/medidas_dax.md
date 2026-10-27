# Catálogo de medidas DAX

Las medidas viven en `FACT_INASISTENCIAS.tmdl` y usan contexto de filtro de las dimensiones relacionadas. Formatos numéricos y carpetas están declarados junto con cada medida. La lista completa y sus expresiones ejecutables se mantienen en ese archivo TMDL.

## 00 KPIs

`Total inasistencias` cuenta las filas del hecho; `Total horas perdidas` suma `CantidadHoras`; `Aprendices con inasistencias`, `Fichas con inasistencias` y `Programas con inasistencias` cuentan claves distintas dentro del filtro actual. `Fichas en riesgo alto`, `Programas en riesgo alto` y `Casos posible deserción` cuentan las entidades que tienen al menos un registro relacionado con la respectiva bandera de corte. Los porcentajes de horas se calculan sobre horas, no sobre número de registros.

Las medidas de calidad contabilizan duplicados removidos desde el resumen ETL, filas sin texto de justificación, filas no clasificadas, registros que requieren revisión, outliers, cobertura y fechas extremas. Los conteos de corte del resumen no reaccionan a filtros del informe; las medidas calculadas desde el hecho sí.

## 01 Inasistencias

`Horas justificadas`, `Horas no justificadas` y `Horas sin información` aplican la bandera de categoría y suman horas. Las medidas equivalentes de cantidad de registros cuentan novedades. `Participación por categoría` expresa la distribución con el contexto actual. Retardos y ausencias tienen medidas separadas; la clasificación no debe confundirse con el registro administrativo de una falta.

## 02 Riesgo

Medidas de índice promedio, fichas/programas de riesgo alto, aprendices reincidentes y alertas de deserción agregan las banderas y puntuaciones generadas por ETL. La clasificación de ficha/programa se evalúa en el corte de procesamiento y no es una predicción en tiempo real. Revise umbrales y tamaño muestral en `00_resumen_etl.json`.

## 03 Aprendices

Conteos y participaciones de aprendices con inasistencias, reincidencia, reincidencia alta y alerta de deserción operan con `DISTINCTCOUNT` sobre `AprendizID` para evitar duplicar aprendices por tener múltiples novedades. Los detalles visibles son seudonimizados.

## 04 Tendencias

La variación mensual compara horas con el mes previo en `DIM_CALENDARIO`; el promedio móvil considera tres meses. La serie usa `Fecha Inicio`. Meses parciales y cambios de universo pueden afectar comparaciones; interprete las variaciones con los filtros y el corte visibles.

## Uso responsable

Las medidas de riesgo y deserción solo priorizan validación humana. Los porcentajes por registro y por hora responden preguntas distintas. Los rankings deben considerar el tamaño de ficha/programa y la cobertura disponible. No usar medidas de asistencia como sustituto de estado de matrícula oficial.
