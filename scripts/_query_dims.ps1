$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$asm = Join-Path $d "tools\adomdclient\lib\net472\Microsoft.AnalysisServices.AdomdClient.dll"
try { Add-Type -Path $asm } catch { }
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection 'Data Source=localhost:54135;Initial Catalog=d5fc8850-de1f-4faf-967b-5d344694c21e;'
$conn.Open()
$cmd = $conn.CreateCommand()
$queries = @(
 'EVALUATE SUMMARIZECOLUMNS(DIM_FICHA[NivelRiesgoCorte], "n", COUNTROWS(DIM_FICHA), "mn", MIN(DIM_FICHA[IndiceRiesgoCorte]), "mx", MAX(DIM_FICHA[IndiceRiesgoCorte]), "av", AVERAGE(DIM_FICHA[IndiceRiesgoCorte]))',
 'EVALUATE TOPN(8, SUMMARIZECOLUMNS(DIM_FICHA[FichaID], DIM_FICHA[NivelRiesgoCorte], DIM_FICHA[IndiceRiesgoCorte], DIM_FICHA[Horas], "aps", SUM(DIM_FICHA[Aprendices])), DIM_FICHA[IndiceRiesgoCorte], DESC)',
 'EVALUATE SUMMARIZECOLUMNS(DIM_CALENDARIO[AnioMes], "h", SUM(FACT_INASISTENCIAS[CantidadHoras]), "nj", CALCULATE(SUM(FACT_INASISTENCIAS[CantidadHoras]), FACT_INASISTENCIAS[EsNoJustificada]=1))'
)
foreach ($q in $queries) {
  Write-Output "--- QUERY"
  $cmd.CommandText = $q
  $rd = $cmd.ExecuteReader()
  $cols = @(); for ($i=0; $i -lt $rd.FieldCount; $i++) { $cols += $rd.GetName($i) }
  Write-Output ($cols -join ' | ')
  while ($rd.Read()) {
    $vals = @(); for ($i=0; $i -lt $rd.FieldCount; $i++) { $vals += [string]$rd.GetValue($i) }
    Write-Output ($vals -join ' | ')
  }
  $rd.Close()
}
$conn.Close()
