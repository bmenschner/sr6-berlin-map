@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "SR6_PORT=8765"
if defined SR6_PREVIEW_PORT set "SR6_PORT=%SR6_PREVIEW_PORT%"
set "SR6_BASE_URL=http://127.0.0.1:%SR6_PORT%/"
set "SR6_URL=%SR6_BASE_URL%?dev=1"

call :is_ready
if not errorlevel 1 goto ready

set "SR6_WSL_DIR="
for /f "delims=" %%I in ('wsl.exe -d Ubuntu wslpath -u "%CD%" 2^>nul') do set "SR6_WSL_DIR=%%I"

if not defined SR6_WSL_DIR (
    echo Die Ubuntu-WSL-Umgebung konnte nicht gefunden werden.
    echo Bitte pruefe, ob WSL und Ubuntu gestartet werden koennen.
    pause
    exit /b 1
)

wsl.exe -d Ubuntu test -f "%SR6_WSL_DIR%/index.html"
if errorlevel 1 (
    echo Die Datei index.html wurde im Projektordner nicht gefunden.
    pause
    exit /b 1
)

start "Shadowrun Kartenserver - dieses Fenster beendet den Server" /min wsl.exe -d Ubuntu --cd "%SR6_WSL_DIR%" python3 -m http.server %SR6_PORT% --bind 127.0.0.1

for /l %%N in (1,1,10) do (
    call :is_ready
    if not errorlevel 1 goto ready
    timeout /t 1 /nobreak >nul
)

echo Die lokale Vorschau konnte nicht auf Port %SR6_PORT% gestartet werden.
echo Moeglicherweise wird der Port bereits von einem anderen Programm verwendet.
pause
exit /b 1

:ready
if /i not "%SR6_PREVIEW_NO_BROWSER%"=="1" start "" "%SR6_URL%"
echo Shadowrun-Karte: %SR6_URL%
echo Zum Beenden das Fenster "Shadowrun Kartenserver" schliessen.
exit /b 0

:is_ready
powershell.exe -NoProfile -Command "try { $response = Invoke-WebRequest -UseBasicParsing -Uri '%SR6_BASE_URL%data/berlin-2080/manifest.json?preview-check=1' -TimeoutSec 1; $manifest = $response.Content | ConvertFrom-Json; if ($response.StatusCode -eq 200 -and $manifest.files.historicalPeople -and $manifest.dataVersion -ge 6) { exit 0 } } catch {}; exit 1" >nul 2>nul
exit /b %errorlevel%
