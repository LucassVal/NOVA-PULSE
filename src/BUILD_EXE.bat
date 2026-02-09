@echo off
echo ========================================
echo   NovaPulse 2.2.1 - BUILD EXE
echo ========================================
echo.

:: Request admin elevation if not already elevated
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo [INFO] Working directory: %cd%
echo.

echo [INFO] Python version:
python --version

echo.
echo [INFO] Installing/updating dependencies...
python -m pip install pyinstaller psutil wmi pyyaml colorama rich pynvml pystray pillow pywebview --quiet

echo.
echo [INFO] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo [INFO] Building NovaPulse.exe...
echo.

python -m PyInstaller ^
    --clean ^
    --noconfirm ^
    NovaPulse.spec

echo.

if exist dist\NovaPulse.exe (
    echo ========================================
    echo   BUILD SUCCESSFUL!
    echo   Output: dist\NovaPulse.exe
    echo ========================================
    echo.
    echo [INFO] Copying to Desktop...
    copy /y dist\NovaPulse.exe "%USERPROFILE%\Desktop\NovaPulse.exe"
    echo [OK] NovaPulse.exe copied to Desktop!
) else (
    echo ========================================
    echo   BUILD FAILED!
    echo   Check the output above for errors.
    echo ========================================
)

echo.
pause
