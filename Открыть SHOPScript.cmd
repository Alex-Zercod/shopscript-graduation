@echo off
cd /d "%~dp0"
powershell -NoProfile -Command "$exe = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'; if (!(Test-Path $exe)) { $py = Get-Command python.exe -ErrorAction SilentlyContinue; if ($py) { $exe = $py.Source } }; if (!(Test-Path $exe)) { Write-Host 'Python 3.10 or newer is required.'; Read-Host; exit 1 }; & $exe 'start.py'; if ($LASTEXITCODE -ne 0) { Read-Host 'Press Enter to close' }"
