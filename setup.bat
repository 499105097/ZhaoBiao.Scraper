@echo off
chcp 65001 >nul
echo ========================================
echo 招标信息自动抓取工具 - 环境设置
echo ========================================
echo.

echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python环境，请先安装Python 3.8或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [成功] Python环境已安装
python --version

echo.
echo 正在安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [警告] 使用国内镜像源重试安装...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
)

echo.
echo ========================================
echo 环境设置完成！
echo ========================================
echo.
echo 使用方法：
echo 1. 双击 start.bat 开始抓取（抓取前一天数据）
echo 2. 或者使用命令行：python scraper.py --date 2025-07-17
echo 3. 查看用户使用手册.md了解详细使用方法
echo.
pause
