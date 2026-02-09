@echo off
echo ========================================
echo   NovaPulse 2.0 - BUILD EXE
echo ========================================
echo.

cd /d "G:\Meu Drive\NovaPulse\PythonVersion"

echo [INFO] Instalando dependencias...
python -m pip install pyinstaller pywebview --quiet

echo.
echo [INFO] Compilando NovaPulse.exe...
echo.

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "NovaPulse" ^
    --icon "novapulse.ico" ^
    --add-data "config.yaml;." ^
    --add-data "modules;modules" ^
    --add-data "dashboard.html;." ^
    --add-data "novapulse.ico;." ^
    --add-data "novapulse_logo.png;." ^
    --hidden-import pynvml ^
    --hidden-import wmi ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import psutil ^
    --hidden-import yaml ^
    --hidden-import webview ^
    --uac-admin ^
    novapulse.py

echo.
if exist "dist\NovaPulse.exe" (
    echo [SUCCESS] NovaPulse.exe criado!
    copy "dist\NovaPulse.exe" "%USERPROFILE%\Desktop\" >nul 2>&1
    echo [OK] Copiado para Area de Trabalho!
) else (
    echo [ERROR] Falha na compilacao.
)

pause
