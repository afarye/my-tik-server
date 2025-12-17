# TikTok Scraper Server

## 项目结构

```
tik-server/
├── app/                    # 应用代码
│   ├── main.py            # FastAPI 主应用
│   └── tiktok_scraper/    # Scrapy 爬虫模块
├── config/                 # 配置文件
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── scrapy.cfg
│   └── requirements.txt
├── docs/                   # 文档
│   ├── API文档.md
│   ├── README_DATABASE.md
│   └── 前端代理配置.md
├── scripts/                # 脚本
│   ├── start.sh
│   ├── check_env.sh
│   └── ...
└── README.md
```

## 快速开始

### 启动服务

```bash
./scripts/start.sh
```

或

```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端代理配置

前端需要配置代理将 `/api` 请求转发到 `http://localhost:8000`。

详见 `docs/前端代理配置.md`

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

详细文档见 `docs/API文档.md`

