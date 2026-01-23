# NovaPulse - Script de Instalação do Serviço
# Execute como Administrador
# ============================================

$scriptPath = Join-Path $PSScriptRoot "novapulse.py"
$pythonExe = "python"  # ou "python3" ou caminho completo

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NovaPulse 1.0 - Instalador de Serviço" -ForegroundColor Cyan
Write-Host "  Intelligent System Optimization" -ForegroundColor DarkCyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Testa se Python está instalado
try {
    $pythonVersion = & $pythonExe --version
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ ERRO: Python não encontrado!" -ForegroundColor Red
    Write-Host "Instale Python e tente novamente" -ForegroundColor Yellow
    pause
    exit 1
}

# Instala dependências
Write-Host "`nInstalando dependências..." -ForegroundColor Cyan
& $pythonExe -m pip install -r requirements.txt

# Cria Task Scheduler task
Write-Host "`nConfigurando auto-start do NovaPulse..." -ForegroundColor Cyan

$taskName = "NovaPulse"
$taskDescription = "NovaPulse - Intelligent System Optimization"

# Remove task existente
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# Cria nova task
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$scriptPath`"" -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest

Register-ScheduledTask `
    -TaskName $taskName `
    -Description $taskDescription `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ NovaPulse instalado com sucesso!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "O NovaPulse será iniciado automaticamente ao ligar o PC" -ForegroundColor Yellow
Write-Host ""
Write-Host "Para testar agora, execute:" -ForegroundColor Cyan
Write-Host "    python novapulse.py" -ForegroundColor White
Write-Host ""

pause
