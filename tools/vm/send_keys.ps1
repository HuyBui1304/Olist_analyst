<#
Đưa một cửa sổ (theo tên UI Automation) lên trước rồi gửi phím. Dùng cho hộp thoại của Power BI.
  powershell -File send_keys.ps1 -Window "Auto recovery" -Keys "{ESC}"
#>
param([Parameter(Mandatory)][string]$Window, [Parameter(Mandatory)][string]$Keys)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes, System.Windows.Forms
Add-Type @"
using System; using System.Runtime.InteropServices;
public class Fg {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern void keybd_event(byte k, byte s, uint f, UIntPtr e);
}
"@
$A = [System.Windows.Automation.AutomationElement]
$cond = New-Object System.Windows.Automation.PropertyCondition($A::NameProperty, $Window)
$w = $A::RootElement.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
if (-not $w) { throw "Không thấy cửa sổ '$Window'" }
$h = [IntPtr]$w.Current.NativeWindowHandle
[Fg]::keybd_event(0x12, 0, 0, [UIntPtr]::Zero); [Fg]::keybd_event(0x12, 0, 2, [UIntPtr]::Zero)
[Fg]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 300
"foreground ok: $([Fg]::GetForegroundWindow() -eq $h)"
[System.Windows.Forms.SendKeys]::SendWait($Keys)
