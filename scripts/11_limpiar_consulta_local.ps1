#Requires -Version 5.1
<#
.SYNOPSIS
    Elimina los archivos nominales generados en el equipo local.

.DESCRIPTION
    Borra data/private/consulta_web.json y outputs/consulta_interna.html, que
    contienen nombres de aprendices. No borra el Blob privado de Azure ni los
    respaldos. Úselo después de subir el archivo a Azure o al terminar una
    revisión local.

.EXAMPLE
    .\scripts\11_limpiar_consulta_local.ps1

.EXAMPLE
    .\scripts\11_limpiar_consulta_local.ps1 -Force
#>
[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$targets = @(
    (Join-Path $root 'data\private\consulta_web.json'),
    (Join-Path $root 'outputs\consulta_interna.html')
)

$existing = @($targets | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf })
if ($existing.Count -eq 0) {
    Write-Host 'No hay archivos nominales locales para eliminar.' -ForegroundColor DarkGray
    exit 0
}

Write-Host 'Se eliminarán los siguientes archivos con datos personales:' -ForegroundColor Yellow
$existing | ForEach-Object { Write-Host "  $_" }
Write-Host 'Esta acción no borra el Blob privado de Azure ni los respaldos.' -ForegroundColor DarkGray

if (-not $Force) {
    $answer = Read-Host 'Escriba BORRAR para continuar'
    if ($answer -ne 'BORRAR') {
        throw 'Operación cancelada por el usuario.'
    }
}

foreach ($file in $existing) {
    Remove-Item -LiteralPath $file -Force
    Write-Host "Eliminado: $file" -ForegroundColor Green
}

$webRoot = Join-Path $root 'web'
$webReal = @(
    Get-ChildItem -LiteralPath $webRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            ($_.DirectoryName -like '*\web\data*' -and $_.Name -notlike 'demo_*') -or
            ($_.Extension -in @('.csv', '.xlsx', '.xls'))
        }
)
if ($webReal.Count -gt 0) {
    Write-Host ''
    Write-Host 'ADVERTENCIA: hay archivos de datos que no son de demostración dentro de web/:' -ForegroundColor Red
    $webReal | ForEach-Object { Write-Host "  $($_.FullName)" -ForegroundColor Red }
    Write-Host 'Revise que no contengan datos personales antes de publicar.' -ForegroundColor Red
}
else {
    Write-Host 'web/ no contiene archivos de datos distintos de la demostración.' -ForegroundColor Green
}
