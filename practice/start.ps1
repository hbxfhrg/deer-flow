# ╔══════════════════════════════════════════════════════════╗
# ║      DeerFlow 对练系统 — 一键启动 (PowerShell)          ║
# ╚══════════════════════════════════════════════════════════╝

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      DeerFlow 对练系统 — 一键启动            ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ====================== 环境检查 ======================
Write-Host "[检查] 环境依赖..." -ForegroundColor Yellow

# 检查 Python
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) { $pythonCmd = "python" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $pythonCmd = "python3" }
else {
    Write-Host "  [错误] 未找到 Python，请先安装 Python 3.12+" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  Python: $((& $pythonCmd --version) 2>&1)" -ForegroundColor Green

# 检查 Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  [错误] 未找到 Node.js，请先安装 Node.js 18+" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  Node: $((node --version) 2>&1)" -ForegroundColor Green

# 检查 npm
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "  [错误] 未找到 npm" -ForegroundColor Red
    pause
    exit 1
}
Write-Host "  npm: $((npm --version) 2>&1)" -ForegroundColor Green

Write-Host ""

# ====================== 安装依赖（如需要） ======================
Write-Host "[检查] 依赖安装状态..." -ForegroundColor Yellow

# 后端依赖
$backendDir = Join-Path $ScriptDir "backend"
if (Test-Path (Join-Path $backendDir "requirements.txt")) {
    # 快速检查关键包是否已安装
    $checkResult = & $pythonCmd -c "import fastapi, uvicorn, sqlalchemy, langchain_openai" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  后端依赖未安装，正在安装..." -ForegroundColor Yellow
        Push-Location $backendDir
        & $pythonCmd -m pip install -r requirements.txt -q
        Pop-Location
        Write-Host "  后端依赖安装完成" -ForegroundColor Green
    } else {
        Write-Host "  后端依赖: 已安装" -ForegroundColor Green
    }
}

# 前端依赖
if (Test-Path (Join-Path $ScriptDir "node_modules")) {
    Write-Host "  前端依赖: 已安装" -ForegroundColor Green
} else {
    Write-Host "  前端依赖未安装，正在安装..." -ForegroundColor Yellow
    Push-Location $ScriptDir
    npm install
    Pop-Location
    Write-Host "  前端依赖安装完成" -ForegroundColor Green
}

Write-Host ""

# ====================== 启动后端 ======================
Write-Host "[1/2] 启动后端服务 (端口 8001)..." -ForegroundColor Green
Write-Host "      命令: uvicorn main:app --reload --port 8001" -ForegroundColor Gray

Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Write-Host '╔══════════════════════════════════════════╗' -ForegroundColor Cyan
Write-Host '║  对练后端  (端口 8001)                  ║' -ForegroundColor Cyan
Write-Host '╚══════════════════════════════════════════╝' -ForegroundColor Cyan
cd '$backendDir'
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
"@

# 等待后端初始化
Write-Host "      等待后端初始化 (4秒)..." -ForegroundColor Gray
Start-Sleep -Seconds 4

# 检查后端是否启动成功
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "      后端启动成功 ✓" -ForegroundColor Green
    }
} catch {
    Write-Host "      后端可能仍在启动中，请稍后检查 http://localhost:8001/health" -ForegroundColor Yellow
}

Write-Host ""

# ====================== 启动前端 ======================
Write-Host "[2/2] 启动前端服务 (端口 4000)..." -ForegroundColor Green
Write-Host "      命令: npm run dev" -ForegroundColor Gray

Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
Write-Host '╔══════════════════════════════════════════╗' -ForegroundColor Magenta
Write-Host '║  对练前端  (端口 4000)                  ║' -ForegroundColor Magenta
Write-Host '╚══════════════════════════════════════════╝' -ForegroundColor Magenta
cd '$ScriptDir'
npm run dev
"@

Write-Host ""

# ====================== 完成 ======================
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           启动完成！                          ║" -ForegroundColor Cyan
Write-Host "╠══════════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  前端页面:  http://localhost:4000            ║" -ForegroundColor Cyan
Write-Host "║  API 文档:  http://localhost:8001/docs       ║" -ForegroundColor Cyan
Write-Host "║  健康检查:  http://localhost:8001/health      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "按任意键退出此窗口（不影响服务运行）..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
