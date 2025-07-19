@echo off
chcp 65001 >nul
echo ========================================
echo     招标候选人信息抓取工具
echo ========================================
echo.
echo 请选择要执行的操作：
echo 1. 立即执行一次抓取
echo 2. 启动定时任务调度器（每天早上8点执行）
echo 3. 退出
echo.
set /p choice=请输入选项 (1-3): 

if "%choice%"=="1" (
    echo.
    echo 正在执行抓取任务...
    python scraper.py
    echo.
    echo 抓取完成！请查看生成的CSV文件。
    pause
) else if "%choice%"=="2" (
    echo.
    echo 启动定时任务调度器...
    echo 程序将在每天早上8:00自动执行抓取任务
    echo 按 Ctrl+C 可以停止程序
    echo.
    python scheduler.py
) else if "%choice%"=="3" (
    echo 再见！
    exit /b 0
) else (
    echo 无效选项，请重新运行程序。
    pause
)
pause
