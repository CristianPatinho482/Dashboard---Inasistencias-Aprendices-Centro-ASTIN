<#
Actualiza los datos, el modelo Power BI, el informe PBIR y el portal HTML desde el Excel sincronizado en OneDrive.
Después, actualice el modelo abierto en Power BI Desktop con Inicio > Actualizar.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pipeline = @(
    '01_etl_modelo_estrella.py',
    '02_generar_modelo_tmdl.py',
    '03_generar_reporte_pbir.py',
    '04_generar_portal_html.py'
)
$sourceFile = Join-Path $env:USERPROFILE 'OneDrive - Servicio Nacional de Aprendizaje\Equipo ASTIN-DESAROLLOS POWER-BI - RAPS ASTIN 2026\Inasistencias.xls'

if (-not (Test-Path -LiteralPath $sourceFile)) {
    throw "No se encontró el archivo fuente: $sourceFile"
}

Push-Location $root
$previousSource = $env:INASISTENCIAS_SOURCE
try {
    $env:INASISTENCIAS_SOURCE = $sourceFile
    foreach ($scriptName in $pipeline) {
        $scriptPath = Join-Path $PSScriptRoot $scriptName
        python $scriptPath
        if ($LASTEXITCODE -ne 0) {
            throw "Falló $scriptName con código $LASTEXITCODE. No actualice el modelo hasta corregir el error."
        }
    }
    Write-Host 'Datos, modelo, reporte y portal regenerados. Portal: outputs\portal_astin.html. En Power BI Desktop, use Inicio > Actualizar.' -ForegroundColor Green
}
finally {
    if ($null -eq $previousSource) {
        Remove-Item Env:\INASISTENCIAS_SOURCE -ErrorAction SilentlyContinue
    }
    else {
        $env:INASISTENCIAS_SOURCE = $previousSource
    }
    Pop-Location
}
