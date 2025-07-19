#!/bin/bash

echo "========================================"
echo "Bid Information Scraper - Environment Setup"
echo "========================================"
echo

echo "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 environment not detected. Please install Python 3.8 or higher"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "macOS: brew install python3"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

echo "[SUCCESS] Python environment installed"
python3 --version

echo
echo "Installing dependencies..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[WARNING] Retrying with Chinese mirror..."
    pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
fi

echo
echo "========================================"
echo "Environment setup completed!"
echo "========================================"
echo
echo "Usage:"
echo "1. Run: python3 scraper.py (scrape previous day data)"
echo "2. Or: python3 scraper.py --date 2025-07-17 (specific date)"
echo "3. Check README.md for detailed usage instructions"
echo
echo "Data will be saved directly to MySQL database as configured in config.ini"
echo
