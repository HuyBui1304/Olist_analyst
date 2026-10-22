# Đưa cửa sổ Power BI có tiêu đề chứa -Title lên trước (phóng to), thu nhỏ các cửa sổ Power BI khác.
# Dùng khi chụp màn hình máy ảo từ Mac (prlctl capture).
param([string]$Title = "Olist")
Add-Type @"
using System; using System.Runtime.InteropServices;
public class F {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
}
"@
$all = Get-Process PBIDesktop | Where-Object { $_.MainWindowHandle -ne 0 }
$p = $all | Where-Object { $_.MainWindowTitle -like "*$Title*" } | Select-Object -First 1
if (-not $p) { throw "Không thấy cửa sổ '$Title'" }
$all | Where-Object { $_.Id -ne $p.Id } | ForEach-Object { [F]::ShowWindow($_.MainWindowHandle, 6) | Out-Null }
[F]::ShowWindow($p.MainWindowHandle, 9) | Out-Null
[F]::ShowWindow($p.MainWindowHandle, 3) | Out-Null
[F]::BringWindowToTop($p.MainWindowHandle) | Out-Null
[F]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
"focused $($p.Id): $($p.MainWindowTitle)"
