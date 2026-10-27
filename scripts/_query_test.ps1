$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$asm = Join-Path $d "tools\adomdclient\lib\net472\Microsoft.AnalysisServices.AdomdClient.dll"
try { Add-Type -Path $asm } catch { }
$cs = 'Data Source=localhost:54135;Initial Catalog=d5fc8850-de1f-4faf-967b-5d344694c21e;'
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection $cs
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandText = 'EVALUATE ROW("Filas", COUNTROWS(FACT_INASISTENCIAS), "Horas", SUM(FACT_INASISTENCIAS[CantidadHoras]))'
$rd = $cmd.ExecuteReader()
Write-Output ("FIELDCOUNT=" + $rd.FieldCount)
for ($i=0; $i -lt $rd.FieldCount; $i++) { Write-Output ("COL " + $i + " = " + $rd.GetName($i)) }
while ($rd.Read()) {
    for ($i=0; $i -lt $rd.FieldCount; $i++) { Write-Output ("VAL " + $rd.GetName($i) + " = " + $rd.GetValue($i)) }
}
$rd.Close()
$conn.Close()
