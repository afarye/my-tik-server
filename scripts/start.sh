#!/bin/bash
cd "$(dirname "$0")/.."
export PYTHONPATH="$(pwd):$PYTHONPATH"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

# =============================================================================
# 启动流程
# 1.
# 环境准备: 切换到项目根目录，设置Python模块路径
# 2.
# 服务启动: 使用uvicorn ASGI服务器启动FastAPI应用
# 3.
# 网络配置: 监听0.0.0.0:8000，支持外部访问
# 4.
# 性能配置: 2个工作进程处理并发请求
# 访问地址
# 本地访问: http://localhost:8000
# API文档: http://localhost:8000/docs
# ReDoc文档: http://localhost:8000/redoc
# 健康检查: http://localhost:8000/health
# 与TikTok爬虫的关系
# 启动Web API服务，提供RESTful接口
# 前端应用可以通过HTTP请求调用爬虫功能
# 支持Track和User的管理操作
# 提供爬取结果的查询和历史记录功能
# =============================================================================