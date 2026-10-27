param(
    [string]$Port = "54135",
    [string]$Database = "d5fc8850-de1f-4faf-967b-5d344694c21e",
    [switch]$Refresh
)
$ErrorActionPreference = "Stop"
$d = Split-Path -Parent $PSScriptRoot
$lib = Join-Path $d "tools\analysisservices\lib\net472"
[Reflection.Assembly]::LoadFrom((Join-Path $lib "Microsoft.AnalysisServices.Core.dll")) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $lib "Microsoft.AnalysisServices.Tabular.Json.dll")) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $lib "Microsoft.AnalysisServices.Tabular.dll")) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $lib "Microsoft.AnalysisServices.dll")) | Out-Null

$server = New-Object Microsoft.AnalysisServices.Tabular.Server
$server.Connect("localhost:$Port")
Write-Output ("CONNECTED " + $server.Version)
$db = $server.Databases[$Database]
if ($null -eq $db) {
    Write-Output "DATABASES:"
    foreach ($x in $server.Databases) { Write-Output ("  " + $x.ID + " | " + $x.Name) }
    exit 1
}
Write-Output ("DB=" + $db.ID + " Compatibility=" + $db.CompatibilityLevel + " Tables=" + $db.Model.Tables.Count)
if ($Refresh) {
    Write-Output "REFRESHING FULL MODEL..."
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $db.Model.RequestRefresh([Microsoft.AnalysisServices.Tabular.RefreshType]::Full)
    $db.Model.SaveChanges()
    $sw.Stop()
    Write-Output ("REFRESH DONE in " + [math]::Round($sw.Elapsed.TotalSeconds,1) + "s")
}
$server.Disconnect()
