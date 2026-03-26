@echo off
echo =========================================================
echo                  GI SCRIBE LAUNCHER
echo =========================================================
echo Initializing standalone AI environment...
echo.

cd /d "%~dp0"

IF EXIST "dist\GI_Scribe\GI_Scribe.exe" (
    echo [INFO] Found pre-compiled executable. Starting application...
    start "" "dist\GI_Scribe\GI_Scribe.exe"
) ELSE (
    echo [ERROR] The standalone executable was not found. 
    echo Please make sure the 'dist' folder exists and PyInstaller compiled successfully.
    pause
    exit /b 1
)

echo Application launched. You can close this window.
exit /b 0
