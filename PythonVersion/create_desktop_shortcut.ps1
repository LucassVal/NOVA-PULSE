# NovaPulse - Script para criar atalho na Área de Trabalho
# =========================================================

$SourcePath = Join-Path $PSScriptRoot "RUN_NOVAPULSE.bat"
$IconPath = Join-Path $PSScriptRoot "novapulse.ico"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "NovaPulse.lnk"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NovaPulse 1.0 - Criando Atalho" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $SourcePath
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.Description = "NovaPulse - Intelligent System Optimization"

# Usa o ícone personalizado se existir
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
    Write-Host "✓ Ícone personalizado encontrado" -ForegroundColor Green
} else {
    $Shortcut.IconLocation = "powershell.exe,0"
    Write-Host "⚠ Ícone padrão usado (novapulse.ico não encontrado)" -ForegroundColor Yellow
}

$Shortcut.Save()

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✓ Atalho NovaPulse criado com sucesso!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Local: $ShortcutPath" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANTE: Execute como Administrador!" -ForegroundColor Yellow
Write-Host ""

pause
