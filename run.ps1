param (
    [string]$Process = "d:\Official\BMR_OCR2\data\input\sample.pdf"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "    BMR OCR Engine - Startup Script      " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check if virtual environment exists
$VenvActivate = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
if (-Not (Test-Path $VenvActivate)) {
    Write-Host "Error: Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "Please run 'python -m venv .venv' and install requirements first." -ForegroundColor Yellow
    exit 1
}

# 2. Process Document if requested
if ($Process) {
    Write-Host "`n[1/3] Processing Document: $Process" -ForegroundColor Yellow
    # Run synchronously in current window
    & $ProjectRoot\.venv\Scripts\python.exe main.py --process "$Process"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error occurred during document processing." -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Document Processing Complete!" -ForegroundColor Green
}
else {
    Write-Host "`n[1/3] Skipping document processing (use -Process <path> to run)" -ForegroundColor DarkGray
}

# 3. Start Backend Server
Write-Host "`n[2/3] Starting Backend API Server (New Window)..." -ForegroundColor Yellow
$BackendCmd = "& '$VenvActivate'; python main.py --server"
Start-Process powershell -ArgumentList "-NoExit -Command `" $BackendCmd `"" -WorkingDirectory $ProjectRoot

# 4. Start Frontend Server
Write-Host "`n[3/3] Starting React Frontend Server (New Window)..." -ForegroundColor Yellow
$FrontendDir = Join-Path $ProjectRoot "ui\react-app"
if (Test-Path $FrontendDir) {
    $FrontendCmd = "npm run dev"
    Start-Process powershell -ArgumentList "-NoExit -Command `" $FrontendCmd `"" -WorkingDirectory $FrontendDir
    Write-Host "`nAll services starting! Check the new windows for logs." -ForegroundColor Green
    Write-Host "Frontend should be available at: http://localhost:5173" -ForegroundColor Green
}
else {
    Write-Host "Error: Frontend directory not found at $FrontendDir" -ForegroundColor Red
}
