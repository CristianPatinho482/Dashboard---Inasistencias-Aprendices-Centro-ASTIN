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
EVALUATE
TOPN (
    15,
    SUMMARIZE ( DIM_PROGRAMA, DIM_PROGRAMA[NombrePrograma], "Horas", [Horas no justificadas], "Aprendices", [Aprendices con inasistencias] ),
    [Horas], DESC
)
'@
$rd = $cmd.ExecuteReader()
while ($rd.Read()) { $vals = @(); for ($i=0; $i -lt $rd.FieldCount; $i++) { $vals += ($rd.GetName($i) + '=' + [string]$rd.GetValue($i)) }; Write-Output ($vals -join ' | ') }
$rd.Close()
$conn.Close()
