<#
  serve-galleyquest.ps1
  Serves GalleyQuest as a static site on http://localhost:8000/.
  Run by the "GalleyQuest Server" scheduled task, or manually:
      powershell -ExecutionPolicy Bypass -File .\scripts\serve-galleyquest.ps1
  Blocks for the life of the server and appends output to scripts\serve.log.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot          # repo root (this script lives in scripts\)
Set-Location $root
$log = Join-Path $PSScriptRoot 'serve.log'

# Prefer the Windows 'py' launcher; fall back to 'python' on PATH.
$py = 'python'
if (Get-Command py -ErrorAction SilentlyContinue) { $py = 'py' }

"[$(Get-Date -Format s)] GalleyQuest serving http://localhost:8000/  root=$root  via=$py" |
    Out-File -FilePath $log -Append -Encoding utf8

# Blocks here until the server exits; the task's restart-on-failure relaunches it if it dies.
& $py -m http.server 8000 *>> $log
