<#
Kết nối vào engine Analysis Services cục bộ của Power BI Desktop đang mở.

  # Làm mới toàn bộ dữ liệu của model
  powershell -File pbi_local.ps1 -Refresh
  # Chạy truy vấn DAX, ghi kết quả TSV (UTF-8)
  powershell -File pbi_local.ps1 -QueryFile q.dax -Out result.tsv

-Title: một phần tiêu đề cửa sổ Power BI để chọn đúng phiên bản khi mở nhiều file (mặc định "Olist").
#>
param(
    [string]$Query,
    [string]$QueryFile,
    [string]$Out,
    [switch]$Refresh,
    [string]$Title = "Olist"
)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName "Microsoft.AnalysisServices.AdomdClient, Version=15.0.0.0, Culture=neutral, PublicKeyToken=89845dcd8080cc91"

function Get-PbiPort {
    $pbi = Get-Process PBIDesktop -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*$Title*" } | Select-Object -First 1
    if (-not $pbi) { throw "Không thấy cửa sổ Power BI có tiêu đề chứa '$Title'" }
    $engine = Get-CimInstance Win32_Process -Filter "Name='msmdsrv.exe'" | Where-Object { $_.ParentProcessId -eq $pbi.Id } | Select-Object -First 1
    if (-not $engine) { throw "Power BI (PID $($pbi.Id)) chưa khởi động engine msmdsrv" }
    $conn = Get-NetTCPConnection -State Listen -OwningProcess $engine.ProcessId | Where-Object { $_.LocalAddress -in @("127.0.0.1", "::1", "0.0.0.0", "::") } | Select-Object -First 1
    return $conn.LocalPort
}

$port = Get-PbiPort
# Tắt nén: ADOMD sẽ cần thư viện nén native x64, không nạp được trong PowerShell ARM64
$conn = New-Object Microsoft.AnalysisServices.AdomdClient.AdomdConnection("Data Source=localhost:$port;Transport Compression=None")
$conn.Open()
$cmd = $conn.CreateCommand()
$cmd.CommandTimeout = 900

$cmd.CommandText = "SELECT [CATALOG_NAME] FROM `$SYSTEM.DBSCHEMA_CATALOGS"
$r = $cmd.ExecuteReader(); $null = $r.Read(); $db = $r.GetString(0); $r.Close()

if ($Refresh) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    $cmd.CommandText = '{"refresh":{"type":"full","objects":[{"database":"' + $db + '"}]}}'
    $null = $cmd.ExecuteNonQuery()
    "Refresh xong sau $([math]::Round($sw.Elapsed.TotalSeconds,1)) giây (port $port)"
}

if ($QueryFile) { $Query = [IO.File]::ReadAllText($QueryFile, [Text.Encoding]::UTF8) }
if ($Query) {
    $cmd.CommandText = $Query
    $r = $cmd.ExecuteReader()
    $sb = New-Object Text.StringBuilder
    do {
        $cols = @(0..($r.FieldCount - 1) | ForEach-Object { $r.GetName($_) })
        $null = $sb.AppendLine(($cols -join "`t"))
        while ($r.Read()) {
            $vals = @(0..($r.FieldCount - 1) | ForEach-Object {
                $v = $r.GetValue($_)
                if ($v -is [double] -or $v -is [decimal]) { $v.ToString([Globalization.CultureInfo]::InvariantCulture) } else { "$v" }
            })
            $null = $sb.AppendLine(($vals -join "`t"))
        }
        $null = $sb.AppendLine("")
    } while ($r.NextResult())
    $r.Close()
    if ($Out) { [IO.File]::WriteAllText($Out, $sb.ToString(), (New-Object Text.UTF8Encoding($false))) } else { $sb.ToString() }
}
$conn.Close()
