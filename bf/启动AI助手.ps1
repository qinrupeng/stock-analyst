Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "      🚀 OpenClaw AI 助手一键启动" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# 1. 设置工作空间路径
$WorkspacePath = "D:\AI_Workspace"
$ProjectsPath = "$WorkspacePath\projects"
$DocsPath = "$WorkspacePath\docs"
$DataPath = "$WorkspacePath\data"
$LogsPath = "$WorkspacePath\logs"

Write-Host "`n[1/6] 📁 检查工作空间目录..." -ForegroundColor Green

# 创建目录结构
$directories = @($WorkspacePath, $ProjectsPath, $DocsPath, $DataPath, $LogsPath)
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Host "   创建目录: $dir" -ForegroundColor Yellow
    } else {
        Write-Host "   目录已存在: $dir" -ForegroundColor Gray
    }
}

# 2. 设置工作空间配置
Write-Host "`n[2/6] ⚙️ 配置工作空间..." -ForegroundColor Green

# 检查是否已设置工作空间
$currentWorkspace = openclaw config get agents.defaults.workspace 2>$null
if (-not $currentWorkspace -or $currentWorkspace -ne $WorkspacePath) {
    try {
        openclaw config set agents.defaults.workspace $WorkspacePath
        Write-Host "   工作空间已设置为: $WorkspacePath" -ForegroundColor Yellow
    } catch {
        Write-Host "   警告: 无法自动设置工作空间，请手动设置" -ForegroundColor Red
        Write-Host "   运行: openclaw config set agents.defaults.workspace `"$WorkspacePath`""
    }
} else {
    Write-Host "   工作空间已正确配置: $WorkspacePath" -ForegroundColor Green
}

# 3. 修复认证问题
Write-Host "`n[3/6] 🔐 修复认证问题..." -ForegroundColor Green
Write-Host "   设置认证令牌..." -ForegroundColor Yellow

# 先检查是否能运行 openclaw 命令
$openclawCmd = "openclaw"
$openclawPath = "C:\Users\Administrator\AppData\Roaming\npm\openclaw.cmd"

# 如果 openclaw 命令不能用，就用完整路径
try {
    $testResult = & $openclawCmd --version
    Write-Host "   ✅ openclaw 命令可用" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  openclaw 命令不可用，使用完整路径" -ForegroundColor Yellow
    $openclawCmd = $openclawPath
}

# 设置认证配置
try {
    & $openclawCmd config set gateway.auth.mode token
    & $openclawCmd config set gateway.auth.token "openclaw-local"
    Write-Host "   ✅ 认证已设置" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 无法设置认证，跳过..." -ForegroundColor Red
}

# 设置环境变量
$env:OPENCLAW_GATEWAY_TOKEN = "openclaw-local"

# 4. 显示目录信息
Write-Host "`n[4/6] 📊 目录结构信息:" -ForegroundColor Green
Write-Host "   📁 工作空间: $WorkspacePath"
Write-Host "   📁 项目目录: $ProjectsPath"
Write-Host "   📁 文档目录: $DocsPath"
Write-Host "   📁 数据目录: $DataPath"
Write-Host "   📁 日志目录: $LogsPath"

# 5. 切换到工作空间
Write-Host "`n[5/6] 🔄 切换到工作空间..." -ForegroundColor Green
Set-Location $WorkspacePath
Write-Host "   当前目录: $(Get-Location)" -ForegroundColor Yellow

# 6. 启动浏览器自动化服务（在网关之前启动，避免依赖问题）
Write-Host "`n[6/7] 🌐 启动浏览器自动化服务..." -ForegroundColor Green
try {
    # 检查浏览器服务是否已在运行
    $browserStatus = & $openclawCmd browser status 2>&1
    if ($browserStatus -match "running: true") {
        Write-Host "   ℹ️  浏览器服务已在运行" -ForegroundColor Cyan
    } else {
        # 启动浏览器服务
        & $openclawCmd browser start
        Write-Host "   ✅ 浏览器服务启动命令已执行" -ForegroundColor Green
        
        # 等待浏览器服务启动
        Start-Sleep -Seconds 3
        
        # 验证浏览器服务状态
        $browserStatus = & $openclawCmd browser status 2>&1
        if ($browserStatus -match "running: true") {
            Write-Host "   ✅ 浏览器服务运行正常" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  浏览器服务启动状态异常" -ForegroundColor Yellow
            Write-Host "   状态信息: $browserStatus" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "   ⚠️  启动浏览器服务时遇到问题: $_" -ForegroundColor Yellow
    Write-Host "   您可以在网关启动后手动运行：openclaw browser start" -ForegroundColor Gray
}

# 7. 启动 OpenClaw 网关服务（前台运行，保持窗口不关闭）
Write-Host "`n[7/7] 🚀 启动 OpenClaw 网关服务（前台运行）..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   🎯 正在启动 OpenClaw AI 助手..." -ForegroundColor Green
Write-Host "   🔗 访问地址: http://localhost:8090" -ForegroundColor Cyan
Write-Host "   🔐 认证令牌: openclaw-local" -ForegroundColor Cyan
Write-Host "   📁 工作空间: $WorkspacePath" -ForegroundColor Cyan
Write-Host "   🏷️  版本: 2026.2.6-3" -ForegroundColor Cyan
Write-Host "   🕐 启动时间: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "`n重要提示:" -ForegroundColor Yellow
Write-Host "• 请勿关闭此窗口，否则服务将停止" -ForegroundColor White
Write-Host "• 按 Ctrl+C 可停止服务" -ForegroundColor White
Write-Host "• 如果页面需要认证，请输入令牌: openclaw-local" -ForegroundColor White
Write-Host "`n"

# 在后台自动打开浏览器（不等待）
try {
    # 延迟2秒后打开浏览器，给网关一点启动时间
    Start-Job -ScriptBlock {
        Start-Sleep -Seconds 2
        Start-Process "http://localhost:8090" -ErrorAction SilentlyContinue
    } | Out-Null
    Write-Host "   ✅ 已安排自动打开浏览器" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  无法自动打开浏览器，请手动访问: http://localhost:8090" -ForegroundColor Yellow
}

Write-Host "`n正在启动网关服务（此过程将持续运行）..." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan

# 这里是关键改动：直接在前台启动网关服务，这会阻塞脚本执行，直到按 Ctrl+C
try {
    # 直接运行网关服务（前台阻塞模式）
    & $openclawCmd gateway --token openclaw-local
} catch {
    Write-Host "网关服务异常退出: $_" -ForegroundColor Red
}

Write-Host "`n==================================================" -ForegroundColor Cyan
Write-Host "      ⏹️  OpenClaw 网关服务已停止" -ForegroundColor Yellow
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")