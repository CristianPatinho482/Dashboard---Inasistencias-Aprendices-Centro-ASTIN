param(
  [Parameter(Mandatory=$true)][int]$Port,
  [Parameter(Mandatory=$true)][string]$Database
)
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$asm = Join-Path $d "tools\adomdclient\lib\net472\Microsoft.AnalysisServices.AdomdClient.dll"
try { Add-Type -Path $asm } catch { }
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection "Data Source=localhost:$Port;Initial Catalog=$Database;"
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = @'
EVALUATE ROW(
    "FactRows", COUNTROWS(FACT_INASISTENCIAS),
    "Horas", SUM(FACT_INASISTENCIAS[CantidadHoras]),
    "Aprendices", COUNTROWS(DIM_APRENDIZ),
    "Fichas", COUNTROWS(DIM_FICHA),
    "Programas", COUNTROWS(DIM_PROGRAMA),
    "PctFichaMin", MIN(DIM_FICHA[PctHorasNoJust]),
    "PctFichaMax", MAX(DIM_FICHA[PctHorasNoJust]),
    "HpaFichaMin", MIN(DIM_FICHA[HorasPorAprendiz]),
    "HpaFichaMax", MAX(DIM_FICHA[HorasPorAprendiz]),
    "IpaFichaMin", MIN(DIM_FICHA[InasPorAprendiz]),
    "IpaFichaMax", MAX(DIM_FICHA[InasPorAprendiz]),
    "IndiceFichaMin", MIN(DIM_FICHA[IndiceRiesgoCorte]),
    "IndiceFichaMax", MAX(DIM_FICHA[IndiceRiesgoCorte]),
    "PctProgMin", MIN(DIM_PROGRAMA[PctHorasNoJust]),
    "PctProgMax", MAX(DIM_PROGRAMA[PctHorasNoJust]),
    "ScoreMin", MIN(DIM_APRENDIZ[ScoreRiesgo]),
    "ScoreMax", MAX(DIM_APRENDIZ[ScoreRiesgo]),
    "HorasPorDiaMin", MIN(FACT_INASISTENCIAS[HorasPorDia]),
    "HorasPorDiaMax", MAX(FACT_INASISTENCIAS[HorasPorDia]),
    "Reincidentes", COUNTROWS(FILTER(DIM_APRENDIZ, DIM_APRENDIZ[EsReincidente]=1)),
    "AlertaDesercion", COUNTROWS(FILTER(DIM_APRENDIZ, DIM_APRENDIZ[AlertaDesercion]=1)),
    "RiesgoAlto", COUNTROWS(FILTER(DIM_APRENDIZ, DIM_APRENDIZ[NivelRiesgo]="Alto")),
    "RequiereRevision", COUNTROWS(FILTER(FACT_INASISTENCIAS, FACT_INASISTENCIAS[RequiereRevision]=1))
)
'@
$rd = $cmd.ExecuteReader()
while ($rd.Read()) { for ($i=0; $i -lt $rd.FieldCount; $i++) { Write-Output ($rd.GetName($i) + '=' + [string]$rd.GetValue($i)) } }
$rd.Close()
$conn.Close()
