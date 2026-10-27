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
UNION (
    SELECTCOLUMNS ( SUMMARIZE ( DIM_APRENDIZ, DIM_APRENDIZ[NivelRiesgo], "N", [Aprendices con inasistencias] ), "Campo", "NivelRiesgo", "Valor", DIM_APRENDIZ[NivelRiesgo], "N", [N] ),
    SELECTCOLUMNS ( SUMMARIZE ( DIM_APRENDIZ, DIM_APRENDIZ[EstadoAsistencia], "N", [Aprendices con inasistencias] ), "Campo", "EstadoAsistencia", "Valor", DIM_APRENDIZ[EstadoAsistencia], "N", [N] ),
    SELECTCOLUMNS ( SUMMARIZE ( DIM_APRENDIZ, DIM_APRENDIZ[MotivoAlertaDesercion], "N", [Aprendices con inasistencias] ), "Campo", "MotivoAlerta", "Valor", DIM_APRENDIZ[MotivoAlertaDesercion], "N", [N] ),
    SELECTCOLUMNS ( SUMMARIZE ( FACT_INASISTENCIAS, FACT_INASISTENCIAS[ConfianzaClasificacion], "N", [Total inasistencias] ), "Campo", "Confianza", "Valor", FACT_INASISTENCIAS[ConfianzaClasificacion], "N", [N] ),
    SELECTCOLUMNS ( SUMMARIZE ( FACT_INASISTENCIAS, FACT_INASISTENCIAS[CategoriaJustificacion], "N", [Total inasistencias] ), "Campo", "Categoria", "Valor", FACT_INASISTENCIAS[CategoriaJustificacion], "N", [N] )
)
ORDER BY [Campo], [N] DESC
'@
$rd = $cmd.ExecuteReader()
while ($rd.Read()) { Write-Output ([string]$rd.GetValue(0) + ' | ' + [string]$rd.GetValue(1) + ' | ' + [string]$rd.GetValue(2)) }
$rd.Close()
$conn.Close()
