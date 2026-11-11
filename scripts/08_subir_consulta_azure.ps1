#Requires -Version 5.1
<#
.SYNOPSIS
    Sube la consulta nominal al Blob privado de Azure.

.DESCRIPTION
    Valida que el archivo sea real (no sintético), que no esté dentro de web/ y
    que tenga registros. Crea el contenedor como privado y sube el blob con
    autenticación de Microsoft Entra (--auth-mode login).

    El archivo contiene nombres de aprendices. Nunca se imprime su contenido.
    El contenedor debe permanecer privado; la API lo lee en el servidor.

.PARAMETER StorageAccount
    Nombre de la cuenta de almacenamiento (sin .blob.core.windows.net).

.PARAMETER GenerarSas
    Genera un SAS de solo lectura para configurar BLOB_SAS_URL en la API
    administrada de Static Web Apps. El SAS es un secreto: no lo guarde en Git
    ni lo comparta por canales abiertos.

.EXAMPLE
    .\scripts\08_subir_consulta_azure.ps1 -StorageAccount astinconsulta

.EXAMPLE
    .\scripts\08_subir_consulta_azure.ps1 -StorageAccount astinconsulta -GenerarSas
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-z0-9]{3,24}$')]
    [string]$StorageAccount,

    [string]$Container = 'consulta-privada',
    [string]$Blob = 'consulta_web.json',
    [string]$Path,
    [switch]$GenerarSas,
    [ValidateRange(1, 730)]
    [int]$SasDias = 365,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

if (-not $Path) {
    $Path = Join-Path $root 'data\private\consulta_web.json'
}
$Path = [System.IO.Path]::GetFullPath($Path)

if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
    throw "No se encontró el archivo: $Path. Ejecute primero python scripts\07_exportar_consulta_web.py"
}

$webRoot = [System.IO.Path]::GetFullPath((Join-Path $root 'web'))
if ($Path.StartsWith($webRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'El archivo real no puede estar dentro de web/. Use data\private\consulta_web.json.'
}

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw 'No se encontró Azure CLI (az). Instálelo desde https://aka.ms/installazurecliwindows y vuelva a intentar.'
}

Write-Host 'Validando el archivo privado...' -ForegroundColor Cyan
$dataset = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
if ($null -eq $dataset -or $null -eq $dataset.records) {
    throw 'El archivo no tiene la propiedad records esperada.'
}
if ($dataset.synthetic -eq $true) {
    throw 'El archivo es de demostración (synthetic=true). No lo suba como datos institucionales.'
}
if ($dataset.schemaVersion -ne 1) {
    throw "schemaVersion no soportada: $($dataset.schemaVersion). Se esperaba 1."
}

$records = @($dataset.records)
if ($records.Count -eq 0) {
    throw 'El archivo no contiene registros.'
}

$demoCount = @($records | Where-Object { [string]$_.name -match '^Aprendiz Demo' }).Count
if ($demoCount -gt 0) {
    throw "El archivo contiene $demoCount registros de demostración. Genere la exportación real antes de subir."
}

$dates = @($records | ForEach-Object { [string]$_.date } | Where-Object { $_ } | Sort-Object)
$minDate = if ($dates.Count) { $dates[0] } else { 'sin fecha' }
$maxDate = if ($dates.Count) { $dates[-1] } else { 'sin fecha' }
$hash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
$size = (Get-Item -LiteralPath $Path).Length

Write-Host ("Archivo: {0:N0} bytes · {1:N0} registros · {2} a {3}" -f $size, $records.Count, $minDate, $maxDate)
Write-Host "SHA-256: $hash"

if (-not $Force) {
    Write-Host ''
    Write-Host 'El archivo contiene datos personales y se subirá a un contenedor privado.' -ForegroundColor Yellow
    $answer = Read-Host "Escriba SUBIR para confirmar la carga a $StorageAccount/$Container/$Blob"
    if ($answer -ne 'SUBIR') {
        throw 'Operación cancelada por el usuario.'
    }
}

function Invoke-AzCli {
    param([string[]]$Arguments)
    $output = & az @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw (($output | Out-String).Trim())
    }
    return $output
}

Write-Host 'Comprobando sesión de Azure CLI...' -ForegroundColor Cyan
try {
    Invoke-AzCli @('account', 'show', '--only-show-errors', '--output', 'none') | Out-Null
}
catch {
    Write-Host 'No hay sesión activa. Se abrirá el inicio de sesión de Azure...' -ForegroundColor Yellow
    & az login | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw 'No fue posible iniciar sesión en Azure.'
    }
}

Write-Host 'Creando o verificando el contenedor privado...' -ForegroundColor Cyan
Invoke-AzCli @(
    'storage', 'container', 'create',
    '--account-name', $StorageAccount,
    '--name', $Container,
    '--auth-mode', 'login',
    '--public-access', 'off',
    '--only-show-errors',
    '--output', 'none'
) | Out-Null

Invoke-AzCli @(
    'storage', 'container', 'set-permission',
    '--account-name', $StorageAccount,
    '--name', $Container,
    '--auth-mode', 'login',
    '--public-access', 'off',
    '--only-show-errors',
    '--output', 'none'
) | Out-Null

Write-Host 'Subiendo el blob privado...' -ForegroundColor Cyan
Invoke-AzCli @(
    'storage', 'blob', 'upload',
    '--account-name', $StorageAccount,
    '--container-name', $Container,
    '--name', $Blob,
    '--file', $Path,
    '--auth-mode', 'login',
    '--overwrite',
    '--content-type', 'application/json; charset=utf-8',
    '--content-cache-control', 'no-store, max-age=0',
    '--only-show-errors',
    '--output', 'none'
) | Out-Null

$infoJson = Invoke-AzCli @(
    'storage', 'blob', 'show',
    '--account-name', $StorageAccount,
    '--container-name', $Container,
    '--name', $Blob,
    '--auth-mode', 'login',
    '--query', '{bytes:properties.contentLength,modified:properties.lastModified,type:properties.contentType}',
    '--output', 'json',
    '--only-show-errors'
)
$info = ($infoJson | Out-String) | ConvertFrom-Json

Write-Host ''
Write-Host ("Carga completada: {0:N0} bytes · modificado {1}" -f [int64]$info.bytes, $info.modified) -ForegroundColor Green
Write-Host 'El contenedor es privado; no hay URL pública para el archivo.' -ForegroundColor Green

if ($GenerarSas) {
    Write-Host ''
    Write-Host 'Generando SAS de solo lectura con delegación de usuario...' -ForegroundColor Cyan
    $expiry = (Get-Date).ToUniversalTime().AddDays($SasDias).ToString('yyyy-MM-ddTHH:mmZ')
    $sas = Invoke-AzCli @(
        'storage', 'blob', 'generate-sas',
        '--account-name', $StorageAccount,
        '--container-name', $Container,
        '--name', $Blob,
        '--permissions', 'r',
        '--expiry', $expiry,
        '--auth-mode', 'login',
        '--as-user',
        '--output', 'tsv',
        '--only-show-errors'
    )
    $sasText = (($sas | Out-String).Trim())
    if (-not $sasText) {
        throw 'Azure no devolvió un SAS. Verifique el rol Storage Blob Delegator y vuelva a intentar.'
    }
    $sasUrl = "https://$StorageAccount.blob.core.windows.net/$Container/$Blob`?$sasText"
    Write-Host ''
    Write-Host 'SECRETO: configure este valor en la aplicación como BLOB_SAS_URL.' -ForegroundColor Yellow
    Write-Host 'No lo guarde en Git, ni en web/, ni en capturas de pantalla.' -ForegroundColor Yellow
    Write-Host "Expira: $expiry (UTC)"
    Write-Host $sasUrl
    Write-Host ''
    Write-Host 'Para rotarlo, vuelva a ejecutar este script con -GenerarSas y actualice BLOB_SAS_URL.' -ForegroundColor DarkGray
}
else {
    Write-Host ''
    Write-Host 'Siguiente paso: configure BLOB_SAS_URL (API administrada) o use una Function App propia con identidad administrada.' -ForegroundColor Cyan
    Write-Host 'Consulte docs/azure_static_web_apps.md.' -ForegroundColor DarkGray
}
