<#
Registra una tarea del usuario actual que revisa OneDrive cada 6 horas.
Requiere iniciar sesión en Windows para que OneDrive y GitHub Credential Manager estén disponibles.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$updater = Join-Path $PSScriptRoot 'actualizar_datos.ps1'
$powershell = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$taskName = 'ASTIN - Actualizar inasistencias y publicar portal'
$user = "$env:USERDOMAIN\$env:USERNAME"

$action = New-ScheduledTaskAction `
    -Execute $powershell `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$updater`" -PublicarPortal -CopiarSalidasSharePoint -SoloSiFuenteNueva" `
    -WorkingDirectory $root

$atLogOn = New-ScheduledTaskTrigger -AtLogOn -User $user
$repeat = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(2) `
    -RepetitionInterval (New-TimeSpan -Hours 6) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger @($atLogOn, $repeat) `
    -Principal $principal `
    -Settings $settings `
    -Description 'Detecta un Excel nuevo en OneDrive, actualiza los artefactos y publica el portal agregado en GitHub Pages.' `
    -Force | Out-Null

Write-Host "Tarea registrada: $taskName" -ForegroundColor Green
Write-Host 'La tarea se ejecuta al iniciar sesión y cada 6 horas. Solo procesa el Excel si su contenido cambió.'
Write-Host "Registro local: $(Join-Path $env:LOCALAPPDATA 'InasistenciasASTIN\logs')"
