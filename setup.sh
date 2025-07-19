#!/bin/bash

echo "========================================"
echo "招标信息自动抓取工具 - 环境设置"
echo "========================================"
echo

echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3环境，请先安装Python 3.8或更高版本"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "macOS: brew install python3"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

echo "[成功] Python环境已安装"
python3 --version

echo
echo "正在安装依赖包..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[警告] 使用国内镜像源重试安装..."
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
fi

echo
echo "========================================"
echo "环境设置完成！"
echo "========================================"
echo
echo "使用方法："
echo "1. 运行: python3 scraper.py （抓取前一天数据）"
echo "2. 或者: python3 scraper.py --date 2025-07-17"
echo "3. 查看用户使用手册.md了解详细使用方法"
echo
