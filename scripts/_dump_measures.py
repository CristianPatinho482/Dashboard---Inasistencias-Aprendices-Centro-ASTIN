import io, re
p = r"CaracterizacionAprendicesASTIN.SemanticModel\definition\tables\FACT_INASISTENCIAS.tmdl"
s = io.open(p, encoding="utf-8").read()
for m in re.finditer(r"measure '([^']+)' = ```\n(.*?)\n\t\t\t```\n((?:\t\t.*\n)*)", s, re.S):
    name = m.group(1)
    if name in {
        "Horas no justificadas", "% horas no justificadas", "Índice de riesgo promedio de fichas",
        "Aprendices con inasistencias", "Aprendices reincidentes", "Aprendices reincidentes altos",
        "Casos posible deserción", "Aprendices en riesgo alto", "Tasa de reincidencia",
        "Cantidad de retardos", "Registros que requieren revisión", "% registros que requieren revisión",
        "Registros con horas atípicas", "Registros no clasificados", "Cobertura documento",
        "Total horas perdidas", "Total inasistencias", "Fichas con inasistencias",
        "Programas con inasistencias", "Fichas en riesgo alto", "Programas en riesgo alto",
        "Horas promedio por aprendiz", "Inasistencias promedio por aprendiz", "Aprendices en riesgo medio",
        "Aprendices en riesgo bajo", "Aprendices con retardo", "Horas de retardo",
        "Aprendices afectados en fichas de alto riesgo", "Horas no justificadas en fichas de alto riesgo",
        "Ficha crítica principal", "Programa crítico principal", "Máximo índice de riesgo de ficha",
        "% fichas en riesgo alto", "Fichas en riesgo medio", "Fichas muestra insuficiente",
        "Programas en riesgo medio", "Programas muestra insuficiente",
        "Registros origen", "Duplicados removidos", "% duplicados removidos",
        "Registros sin justificación", "Justificaciones únicas", "Cobertura jornada",
        "Cobertura modalidad", "Cobertura estado académico", "Cobertura matrícula",
        "Fichas sin jornada", "Programas sin nivel formativo", "Días de cobertura",
        "Fecha mínima de novedad", "Fecha máxima de novedad",
        "Horas último mes", "Variación % horas mes", "Inasistencias último mes", "Variación % inasistencias mes",
    }:
        print("###", name)
        print(m.group(2))
        print(m.group(3).strip())
        print()
