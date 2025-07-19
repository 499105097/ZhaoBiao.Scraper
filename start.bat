@echo off
chcp 65001 >nul
echo ========================================
echo     Bid Candidate Information Scraper
echo ========================================
echo.
echo Please select an operation:
echo 1. Execute scraping immediately
echo 2. Start scheduled task (runs daily at 8:00 AM)
echo 3. Exit
echo.
set /p choice=Please enter option (1-3): 

if "%choice%"=="1" (
    echo.
    echo Executing scraping task...
    python scraper.py
    echo.
    echo Scraping completed! Please check the database.
    pause
) else if "%choice%"=="2" (
    echo.
    echo Starting scheduled task...
    echo Program will automatically execute scraping task daily at 8:00 AM
    echo Press Ctrl+C to stop the program
    echo.
    python scheduler.py
) else if "%choice%"=="3" (
    echo Goodbye!
    exit /b 0
) else (
    echo Invalid option, please restart the program.
    pause
)
pause