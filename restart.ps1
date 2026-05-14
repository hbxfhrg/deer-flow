# DeerFlow 服务重启脚本

Write-Host "=== 清理旧进程 ===" -ForegroundColor Yellow

# 方法1：通过端口查找并停止进程
$ports = @(3000, 3001, 3002, 8001, 8000, 4000)
foreach ($port in $ports) {
    $pids = netstat -ano | Select-String ":$port\s" | ForEach-Object {
        ($_ -split '\s+')[-1]
    } | Where-Object { $_ -match '^\d+$' } | Sort-Object -Unique
    foreach ($procId in $pids) {
        if ($procId -and (Get-Process -Id $procId -ErrorAction SilentlyContinue)) {
            $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
            Write-Host "  停止进程 ID: $procId (名称: $procName, 端口: $port)" -ForegroundColor Gray
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

# 方法2：强制停止所有 Python 进程（包含 uvicorn）
Write-Host ""
Write-Host "  检查 Python 进程..." -ForegroundColor Gray
$pythonProcs = Get-Process -Name python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    foreach ($proc in $pythonProcs) {
        try {
            $procName = $proc.ProcessName
            $procId = $proc.Id
            Write-Host "  停止 Python 进程 ID: $procId" -ForegroundColor Gray
            Stop-Process -Id $procId -Force -ErrorAction Stop
        } catch {
            Write-Host "  无法停止进程 ID: $($proc.Id)" -ForegroundColor Yellow
        }
    }
}

# 方法3：强制停止所有 Node 进程（前端）
Write-Host "  检查 Node 进程..." -ForegroundColor Gray
$nodeProcs = Get-Process -Name node -ErrorAction SilentlyContinue
if ($nodeProcs) {
    foreach ($proc in $nodeProcs) {
        try {
            $procName = $proc.ProcessName
            $procId = $proc.Id
            Write-Host "  停止 Node 进程 ID: $procId" -ForegroundColor Gray
            Stop-Process -Id $procId -Force -ErrorAction Stop
        } catch {
            Write-Host "  无法停止进程 ID: $($proc.Id)" -ForegroundColor Yellow
        }
    }
}

# 等待进程完全退出
Write-Host ""
Write-Host "  等待进程完全退出..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 验证进程是否已停止
$remainingPython = Get-Process -Name python -ErrorAction SilentlyContinue
$remainingNode = Get-Process -Name node -ErrorAction SilentlyContinue

if ($remainingPython) {
    Write-Host "  警告: 仍有 Python 进程在运行" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ 所有 Python 进程已停止" -ForegroundColor Green
}

if ($remainingNode) {
    Write-Host "  警告: 仍有 Node 进程在运行" -ForegroundColor Yellow
} else {
    Write-Host "  ✓ 所有 Node 进程已停止" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 启动后端服务 ===" -ForegroundColor Green

# 启动后端
Start-Process powershell -ArgumentList "-NoExit", "cd $PSScriptRoot\backend; python -m uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 --reload"

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "=== 启动前端服务 ===" -ForegroundColor Green

# 启动前端
Start-Process powershell -ArgumentList "-NoExit", "cd $PSScriptRoot\frontend; pnpm dev"

Start-Sleep -Seconds 1

Write-Host ""
Write-Host "=== 启动对练前端服务 ===" -ForegroundColor Green

# 启动对练前端
Start-Process powershell -ArgumentList "-NoExit", "cd $PSScriptRoot\practice; npm run dev"

Write-Host ""
Write-Host "=== 重启完成 ===" -ForegroundColor Green
Write-Host "  后端: http://localhost:8001" -ForegroundColor Cyan
Write-Host "  前端: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  对练前端: http://localhost:4000" -ForegroundColor Cyan
Write-Host ""