$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$asm = Join-Path $d "tools\adomdclient\lib\net472\Microsoft.AnalysisServices.AdomdClient.dll"
try { Add-Type -Path $asm } catch { }
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection 'Data Source=localhost:54135;Initial Catalog=d5fc8850-de1f-4faf-967b-5d344694c21e;'
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = 'EVALUATE ROW("PctMin", MIN(DIM_FICHA[PctHorasNoJust]), "PctMax", MAX(DIM_FICHA[PctHorasNoJust]), "ScoreMin", MIN(DIM_APRENDIZ[ScoreRiesgo]), "ScoreMax", MAX(DIM_APRENDIZ[ScoreRiesgo]), "HpaMin", MIN(DIM_FICHA[HorasPorAprendiz]), "HpaMax", MAX(DIM_FICHA[HorasPorAprendiz]))'
$rd = $cmd.ExecuteReader()
while ($rd.Read()) { for ($i=0; $i -lt $rd.FieldCount; $i++) { Write-Output ($rd.GetName($i) + '=' + [string]$rd.GetValue($i)) } }
$rd.Close()
$conn.Close()
