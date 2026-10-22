<#
Điều khiển Power BI Desktop bằng UI Automation (không cần chuột) – dùng từ Mac qua prlctl exec --current-user.

  powershell -File uia.ps1 -Invoke "Cancel"                 # bấm nút theo tên
  powershell -File uia.ps1 -Invoke "Delivery" -Type TabItem # chọn tab trang
  powershell -File uia.ps1 -List -Filter "Delivery"         # liệt kê phần tử có tên chứa chuỗi
#>
param(
    [string]$Invoke,
    [string]$Type,
    [switch]$List,
    [string]$Filter = "",
    [string]$Window = "Olist"
)
Add-Type -AssemblyName UIAutomationClient, UIAutomationTypes
$A = [System.Windows.Automation.AutomationElement]
$pbi = Get-Process PBIDesktop | Where-Object { $_.MainWindowTitle -like "*$Window*" } | Select-Object -First 1
if (-not $pbi) { throw "Không thấy cửa sổ '$Window'" }
$root = $A::FromHandle($pbi.MainWindowHandle)
$all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)

if ($List) {
    foreach ($e in $all) {
        $n = $e.Current.Name
        if ($n -and $n -like "*$Filter*") { "{0}`t{1}`t{2}" -f $e.Current.ControlType.ProgrammaticName, $n.Substring(0, [Math]::Min(80, $n.Length)), $e.Current.BoundingRectangle }
    }
    return
}

if ($Invoke) {
    $match = $all | Where-Object { $_.Current.Name -eq $Invoke -and (-not $Type -or $_.Current.ControlType.ProgrammaticName -eq "ControlType.$Type") } | Select-Object -First 1
    if (-not $match) { throw "Không thấy phần tử '$Invoke'" }
    foreach ($pat in @([System.Windows.Automation.InvokePattern]::Pattern, [System.Windows.Automation.SelectionItemPattern]::Pattern)) {
        $obj = $null
        if ($match.TryGetCurrentPattern($pat, [ref]$obj)) {
            if ($obj -is [System.Windows.Automation.InvokePattern]) { $obj.Invoke() } else { $obj.Select() }
            "OK: $($match.Current.ControlType.ProgrammaticName) '$Invoke'"
            return
        }
    }
    throw "Phần tử '$Invoke' không hỗ trợ Invoke/Select"
}
