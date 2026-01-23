@echo off
REM Script para parar otimizador atual e reiniciar com novas configs

echo.
echo ════════════════════════════════════════════════════════════
echo   REINICIANDO OTIMIZADOR COM NOVAS CONFIGURACOES
echo ════════════════════════════════════════════════════════════
echo.
echo [1/2] Parando otimizador atual...
echo       Pressione Ctrl+C na janela do otimizador para parar
echo.
pause
echo.
echo [2/2] Iniciando otimizador com configuracoes de CPU...
echo.
powershell -Command "Start-Process python -ArgumentList 'win_optimizer.py' -Verb RunAs"
echo.
echo Otimizador reiniciado!
echo.
pause
