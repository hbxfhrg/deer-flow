# DeerFlow 服务重启脚本

Write-Host "=== 清理旧进程 ===" -ForegroundColor Yellow

# 杀掉占用 3000, 3001, 3002 端口的 Node 进程
$nodePorts = @(3000, 3001, 3002)
foreach ($port in $nodePorts) {
    $pids = netstat -ano | Select-String ":$port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Sort-Object -Unique
    foreach ($procId in $pids) {
        if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
            Write-Host "  停止 Node 进程 ID: $procId (端口: $port)" -ForegroundColor Gray
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

# 杀掉占用 8001 端口的 Python/uvicorn 进程
$backendPorts = @(8001, 8000)
foreach ($port in $backendPorts) {
    $pids = netstat -ano | Select-String ":$port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Sort-Object -Unique
    foreach ($procId in $pids) {
        if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
            Write-Host "  停止 Python 进程 ID: $procId (端口: $port)" -ForegroundColor Gray
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

# 等待进程完全退出
Start-Sleep -Seconds 2

Write-Host ""
Write-Host "=== 启动后端服务 ===" -ForegroundColor Green

# 启动后端
Start-Process powershell -ArgumentList "-NoExit", "cd $PSScriptRoot\backend; python -m uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=== 启动前端服务 ===" -ForegroundColor Green

# 启动前端
Start-Process powershell -ArgumentList "-NoExit", "cd $PSScriptRoot\frontend; pnpm dev"

Write-Host ""
Write-Host "=== 启动完成 ===" -ForegroundColor Cyan
Write-Host "后端: http://localhost:8001"
Write-Host "前端: http://localhost:3000 (或自动分配的端口)"
Write-Host ""
