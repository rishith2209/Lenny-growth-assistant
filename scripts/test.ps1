# Lenny Growth Assistant — Test Execution Script
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " RUNNING AUTOMATED TEST SUITE (M1)" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Python Unit & Contract Tests
Write-Host "`n[1/2] Running Python Unit and Contract Tests..." -ForegroundColor Yellow
python -m pytest tests/unit tests/contract -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nPython tests failed!" -ForegroundColor Red
    exit 1
}

# 2. TypeScript Compilation Check for Pi Bridge
Write-Host "`n[2/2] Checking Pi Bridge TypeScript Compilation..." -ForegroundColor Yellow
npm run pi:build
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nTypeScript compilation failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n========================================================" -ForegroundColor Green
Write-Host " ALL TESTS PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
