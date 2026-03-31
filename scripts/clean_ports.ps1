# GI Scribe Safe Port Cleanup
Write-Host "Safe Cleaning GI Scribe ports 3000 and 8000..." -ForegroundColor Cyan
Write-Host "[NOTE: This script will NOT close your browser tabs.]" -ForegroundColor Yellow

# Function to kill process on port
function Stop-PortProcess([int]$port) {
    $process = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($process) {
        $pidToKill = $process.OwningProcess
        Write-Host "[SAFE] Clearing port $port (PID $pidToKill)..."
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
    }
}

Stop-PortProcess 3000
Stop-PortProcess 8000

Write-Host "Safe port cleanup complete." -ForegroundColor Green
exit 0
