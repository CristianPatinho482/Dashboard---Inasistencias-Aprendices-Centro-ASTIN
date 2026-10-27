$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$asm = Join-Path $d "tools\adomdclient\lib\net472\Microsoft.AnalysisServices.AdomdClient.dll"
try { Add-Type -Path $asm } catch { }
$cs = 'Data Source=localhost:54135;Initial Catalog=d5fc8850-de1f-4faf-967b-5d344694c21e;'
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection $cs
$conn.Open()
$cmd = $conn.CreateCommand()
$queries = @{
  'Horas' = 'EVALUATE ROW("v", SUM(FACT_INASISTENCIAS[CantidadHoras]))'
  'Inasistencias' = 'EVALUATE ROW("v", COUNTROWS(FACT_INASISTENCIAS))'
  'Aprendices' = 'EVALUATE ROW("v", DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]))'
  'Fichas' = 'EVALUATE ROW("v", DISTINCTCOUNT(FACT_INASISTENCIAS[FichaID]))'
  'Programas' = 'EVALUATE ROW("v", DISTINCTCOUNT(FACT_INASISTENCIAS[ProgramaID]))'
  'PctNoJustHoras' = 'EVALUATE ROW("v", DIVIDE(CALCULATE(SUM(FACT_INASISTENCIAS[CantidadHoras]),FACT_INASISTENCIAS[EsNoJustificada]=1),SUM(FACT_INASISTENCIAS[CantidadHoras])))'
  'Reincidentes' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),FACT_INASISTENCIAS[EsReincidenteAprendiz]=1))'
  'ReincidentesAltos' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),FACT_INASISTENCIAS[EsReincidenteAltoAprendiz]=1))'
  'Desercion' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),FACT_INASISTENCIAS[EsAlertaDesercionAprendiz]=1))'
  'RiesgoAltoAprendiz' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),FACT_INASISTENCIAS[NivelRiesgoAprendiz]="Alto"))'
  'RiesgoMedioAprendiz' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),FACT_INASISTENCIAS[NivelRiesgoAprendiz]="Medio"))'
  'RiesgoBajoAprendiz' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),FACT_INASISTENCIAS[NivelRiesgoAprendiz]="Bajo"))'
  'FichasAlto' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_FICHA),DIM_FICHA[NivelRiesgoCorte]="Alto"))'
  'FichasMedio' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_FICHA),DIM_FICHA[NivelRiesgoCorte]="Medio"))'
  'FichasBajo' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_FICHA),DIM_FICHA[NivelRiesgoCorte]="Bajo"))'
  'FichasBajaMuestra' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_FICHA),DIM_FICHA[NivelRiesgoCorte]="Muestra baja"))'
  'ProgAlto' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_PROGRAMA),DIM_PROGRAMA[NivelRiesgoCorte]="Alto"))'
  'ProgMedio' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_PROGRAMA),DIM_PROGRAMA[NivelRiesgoCorte]="Medio"))'
  'ProgBajo' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_PROGRAMA),DIM_PROGRAMA[NivelRiesgoCorte]="Bajo"))'
  'ProgBajaMuestra' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(DIM_PROGRAMA),DIM_PROGRAMA[NivelRiesgoCorte]="Muestra baja"))'
  'IndicePromFichas' = 'EVALUATE ROW("v", AVERAGE(DIM_FICHA[IndiceRiesgoCorte]))'
  'HorasNoJustFichasAlto' = 'EVALUATE ROW("v", CALCULATE(SUM(FACT_INASISTENCIAS[CantidadHoras]),DIM_FICHA[NivelRiesgoCorte]="Alto",FACT_INASISTENCIAS[EsNoJustificada]=1))'
  'AprendicesFichasAlto' = 'EVALUATE ROW("v", CALCULATE(DISTINCTCOUNT(FACT_INASISTENCIAS[AprendizID]),DIM_FICHA[NivelRiesgoCorte]="Alto"))'
  'HorasUltimoMes' = 'EVALUATE ROW("v", CALCULATE(SUM(FACT_INASISTENCIAS[CantidadHoras]),DIM_CALENDARIO[AnioMes]=MAX(DIM_CALENDARIO[AnioMes])))'
  'HorasMesAnterior' = 'EVALUATE ROW("v", CALCULATE(SUM(FACT_INASISTENCIAS[CantidadHoras]),DIM_CALENDARIO[AnioMes]=FORMAT(EDATE(MAX(DIM_CALENDARIO[Fecha]),-1),"YYYY-MM")))'
  'Retardos' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(FACT_INASISTENCIAS),FACT_INASISTENCIAS[EsRetardo]=1))'
  'HorasRetardo' = 'EVALUATE ROW("v", CALCULATE(SUM(FACT_INASISTENCIAS[CantidadHoras]),FACT_INASISTENCIAS[EsRetardo]=1))'
  'RequiereRevision' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(FACT_INASISTENCIAS),FACT_INASISTENCIAS[RequiereRevision]=1))'
  'Outliers' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(FACT_INASISTENCIAS),FACT_INASISTENCIAS[EsOutlierHoras]=1))'
  'SinJust' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(FACT_INASISTENCIAS),FACT_INASISTENCIAS[EsSinInformacion]=1))'
  'Justificadas' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(FACT_INASISTENCIAS),FACT_INASISTENCIAS[EsJustificada]=1))'
  'NoJustificadas' = 'EVALUATE ROW("v", CALCULATE(COUNTROWS(FACT_INASISTENCIAS),FACT_INASISTENCIAS[EsNoJustificada]=1))'
}
foreach ($k in ($queries.Keys | Sort-Object)) {
  $cmd.CommandText = $queries[$k]
  try {
    $rd = $cmd.ExecuteReader()
    $v = $null
    while ($rd.Read()) { $v = $rd.GetValue(0) }
    $rd.Close()
    Write-Output ("{0}={1}" -f $k, $v)
  } catch {
    Write-Output ("{0}=ERROR: {1}" -f $k, $_.Exception.Message)
  }
}
$conn.Close()
