@echo off
chcp 65001 >nul
echo ========================================
echo Bid Information Scraper - Environment Setup
echo ========================================
echo.

echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python environment not detected. Please install Python 3.8 or higher
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [SUCCESS] Python environment installed
python --version

echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Retrying with Chinese mirror...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
)

echo.
echo ========================================
echo Environment setup completed!
echo ========================================
echo.
echo Usage:
echo 1. Double-click start.bat to begin scraping (previous day data)
echo 2. Or use command line: python scraper.py --date 2025-07-18
echo 3. Check README.md for detailed usage instructions
echo.
echo Data will be saved directly to MySQL database as configured in config.ini
echo.
pause
