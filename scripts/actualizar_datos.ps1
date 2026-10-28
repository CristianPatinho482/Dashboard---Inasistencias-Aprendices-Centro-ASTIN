<#
Actualiza los datos, el modelo Power BI, el informe PBIR y el portal HTML desde el Excel sincronizado en OneDrive.
Después, actualice el modelo abierto en Power BI Desktop con Inicio > Actualizar.
#>
param(
    [switch]$PublicarPortal,
    [switch]$CopiarSalidasSharePoint
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$pipeline = @(
    '01_etl_modelo_estrella.py',
    '02_generar_modelo_tmdl.py',
    '03_generar_reporte_pbir.py',
    '04_generar_portal_html.py',
    '05_generar_consulta_interna.py'
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
    if ($CopiarSalidasSharePoint) {
        $configPath = Join-Path $root 'config\sharepoint.json'
        if (-not (Test-Path -LiteralPath $configPath)) {
            throw 'No existe config\sharepoint.json. Copie el ejemplo y configure la carpeta de sincronización de SharePoint.'
        }
        $spConfig = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        if ([string]::IsNullOrWhiteSpace($spConfig.local_sync_folder)) {
            throw 'Configure local_sync_folder en config\sharepoint.json como carpeta de documentos de SharePoint sincronizada en este equipo.'
        }
        if (-not (Test-Path -LiteralPath $spConfig.local_sync_folder -PathType Container)) {
            throw "No existe la carpeta sincronizada de SharePoint: $($spConfig.local_sync_folder)"
        }
        python (Join-Path $PSScriptRoot '06_preparar_salidas_sharepoint.py') --source (Join-Path $root 'data\processed') --destination $spConfig.local_sync_folder
        if ($LASTEXITCODE -ne 0) {
            throw 'Falló la preparación de salidas para SharePoint; no se copiaron datos restringidos.'
        }
        Write-Host 'Salidas ETL preparadas y copiadas a SharePoint. No se incluyó DIM_APRENDIZ_PII.csv; valores de identificación directa en DIM_APRENDIZ fueron vaciados. Espere a que OneDrive termine la sincronización antes de refrescar Power BI Service.' -ForegroundColor Green
    }
    if ($PublicarPortal) {
        git -C $root diff --quiet HEAD -- index.html
        if ($LASTEXITCODE -eq 1) {
            git -C $root commit --only -m 'Actualiza portal de inasistencias' -- index.html
            if ($LASTEXITCODE -ne 0) {
                throw 'No se pudo crear el commit del portal. Revise identidad Git, cambios pendientes y estado de la rama.'
            }
            git -C $root push origin main
            if ($LASTEXITCODE -ne 0) {
                throw 'El portal se generó, pero GitHub rechazó el push. Revise conexión, credenciales y sincronización de main.'
            }
            Write-Host 'Portal actualizado y enviado a GitHub Pages (solo index.html).' -ForegroundColor Green
        }
        elseif ($LASTEXITCODE -ne 0) {
            throw 'No se pudo comparar index.html con Git. Verifique que el proyecto tenga un repositorio Git válido.'
        }
        else {
            Write-Host 'El portal no cambió; no se creó un commit ni se envió a GitHub.' -ForegroundColor DarkGray
        }
    }
    Write-Host 'Datos, modelo, reporte y portal regenerados desde OneDrive. Portal: outputs\portal_astin.html; GitHub Pages: index.html. En Power BI Desktop, use Inicio > Actualizar.' -ForegroundColor Green
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
