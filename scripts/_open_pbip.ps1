param(
  [Parameter(Mandatory=$true)][int]$ProcessId,
  [Parameter(Mandatory=$true)][string]$Path
)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Text;
using System.Runtime.InteropServices;
public class NativeWin {
  public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lParam);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint pid);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int cmd);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern int GetClassName(IntPtr hWnd, StringBuilder s, int n);
}
'@

function Get-Windows([int]$pidTarget) {
  $result = New-Object System.Collections.Generic.List[object]
  $cb = [NativeWin+EnumWindowsProc]{
    param($h, $l)
    $sb = New-Object System.Text.StringBuilder 512
    [void][NativeWin]::GetWindowText($h, $sb, $sb.Capacity)
    $p = 0
    [void][NativeWin]::GetWindowThreadProcessId($h, [ref]$p)
    if ($p -eq $pidTarget -and $sb.Length -gt 0) {
      $cn = New-Object System.Text.StringBuilder 256
      [void][NativeWin]::GetClassName($h, $cn, $cn.Capacity)
      $result.Add([pscustomobject]@{ Handle = $h; Title = $sb.ToString(); Class = $cn.ToString(); Visible = [NativeWin]::IsWindowVisible($h) })
    }
    return $true
  }
  [void][NativeWin]::EnumWindows($cb, [IntPtr]::Zero)
  return $result
}

$wins = Get-Windows $ProcessId
$main = $wins | Where-Object { $_.Class -like 'WindowsForms10*' } | Select-Object -First 1
if (-not $main) { Write-Error "No main window for PID $ProcessId"; exit 1 }
[void][NativeWin]::ShowWindow($main.Handle, 9)
[void][NativeWin]::SetForegroundWindow($main.Handle)
Start-Sleep -Milliseconds 800
$root = [System.Windows.Automation.AutomationElement]::FromHandle($main.Handle)

function Select-Tab($root, $name) {
  $cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, $name)
  $tab = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
  if ($tab) {
    $tab.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select()
    Start-Sleep -Milliseconds 900
    return $true
  }
  return $false
}

[void](Select-Tab $root 'Archivo')
[void](Select-Tab $root 'Abrir')
Start-Sleep -Seconds 2

$wins = Get-Windows $ProcessId
$dlgInfo = $wins | Where-Object { $_.Class -eq '#32770' -and $_.Title -eq 'Abrir' } | Select-Object -First 1
if (-not $dlgInfo) { Write-Error 'Open dialog not found'; exit 2 }
$dlg = [System.Windows.Automation.AutomationElement]::FromHandle($dlgInfo.Handle)
$editCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
$edit = $dlg.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $editCond)
if (-not $edit) { Write-Error 'Filename edit not found'; exit 3 }
$edit.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue($Path)
Start-Sleep -Milliseconds 500
$btnCond = New-Object System.Windows.Automation.AndCondition(
  (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Button)),
  (New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::NameProperty, 'Abrir'))
)
$btn = $dlg.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $btnCond)
if (-not $btn) { Write-Error 'Open button not found'; exit 4 }
$btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
Write-Output "Open requested: $Path"
