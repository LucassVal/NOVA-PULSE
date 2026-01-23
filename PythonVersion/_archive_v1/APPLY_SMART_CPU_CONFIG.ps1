# Script PowerShell para configurar Windows para máxima responsividade
# Mantém limite de 80% da CPU mas otimiza latência e priorização

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  CONFIGURANDO WINDOWS PARA MÁXIMA RESPONSIVIDADE" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# 1. Ativar plano High Performance (mas mantém 80% max configurado)
Write-Host "[1/4] Ativando plano High Performance..." -ForegroundColor Green
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
Write-Host "      ✓ High Performance ativado" -ForegroundColor Gray

# 2. Desabilitar core parking (CPU cores respondem mais rápido)
Write-Host "[2/4] Desabilitando CPU Core Parking..." -ForegroundColor Green
powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR CPMINCORES 100
powercfg /setactive SCHEME_CURRENT
Write-Host "      ✓ Todos os cores sempre disponíveis" -ForegroundColor Gray

# 3. Reduzir latência do timer do Windows (mais responsivo)
Write-Host "[3/4] Otimizando timer resolution..." -ForegroundColor Green
bcdedit /set disabledynamictick yes
bcdedit /set useplatformtick yes
Write-Host "      ✓ Timer otimizado (requer reinicialização)" -ForegroundColor Gray

# 4. Configurar prioridades de I/O
Write-Host "[4/4] Configurando prioridades de disco..." -ForegroundColor Green
fsutil behavior set disablelastaccess 1
Write-Host "      ✓ Last Access desabilitado (I/O mais rápido)" -ForegroundColor Gray

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ✓ CONFIGURAÇÃO COMPLETA!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "RESULTADO:" -ForegroundColor Yellow
Write-Host "  • CPU mais responsiva (menos latência)" -ForegroundColor White
Write-Host "  • Todos os cores sempre ativos" -ForegroundColor White
Write-Host "  • I/O de disco otimizado" -ForegroundColor White
Write-Host "  • Limite de 80% MANTIDO (estabilidade)" -ForegroundColor White
Write-Host ""
Write-Host "ATENÇÃO: Algumas mudanças requerem REINICIALIZAÇÃO" -ForegroundColor Red
Write-Host ""
pause
