#!/bin/bash
echo "=== 环境检查 ==="
echo "Python 版本:"
python3 --version

echo -e "\n工作目录:"
pwd

echo -e "\n检查依赖:"
python3 -c "import fastapi; print('✓ fastapi')" 2>/dev/null || echo "✗ fastapi 未安装"
python3 -c "import uvicorn; print('✓ uvicorn')" 2>/dev/null || echo "✗ uvicorn 未安装"
python3 -c "import scrapy; print('✓ scrapy')" 2>/dev/null || echo "✗ scrapy 未安装"
python3 -c "from playwright.async_api import async_playwright; print('✓ playwright')" 2>/dev/null || echo "✗ playwright 未安装"

echo -e "\n检查 main.py:"
python3 -c "from main import app; print('✓ main.py 导入成功')" 2>/dev/null || echo "✗ main.py 导入失败"

echo -e "\n检查端口 8000:"
lsof -i :8000 2>/dev/null && echo "⚠ 端口 8000 已被占用" || echo "✓ 端口 8000 可用"

echo -e "\n=== 检查完成 ==="

