#Requires -Version 5.1
<#
.SYNOPSIS
    Purga data/ del historial Git y fuerza la actualización del remoto.

.DESCRIPTION
    Procedimiento de emergencia para un repositorio que publicó datos
    personales. Requiere:

      1. Que el repositorio ya sea privado.
      2. Que data/ ya no esté versionado en el commit actual.
      3. Un árbol de trabajo limpio (sin cambios pendientes).
      4. git-filter-repo instalado.

    El script crea un respaldo completo (bundle + clon espejo), reescribe todas
    las ramas y etiquetas para eliminar cualquier ruta data/, verifica que no
    queden rastros y hace push --force de todas las referencias.

    Después del push, GitHub puede conservar objetos y vistas en caché. Abra un
    ticket en https://support.github.com/contact para solicitar la purga y
    notifique al contacto de privacidad/seguridad institucional.

.PARAMETER BackupDirectory
    Carpeta donde se guardan el bundle y el clon espejo. Por defecto, una
    carpeta nueva en %TEMP%.

.PARAMETER NoPush
    Reescritura local únicamente. No modifica el remoto.

.PARAMETER Force
    Omite la confirmación interactiva. Úselo solo en un procedimiento aprobado.

.EXAMPLE
    .\scripts\09_limpiar_pii_git.ps1

.EXAMPLE
    .\scripts\09_limpiar_pii_git.ps1 -NoPush
#>
[CmdletBinding()]
param(
    [string]$BackupDirectory,
    [switch]$NoPush,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw 'No se encontró Git.'
}

$top = (& git -C $root rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $top) {
    throw "La carpeta no es un repositorio Git: $root"
}
$top = $top.Trim()
# Git entrega la ruta en UTF-8; Windows PowerShell 5.1 puede decodificarla mal
# cuando la ruta tiene tildes. Si la ruta decodificada no existe, se conserva la
# ruta real del script.
if (-not (Test-Path -LiteralPath $top -PathType Container)) {
    $top = (Resolve-Path -LiteralPath $root).Path
}
$root = $top

$status = @(& git -C $root status --porcelain)
if ($status.Count -gt 0) {
    $status | ForEach-Object { Write-Host "  $_" }
    throw 'El árbol de trabajo tiene cambios pendientes. Confirme o guarde los cambios antes de reescribir el historial.'
}

$trackedData = @(& git -C $root ls-files -- data)
if ($trackedData.Count -gt 0) {
    throw 'data/ todavía está versionado en el commit actual. Ejecute git rm -r --cached data, confirme el cambio y vuelva a intentar.'
}

$remoteUrl = (& git -C $root remote get-url origin 2>$null)
if ($LASTEXITCODE -ne 0 -or -not $remoteUrl) {
    throw 'No se encontró el remoto origin.'
}
$remoteUrl = $remoteUrl.Trim()

# Verificación de visibilidad: la API pública responde 200 con private=false
# para repositorios públicos y 404 para privados o inexistentes.
$visibility = 'desconocida'
if ($remoteUrl -match 'github\.com[/:](?<owner>[^/]+)/(?<repo>[^/]+?)(?:\.git)?$') {
    $apiUrl = "https://api.github.com/repos/$($Matches.owner)/$($Matches.repo)"
    try {
        $repoInfo = Invoke-RestMethod -Uri $apiUrl -Headers @{ 'User-Agent' = 'astin-pii-cleanup' } -TimeoutSec 20
        if ($repoInfo.private -eq $false) {
            throw "El repositorio $($Matches.owner)/$($Matches.repo) sigue siendo público. Cámbielo a privado antes de continuar."
        }
        $visibility = 'privado'
    }
    catch {
        if ($_.Exception.Message -like '*sigue siendo público*') { throw }
        $visibility = 'privado o inaccesible sin autenticación (verifique en GitHub)'
    }
}

Write-Host "Repositorio: $root"
Write-Host "Remoto: $remoteUrl"
Write-Host "Visibilidad estimada: $visibility"
Write-Host ''

if (-not $Force) {
    Write-Host 'ADVERTENCIA: esta operación reescribe el historial y hace push --force.' -ForegroundColor Yellow
    Write-Host 'Los clones y forks existentes conservarán la copia antigua. El dato ya debe tratarse como comprometido.' -ForegroundColor Yellow
    $answer = Read-Host 'Escriba PURGAR para continuar'
    if ($answer -ne 'PURGAR') {
        throw 'Operación cancelada por el usuario.'
    }
}

if (-not $BackupDirectory) {
    $BackupDirectory = Join-Path $env:TEMP ("astin_repo_backup_" + (Get-Date -Format 'yyyyMMdd_HHmmss'))
}
New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
$BackupDirectory = (Resolve-Path -LiteralPath $BackupDirectory).Path

$bundlePath = Join-Path $BackupDirectory 'repo_all_refs.bundle'
$mirrorPath = Join-Path $BackupDirectory 'repo_mirror.git'

Write-Host "Creando respaldo en $BackupDirectory ..." -ForegroundColor Cyan
& git -C $root bundle create $bundlePath --all
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el bundle de respaldo.' }

& git clone --mirror $root $mirrorPath
if ($LASTEXITCODE -ne 0) { throw 'No se pudo crear el clon espejo de respaldo.' }

$dataBackup = Join-Path $BackupDirectory 'data'
if (Test-Path -LiteralPath (Join-Path $root 'data')) {
    Copy-Item -LiteralPath (Join-Path $root 'data') -Destination $dataBackup -Recurse -Force
    Write-Host "Copia de trabajo de data/ respaldada en $dataBackup" -ForegroundColor DarkGray
}

Write-Host 'Verificando git-filter-repo...' -ForegroundColor Cyan
& git filter-repo --version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw @'
git-filter-repo no está disponible. Instálelo con:
    python -m pip install --user git-filter-repo
y agregue la carpeta Scripts de Python al PATH. Luego vuelva a ejecutar este script.
'@
}

Write-Host 'Reescribiendo el historial para eliminar data/ ...' -ForegroundColor Cyan
Push-Location $root
try {
    & git filter-repo --force --invert-paths --path data/
    if ($LASTEXITCODE -ne 0) {
        throw 'git filter-repo falló. El respaldo está intacto; no se hizo push.'
    }
}
finally {
    Pop-Location
}

Write-Host 'Verificando que no queden rutas data/ en el historial...' -ForegroundColor Cyan
$leftover = @(
    & git -C $root log --all --name-only --pretty=format: |
        Where-Object { $_ -match '^data/' } |
        Sort-Object -Unique
)
if ($leftover.Count -gt 0) {
    $leftover | ForEach-Object { Write-Host "  $_" }
    throw 'Todavía hay rutas data/ en el historial. No se hizo push.'
}

$objects = @(
    & git -C $root rev-list --objects --branches --tags |
        Select-String 'DIM_APRENDIZ_PII|Inasistencias\.xls'
)
if ($objects.Count -gt 0) {
    $objects | ForEach-Object { Write-Host "  $_" }
    throw 'Todavía hay objetos con nombres de archivos restringidos en ramas o etiquetas. No se hizo push.'
}

& git -C $root remote add origin $remoteUrl
if ($LASTEXITCODE -ne 0) {
    throw 'No se pudo restaurar el remoto origin.'
}

Write-Host 'Historial local limpio. Rutas data/ eliminadas de todas las ramas y etiquetas.' -ForegroundColor Green

if ($NoPush) {
    Write-Host ''
    Write-Host 'Modo -NoPush: el remoto no se modificó.' -ForegroundColor Yellow
    Write-Host "Para publicar la limpieza: git -C `"$root`" push --force --all origin"
    Write-Host "y luego: git -C `"$root`" push --force --tags origin"
}
else {
    Write-Host 'Enviando todas las ramas reescritas al remoto...' -ForegroundColor Cyan
    & git -C $root push --force --all origin
    if ($LASTEXITCODE -ne 0) {
        throw 'El push de ramas falló. El historial local ya está limpio; repita el push cuando se resuelva la credencial.'
    }

    & git -C $root push --force --tags origin
    if ($LASTEXITCODE -ne 0) {
        throw 'El push de etiquetas falló. Repita git push --force --tags origin.'
    }
    Write-Host 'Remoto actualizado con el historial limpio.' -ForegroundColor Green
}

Write-Host ''
Write-Host 'PASOS OBLIGATORIOS DESPUÉS DEL PUSH' -ForegroundColor Yellow
Write-Host '1. Abra https://support.github.com/contact y solicite purgar vistas en caché y objetos inaccesibles del repositorio.' -ForegroundColor Yellow
Write-Host '2. Revise forks y clones existentes: conservan la historia antigua. Solicite su eliminación o purga.' -ForegroundColor Yellow
Write-Host '3. Notifique al contacto de privacidad/seguridad del SENA y trate los datos como comprometidos.' -ForegroundColor Yellow
Write-Host '4. Rote cualquier secreto que haya estado en el repositorio o en su historial.' -ForegroundColor Yellow
Write-Host "5. Respaldo conservado en: $BackupDirectory" -ForegroundColor DarkGray
