## 使用 GitHub Actions 远程构建（无本机 Docker Desktop）
如果你的机器无法稳定构建（代理/网络/资源受限），可以让 GitHub Actions 在云端构建镜像并把镜像打包为 tar 下载：
- 在仓库的 Actions 页运行 `Build Docker image and upload artifact`（或在 Push 到分支时触发，如果你想自动化可以把 workflow 添加到 push 事件）。
- 构建完成后在 workflow 运行页面下载名为 `tik-server-image` 的 artifact（文件 `tik-server-latest.tar`）。
- 在本机把 tar 导入并运行：

```bash
# 下载 artifact 后
docker load -i tik-server-latest.tar
docker run -p 8000:8000 tik-server:latest
```

这免除了必须在每台机器上运行 Docker Desktop 的需要，只要能下载 artifact 并在目标机器上 `docker load` 即可部署镜像。
# 部署指南

本项目支持本地运行和 Docker 容器化部署两种方式。

## 前提条件

### 本地运行
- Python 3.9+
- MySQL 8.0 或其他支持的数据库
- Playwright 浏览器环境（需运行 `playwright install chromium`）

### Docker 容器部署
- Docker 20.10+
- Docker Compose 2.0+

---

## 方式一：本地开发/运行（非容器）

### 1. 安装依赖

```bash
# 进入项目根目录
cd /path/to/tik-server

# 设置 Python 路径
export PYTHONPATH=$(pwd):$PYTHONPATH

# 安装 Python 依赖
pip3 install -r config/requirements.txt

# 安装 Playwright 浏览器及系统依赖
### 2. 配置数据库

修改 `app/tiktok_scraper/database/models.py` 中的 `DATABASE_URL`，或设置环境变量：

```bash
export DATABASE_URL="mysql+pymysql://root:root@localhost:3306/tiktok_db?charset=utf8mb4"
```

确保 MySQL 已启动且数据库存在（或由 `init_db()` 自动创建）。

### 3. 启动服务

```bash
./scripts/start.sh
```

或

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. 验证

- 健康检查：`curl http://localhost:8000/health`
- API 文档：访问 `http://localhost:8000/docs`
---

## 方式二：Docker Compose 容器化部署（推荐生产）

### 1. 准备环境配置

确保 `config/.env` 存在且包含以下内容（或已有正确的配置）：

```bash
# MySQL 数据库配置
MYSQL_ROOT_PASSWORD=tiktok_root_123
MYSQL_DATABASE=tiktok_db
MYSQL_USER=tiktok
MYSQL_PASSWORD=tiktok_password_123

# 数据库连接 URL（Docker 内部使用）
DATABASE_URL=mysql+pymysql://tiktok:tiktok_password_123@mysql:3306/tiktok_db?charset=utf8mb4

# 时区
TZ=Asia/Shanghai
```

**注意**：`.env` 可从仓库根复制到 `config/` 下：
```bash
cp .env config/.env
```

### 2. 构建并启动容器
docker compose up --build
```

首次构建会：
- 拉取 Python 3.9-slim 基础镜像
- 安装 Playwright 系统依赖和 Chromium 浏览器（可能耗时 5-10 分钟）
- 启动 MySQL 服务并运行初始化脚本
- 启动 FastAPI 应用

### 3. 验证服务

```bash
# 检查容器状态
docker compose ps

# 查看应用日志
docker compose logs tiktok-app

# 测试健康检查
curl http://localhost:8888/health
```
```bash
FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

# Use Playwright official image to avoid heavy system package installs during build.
ENV PYTHONPATH=/app:$PYTHONPATH

# Copy requirements from the build context (config/) and install
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy config files; application code is mounted into /app/app at runtime by docker-compose
COPY . /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
	CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
docker compose down

# 若要删除数据卷（包括 MySQL 数据）
docker compose down -v
```

---

## 常见问题与排查

### 问题 1：Playwright 浏览器安装失败

**症状**：Docker 构建时 `playwright install chromium` 失败，或提示缺少系统库。

**解决方案**：
1. 确保 Dockerfile 包含完整的系统依赖（已在 `config/Dockerfile` 中修复）。
2. 若仍失败，可尝试改用 Playwright 官方镜像。联系我，我会提供替代 Dockerfile。

### 问题 2：MySQL 连接失败

**症状**：应用日志显示 `pymysql.Error` 或 `Connection refused`。

**排查步骤**：
```bash
# 检查 MySQL 容器是否运行
docker compose ps mysql

# 查看 MySQL 日志
docker compose logs mysql

# 若容器未启动，检查端口冲突
lsof -i :3306
```

**原因**：
- MySQL 容器未正常启动（查看 `docker compose logs mysql`）。
- 数据库凭证不匹配（检查 `.env` 中的 `MYSQL_USER` 和 `MYSQL_PASSWORD`）。
- 应用的 `DATABASE_URL` 与 `.env` 中的配置不一致。

### 问题 3：应用健康检查失败

**症状**：容器启动但反复重启，健康检查返回 502/503。

**排查步骤**：
```bash
# 查看应用日志
docker compose logs tiktok-app

# 检查应用是否正在运行
docker compose ps tiktok-app

# 手动测试健康检查
curl -v http://localhost:8888/health
```

**原因**：
- 应用依赖（如 `uvicorn`）未安装（应该已由 `requirements.txt` 安装）。
- 数据库初始化失败，导致启动阻塞。
- 磁盘或内存不足。

### 问题 4：爬虫请求失败

**症状**：调用 `/api/crawl_scrapy` 返回 500 或爬虫无输出。

**排查步骤**：
```bash
# 查看应用日志中的 Scrapy 错误
docker compose logs tiktok-app | grep -i scrapy

# 手动测试爬虫（在容器内）
docker compose exec tiktok-app bash
cd /app
python3 -m scrapy crawl tiktok -a urls="https://www.tiktok.com/@user" -o test.json
```

**原因**：
- Playwright Chromium 未正确安装或启动失败。
- 目标 URL 不可达或被反爬。
- 爬虫配置错误（查看 `app/tiktok_scraper/settings.py`）。

---

## 前端集成

前端应将请求代理到后端。以 Docker Compose 为例：

```
# .env.production
REACT_APP_API_BASE_URL=http://localhost:8888/api
```

或在代理配置中：

```
/api -> http://localhost:8888/api
```

详见 `docs/前端代理配置.md`。

---

## 生产环境注意事项

1. **环境变量安全**：不要在代码中硬编码数据库凭证；使用 `.env` 或密钥管理服务。
2. **HTTPS**：在生产环境中使用反向代理（Nginx、HAProxy）并启用 TLS。
3. **持久化存储**：MySQL 数据已通过 `mysql-data` 卷持久化；日志存储在 `logs` 卷。
4. **扩展性**：若需水平扩展，考虑使用 Kubernetes 或 Swarm；爬虫任务队列可改用 Celery。
5. **监控**：添加应用监控（Prometheus、ELK）并配置告警。

---

## 调试命令参考

```bash
# 进入应用容器
docker compose exec tiktok-app bash

# 在容器内测试数据库连接
docker compose exec tiktok-app python3 -c "from app.tiktok_scraper.database.models import engine; engine.connect()"

# 查看完整的构建日志
docker compose build --no-cache --progress=plain tiktok-app 2>&1 | tee build.log

# 保存并恢复数据卷
docker run --rm -v tiktok_mysql-data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/mysql-backup.tar.gz -C /data .
```

---

如有进一步问题，请查阅 `docs/` 目录下的其他文档或提交 Issue。
