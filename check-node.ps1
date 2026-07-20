Get-CimInstance Win32_Process -Filter "name='node.exe'" |
  Select-Object ProcessId, CommandLine, ParentProcessId |
  Format-List
Write-Host "--- netstat 8000 ---"
netstat -ano | Select-String ":8000"
