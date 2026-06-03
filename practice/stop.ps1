# ╔══════════════════════════════════════════════════════════╗
# ║     停止对练系统所有服务                                ║
# ╚══════════════════════════════════════════════════════════╝

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     停止对练系统所有服务                      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ====================== 按端口停止 ======================
$ports = @(8001, 4000)
$portNames = @{8001 = "后端"; 4000 = "前端"}

foreach ($port in $ports) {
    Write-Host "[$($portNames[$port])] 释放端口 $port..." -ForegroundColor Yellow
    $connections = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    if ($connections) {
        $pids = @()
        foreach ($conn in $connections) {
            $pid = ($conn -split '\s+')[-1]
            if ($pid -match '^\d+$' -and $pids -notcontains $pid) {
                $pids += $pid
            }
        }
        foreach ($pid in $pids) {
            try {
                $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($proc) {
                    Write-Host "      停止 $($proc.ProcessName) (PID: $pid)" -ForegroundColor Gray
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                }
            } catch {
                Write-Host "      无法停止 PID: $pid" -ForegroundColor Yellow
            }
        }
        Write-Host "      端口 $port 已释放" -ForegroundColor Green
    } else {
        Write-Host "      端口 $port 未被占用" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           所有服务已停止                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
