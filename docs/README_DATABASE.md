# MySQL 数据库集成说明

## 📋 数据库表结构

### users 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键，自增 |
| account | VARCHAR(255) | 用户账号（唯一索引） |
| track | VARCHAR(100) | 对应赛道 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

## 🚀 快速部署

### 1. 配置环境变量

```bash
cp .env.example .env
nano .env
```

修改以下配置：
```env
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_DATABASE=tiktok_db
MYSQL_USER=tiktok
MYSQL_PASSWORD=your_password
DATABASE_URL=mysql+pymysql://tiktok:your_password@mysql:3306/tiktok_db?charset=utf8mb4
```

### 2. 启动服务

```bash
# 构建并启动（应用 + MySQL）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 等待服务就绪（约30-60秒）
```

### 3. 验证部署

```bash
# 健康检查（会显示数据库状态）
curl http://localhost:8888/health

# 应该返回：
# {
#   "status": "ok",
#   "version": "1.2.0",
#   "database": "connected"
# }
```

## 📡 API 接口

### 1. 创建用户

```bash
POST /users
Content-Type: application/json

{
  "account": "user123",
  "track": "美妆"
}
```

**响应：**
```json
{
  "id": 1,
  "account": "user123",
  "track": "美妆",
  "created_at": "2025-12-08T10:00:00",
  "updated_at": "2025-12-08T10:00:00"
}
```

### 2. 查询所有用户

```bash
GET /users?skip=0&limit=100&account=user&track=美妆
```

**响应：**
```json
[
  {
    "id": 1,
    "account": "user123",
    "track": "美妆",
    "created_at": "2025-12-08T10:00:00",
    "updated_at": "2025-12-08T10:00:00"
  }
]
```

### 3. 根据ID查询用户

```bash
GET /users/1
```

### 4. 根据账号查询用户

```bash
GET /users/account/user123
```

### 5. 更新用户

```bash
PUT /users/1
Content-Type: application/json

{
  "track": "时尚"
}
```

### 6. 删除用户

```bash
DELETE /users/1
```

## 🔧 数据库操作

### 连接数据库

```bash
# 进入 MySQL 容器
docker exec -it tiktok-mysql mysql -u tiktok -p

# 或使用 root
docker exec -it tiktok-mysql mysql -u root -p
```

### 查询数据

```sql
USE tiktok_db;

-- 查看所有用户
SELECT * FROM users;

-- 按赛道查询
SELECT * FROM users WHERE track = '美妆';

-- 统计
SELECT track, COUNT(*) as count FROM users GROUP BY track;
```

### 备份数据库

```bash
docker exec tiktok-mysql mysqldump -u root -p tiktok_db > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
cat backup_20251208.sql | docker exec -i tiktok-mysql mysql -u root -p tiktok_db
```

## 📊 数据持久化

数据存储在：
```
/opt/tik-server/mysql-data/
```

即使容器删除，数据也不会丢失：
```bash
docker-compose down
docker-compose up -d
# 数据仍然存在！
```

## 🛠️ 故障排查

### 数据库连接失败

```bash
# 检查 MySQL 容器状态
docker-compose ps mysql

# 查看 MySQL 日志
docker-compose logs mysql

# 测试连接
docker exec -it tiktok-mysql mysql -u tiktok -p -e "SELECT 1"
```

### 表不存在

```bash
# 手动初始化数据库
docker exec -it tiktok-mysql mysql -u root -p < database/init.sql
```

### 字符编码问题

确保使用 `utf8mb4` 字符集：
```sql
ALTER DATABASE tiktok_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

