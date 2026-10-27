param(
    [Parameter(Mandatory = $true)][int]$ProcessId,
    [Parameter(Mandatory = $true)][string]$OutFile,
    [int]$Flags = 2
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class PbiCapture {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint nFlags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
$proc = Get-Process -Id $ProcessId
$hwnd = $proc.MainWindowHandle
if ($hwnd -eq [IntPtr]::Zero) { throw "No main window handle" }
if ([PbiCapture]::IsIconic($hwnd)) {
    [PbiCapture]::ShowWindow($hwnd, 9) | Out-Null
    Start-Sleep -Seconds 2
    [PbiCapture]::ShowWindow($hwnd, 3) | Out-Null
    Start-Sleep -Seconds 2
}
[PbiCapture]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Seconds 2
$r = New-Object PbiCapture+RECT
[PbiCapture]::GetWindowRect($hwnd, [ref]$r) | Out-Null
$w = $r.Right - $r.Left
$h = $r.Bottom - $r.Top
if ($w -lt 200 -or $h -lt 200) { throw "Window too small: ${w}x${h}" }
$bmp = New-Object System.Drawing.Bitmap($w, $h)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [PbiCapture]::PrintWindow($hwnd, $hdc, $Flags)
$g.ReleaseHdc($hdc)
$g.Dispose()
$bmp.Save($OutFile, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
Write-Output ("captured={0} size={1}x{2} printwindow={3} file={4}" -f $hwnd, $w, $h, $ok, $OutFile)
