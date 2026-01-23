@echo off
title NovaPulse - Intelligent System Optimization
color 0A

echo.
echo  ╔═══════════════════════════════════════════════════════════╗
echo  ║                                                           ║
echo  ║           ⚡ NOVAPULSE ⚡                                 ║
echo  ║       Intelligent System Optimization                     ║
echo  ║                                                           ║
echo  ╚═══════════════════════════════════════════════════════════╝
echo.

:: Verifica se está rodando como admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Rodando como Administrador
) else (
    echo [ERRO] Este programa requer privilegios de Administrador!
    echo.
    echo Clique com botao direito e selecione "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo.
echo Iniciando NovaPulse...
echo.

python novapulse.py

if %errorLevel% neq 0 (
    echo.
    echo [ERRO] Falha ao executar. Verifique se Python esta instalado.
    echo.
    pause
)
