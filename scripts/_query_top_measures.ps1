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
$indice = "Top 10 $([char]0xCD)ndice de Riesgo Ficha"
$cmd.CommandText = @"
EVALUATE ROW(
    "TopRiesgoCount", COUNTROWS ( FILTER ( DIM_APRENDIZ, DIM_APRENDIZ[EsTopRiesgo] = 1 ) ),
    "TopFichaHoras", CALCULATE ( [Top 10 Horas No Justificadas Ficha], DIM_FICHA[FichaID] = "3442110" ),
    "TopFichaHorasNoTop", CALCULATE ( [Top 10 Horas No Justificadas Ficha], DIM_FICHA[FichaID] = "3302821" ),
    "TopProgramaHoras", CALCULATE ( [Top 10 Horas No Justificadas Programa], DIM_PROGRAMA[NombrePrograma] = "Dise$([char]0xF1)o y manufactura" ),
    "TopIndice", CALCULATE ( [$indice], DIM_FICHA[FichaID] = "3442110" ),
    "TopAprendices", CALCULATE ( [Top 10 Aprendices Programa], DIM_PROGRAMA[NombrePrograma] = "Dise$([char]0xF1)o y manufactura" )
)
"@
$rd = $cmd.ExecuteReader()
while ($rd.Read()) { for ($i=0; $i -lt $rd.FieldCount; $i++) { Write-Output ($rd.GetName($i) + '=' + [string]$rd.GetValue($i)) } }
$rd.Close()
$conn.Close()
