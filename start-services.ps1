# Start DeerFlow services PowerShell script

Write-Host "=== DeerFlow Service Start Script ==="
Write-Host ""

# Start backend service
Write-Host "Starting backend service..."
Write-Host "Command: cd backend; python -m uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload"
Write-Host ""

# Start new terminal for backend
Start-Process powershell -ArgumentList "-NoExit", "cd backend; python -m uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload"

# Wait 2 seconds for backend to start
Start-Sleep -Seconds 2

# Start frontend service
Write-Host "Starting frontend service..."
Write-Host "Command: cd frontend; pnpm dev"
Write-Host ""

# Start new terminal for frontend
Start-Process powershell -ArgumentList "-NoExit", "cd frontend; pnpm dev"

Write-Host ""
Write-Host "=== Service Start Complete ==="
Write-Host "Backend service: http://localhost:8001"
Write-Host "Frontend service: http://localhost:3000"
Write-Host "API docs: http://localhost:8001/docs"
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
