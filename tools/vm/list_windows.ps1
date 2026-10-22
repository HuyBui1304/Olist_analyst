# Liệt kê cửa sổ hiển thị của Power BI Desktop (tiêu đề, PID) - hỗ trợ gỡ lỗi khi mở project
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public class W {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
  public static List<string> List() { var r = new List<string>(); EnumWindows((h,l)=>{ if(IsWindowVisible(h)){ var s=new StringBuilder(512); GetWindowText(h,s,512); uint p; GetWindowThreadProcessId(h,out p); if(s.Length>0) r.Add(p+"`t"+h+"`t"+s);} return true;}, IntPtr.Zero); return r; }
}
"@
$ids = @(Get-Process PBIDesktop, msedgewebview2 -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
[W]::List() | Where-Object { $ids -contains [int]($_.Split("`t")[0]) }
