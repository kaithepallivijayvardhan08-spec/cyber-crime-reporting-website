$ErrorActionPreference = 'Stop'
$backend = $PSScriptRoot
$frontend = (Resolve-Path (Join-Path $backend '..\frontend')).Path
$python = Join-Path $backend '.venv\Scripts\python.exe'
$webPorts = @(3000, 5500)

if (-not (Test-Path -LiteralPath $python)) {
    throw "Virtual environment Python was not found at $python."
}

foreach ($port in @(3000, 5000, 5500)) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($listener) {
        throw "Port $port is already in use. Stop the old server on that port, then run this launcher."
    }
}

$staticServers = @()
try {
    $quotedFrontend = [char]34 + $frontend + [char]34
    foreach ($port in $webPorts) {
        $arguments = "-m http.server $port --bind 127.0.0.1 --directory $quotedFrontend"
        $server = Start-Process -FilePath $python -ArgumentList $arguments -PassThru -WindowStyle Hidden
        $staticServers += $server
    }

    Start-Sleep -Seconds 1
    foreach ($server in $staticServers) {
        $server.Refresh()
        if ($server.HasExited) {
            throw "A frontend server did not start. Check whether ports 3000 and 5500 are available."
        }
    }

    Write-Host "CyberSafe user website: http://127.0.0.1:3000" -ForegroundColor Cyan
    Write-Host "Separate staff console: http://127.0.0.1:5500/admin-console.html" -ForegroundColor Cyan
    Write-Host "Backend API:             http://127.0.0.1:5000" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop all three services." -ForegroundColor Yellow

    Push-Location $backend
    try {
        & $python app.py
        if ($LASTEXITCODE -ne 0) {
            throw "Flask exited with code $LASTEXITCODE."
        }
    } finally {
        Pop-Location
    }
} finally {
    foreach ($server in $staticServers) {
        $server.Refresh()
        if (-not $server.HasExited) {
            Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
