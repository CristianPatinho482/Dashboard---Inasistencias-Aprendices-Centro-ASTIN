param(
  [Parameter(Mandatory=$true)][int]$Port,
  [Parameter(Mandatory=$true)][string]$Database
)
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$lib = Join-Path $d "tools\analysisservices\lib\net472"
foreach ($p in @("Microsoft.AnalysisServices.Core.dll", "Microsoft.AnalysisServices.Tabular.Json.dll", "Microsoft.AnalysisServices.Tabular.dll", "Microsoft.AnalysisServices.dll")) {
    [Reflection.Assembly]::LoadFrom((Join-Path $lib $p)) | Out-Null
}
$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$Port")
$db = $server.Databases[$Database]
$col = $db.Model.Tables["DIM_APRENDIZ"].Columns["EsTopRiesgo"]
$col.Expression = 'IF ( RANKX ( ALL ( DIM_APRENDIZ ), DIM_APRENDIZ[ScoreRiesgo] + DIM_APRENDIZ[HorasNoJustificadas] / 1000000, , DESC, Dense ) <= 15, 1, 0 )'
$db.Model.SaveChanges()
Write-Output "expression updated"
$db.Model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Calculate)
$db.Model.SaveChanges()
Write-Output "calculate done"
$server.Disconnect()

