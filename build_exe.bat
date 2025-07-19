@echo off
chcp 65001 >nul
echo ========================================
echo Bid Information Scraper - EXE Builder
echo ========================================
echo.

echo Starting build process...
python build_exe.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! See the error message above.
    echo.
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable has been created in the dist folder.
echo.
pause