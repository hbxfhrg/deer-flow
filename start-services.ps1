# 启动DeerFlow服务的PowerShell脚本

Write-Host "=== DeerFlow 服务启动脚本 ==="
Write-Host ""

# 启动后端服务
Write-Host "正在启动后端服务..."
Write-Host "命令: cd backend; python -m uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload"
Write-Host ""

# 启动新终端运行后端
Start-Process powershell -ArgumentList "-NoExit", "cd backend; python -m uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload"

# 等待2秒让后端服务开始启动
Start-Sleep -Seconds 2

# 启动前端服务
Write-Host "正在启动前端服务..."
Write-Host "命令: cd frontend; pnpm dev"
Write-Host ""

# 启动新终端运行前端
Start-Process powershell -ArgumentList "-NoExit", "cd frontend; pnpm dev"

Write-Host ""
Write-Host "=== 服务启动完成 ==="
Write-Host "后端服务地址: http://localhost:8001"
Write-Host "前端服务地址: http://localhost:3000"
Write-Host "API文档地址: http://localhost:8001/docs"
Write-Host ""
Write-Host "按任意键退出..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
