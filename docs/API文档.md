# TikTok 爬虫服务 API 文档

## 基础信息

- **Base URL**: `http://localhost:8000`
- **API 版本**: v1.3.0
- **Content-Type**: `application/json`
- **API 前缀**: `/api` (除健康检查和部分特殊接口外，所有接口都使用此前缀)

## 目录

- [TikTok 爬虫服务 API 文档](#tiktok-爬虫服务-api-文档)
  - [基础信息](#基础信息)
  - [目录](#目录)
  - [接口列表](#接口列表)
    - [1. 健康检查](#1-健康检查)
    - [2. 爬取用户数据](#2-爬取用户数据)
  - [赛道管理接口](#赛道管理接口)
    - [3. 创建赛道](#3-创建赛道)
    - [4. 获取赛道列表](#4-获取赛道列表)
    - [5. 获取单个赛道](#5-获取单个赛道)
    - [6. 更新赛道](#6-更新赛道)
    - [7. 删除赛道](#7-删除赛道)
    - [8. 获取赛道下的用户列表](#8-获取赛道下的用户列表)
  - [用户管理接口](#用户管理接口)
    - [9. 创建用户](#9-创建用户)
    - [10. 获取用户列表](#10-获取用户列表)
    - [11. 获取单个用户（按ID）](#11-获取单个用户按id)
    - [12. 获取单个用户（按账号）](#12-获取单个用户按账号)
    - [13. 更新用户](#13-更新用户)
    - [14. 删除用户（按ID）](#14-删除用户按id)
    - [15. 删除用户（按账号）](#15-删除用户按账号)
    - [16. 根据URL更新Sec User ID](#16-根据url更新sec-user-id)
  - [用户历史记录接口](#用户历史记录接口)
    - [17. 获取用户历史记录](#17-获取用户历史记录)
    - [18. 创建用户历史记录](#18-创建用户历史记录)
  - [错误处理](#错误处理)
    - [HTTP 状态码](#http-状态码)
    - [错误响应格式](#错误响应格式)
  - [注意事项](#注意事项)
  - [交互式文档](#交互式文档)
  - [更新日志](#更新日志)
    - [v1.3.0 (2025-12-16)](#v130-2025-12-16)
    - [v1.2.0 (2025-12-11)](#v120-2025-12-11)
    - [v1.1.0 (2025-12-10)](#v110-2025-12-10)
    - [v1.0.0](#v100)

---

## 接口列表

### 1. 健康检查

检查服务是否正常运行。

**请求**
```http
GET /health
```

**响应**
```json
{
  "status": "ok",
  "version": "1.3.0",
  "database": "connected"
}
```

**示例**
```bash
curl http://localhost:8000/health
```

---

### 2. 爬取用户数据

使用 Scrapy 框架爬取 TikTok 用户数据，支持批量查询。**每次爬取成功后，系统会自动将结果保存到用户历史记录表中。**

**请求**
```http
POST /api/crawl_scrapy
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| urls | string[] | 是 | TikTok 用户主页 URL 列表 |
| start_date | string | 否 | 开始日期，格式：YYYY-MM-DD |
| end_date | string | 否 | 结束日期，格式：YYYY-MM-DD |
| wait_time | float | 否 | 等待时间（秒），默认 2.0 |

**请求示例**
```json
{
  "urls": [
    "https://www.tiktok.com/@maddieprice_backup",
    "https://www.tiktok.com/@noyfaa593"
  ]
}
```

**响应结构**

成功响应：
```json
{
  "success": true,
  "results": [
    {
      "url": "https://www.tiktok.com/@maddieprice_backup",
      "username": "maddieprice_backup",
      "following": "7",
      "followers": "88700",
      "likes": "1200000",
      "video_count": "212"
    }
  ],
  "count": 1
}
```

失败响应：
```json
{
  "success": false,
  "error": "错误信息"
}
```

**示例代码**

```bash
curl -X POST http://localhost:8000/api/crawl_scrapy \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.tiktok.com/@maddieprice_backup"
    ]
  }'
```

---

## 赛道管理接口

### 3. 创建赛道

创建新的赛道。

**请求**
```http
POST /api/tracks
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 赛道名称（唯一） |
| description | string | 否 | 赛道描述 |

**请求示例**
```json
{
  "name": "科技",
  "description": "科技类内容创作者"
}
```

**响应**
```json
{
  "id": 1,
  "name": "科技",
  "description": "科技类内容创作者",
  "user_count": 0,
  "created_at": "2025-12-11T06:49:51",
  "updated_at": "2025-12-11T06:49:51"
}
```

**错误响应**
- `400`: 赛道名称已存在
- `500`: 服务器内部错误

**示例**
```bash
curl -X POST http://localhost:8000/api/tracks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "科技",
    "description": "科技类内容创作者"
  }'
```

---

### 4. 获取赛道列表

获取所有赛道列表，支持分页和搜索。

**请求**
```http
GET /api/tracks?skip=0&limit=100&name=科技
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | integer | 否 | 跳过记录数，默认 0 |
| limit | integer | 否 | 返回记录数，默认 100 |
| name | string | 否 | 赛道名称模糊搜索 |

**响应**
```json
[
  {
    "id": 1,
    "name": "企鹅",
    "description": null,
    "user_count": 4,
    "created_at": "2025-12-11T06:49:51",
    "updated_at": "2025-12-11T06:49:51"
  },
  {
    "id": 2,
    "name": "宗教",
    "description": null,
    "user_count": 1,
    "created_at": "2025-12-11T06:49:51",
    "updated_at": "2025-12-11T06:49:51"
  }
]
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 赛道ID |
| name | string | 赛道名称 |
| description | string | 赛道描述 |
| user_count | integer | 该赛道下的用户数量 |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

**示例**
```bash
curl "http://localhost:8000/api/tracks?name=科技"
```

---

### 5. 获取单个赛道

根据赛道ID获取赛道详情。

**请求**
```http
GET /api/tracks/{track_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| track_id | integer | 赛道ID |

**响应**
```json
{
  "id": 1,
  "name": "企鹅",
  "description": null,
  "user_count": 4,
  "created_at": "2025-12-11T06:49:51",
  "updated_at": "2025-12-11T06:49:51"
}
```

**错误响应**
- `404`: 赛道不存在

**示例**
```bash
curl http://localhost:8000/api/tracks/1
```

---

### 6. 更新赛道

更新赛道信息。

**请求**
```http
PUT /api/tracks/{track_id}
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| track_id | integer | 赛道ID |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 否 | 赛道名称 |
| description | string | 否 | 赛道描述 |

**请求示例**
```json
{
  "name": "新赛道名称",
  "description": "新的描述"
}
```

**响应**
```json
{
  "id": 1,
  "name": "新赛道名称",
  "description": "新的描述",
  "user_count": 4,
  "created_at": "2025-12-11T06:49:51",
  "updated_at": "2025-12-11T07:00:00"
}
```

**错误响应**
- `400`: 赛道名称已存在
- `404`: 赛道不存在

**示例**
```bash
curl -X PUT http://localhost:8000/api/tracks/1 \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新赛道名称",
    "description": "新的描述"
  }'
```

---

### 7. 删除赛道

删除赛道。如果赛道下有用户，则无法删除。

**请求**
```http
DELETE /api/tracks/{track_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| track_id | integer | 赛道ID |

**响应**
```json
{
  "success": true,
  "message": "Track deleted successfully"
}
```

**错误响应**
- `400`: 赛道下有用户，无法删除
- `404`: 赛道不存在

**示例**
```bash
curl -X DELETE http://localhost:8000/api/tracks/1
```

---

### 8. 获取赛道下的用户列表

获取指定赛道下的所有用户。

**请求**
```http
GET /api/tracks/{track_id}/users?skip=0&limit=100
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| track_id | integer | 赛道ID |

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | integer | 否 | 跳过记录数，默认 0 |
| limit | integer | 否 | 返回记录数，默认 100 |

**响应**
```json
[
  {
    "id": 1,
    "account": "hoiuumbu",
    "track_id": 1,
    "track_name": "企鹅",
    "url": "https://www.tiktok.com/@hoiuumbu",
    "sec_user_id": null,
    "created_at": "2025-12-10T11:35:59",
    "updated_at": "2025-12-10T11:35:59"
  }
]
```

**错误响应**
- `404`: 赛道不存在

**示例**
```bash
curl "http://localhost:8000/api/tracks/1/users"
```

---

## 用户管理接口

### 9. 创建用户

创建新的用户记录。

**请求**
```http
POST /api/users
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| account | string | 是 | 用户账号（唯一） |
| track_id | integer | 是 | 赛道ID |
| url | string | 否 | 完整链接 |

**请求示例**
```json
{
  "account": "hoiuumbu",
  "track_id": 1,
  "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi3"
}
```

**响应**
```json
{
  "id": 1,
  "account": "hoiuumbu",
  "track_id": 1,
  "track_name": "企鹅",
  "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi3",
  "sec_user_id": null,
  "created_at": "2025-12-10T11:35:59",
  "updated_at": "2025-12-10T11:35:59"
}
```

**错误响应**
- `400`: 用户账号已存在
- `404`: 赛道不存在

**示例**
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "account": "hoiuumbu",
    "track_id": 1,
    "url": "https://www.tiktok.com/@hoiuumbu"
  }'
```

---

### 10. 获取用户列表

获取用户列表，支持分页和过滤。

**请求**
```http
GET /api/users?skip=0&limit=100&account=hoiuumbu&track_id=1
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| skip | integer | 否 | 跳过记录数，默认 0 |
| limit | integer | 否 | 返回记录数，默认 100 |
| account | string | 否 | 账号模糊搜索 |
| track_id | integer | 否 | 赛道ID精确匹配 |

**响应**
```json
[
  {
    "id": 1,
    "account": "hoiuumbu",
    "track_id": 1,
    "track_name": "企鹅",
    "url": "https://www.tiktok.com/@hoiuumbu",
    "sec_user_id": null,
    "created_at": "2025-12-10T11:35:59",
    "updated_at": "2025-12-10T11:35:59"
  },
  {
    "id": 2,
    "account": "definvei",
    "track_id": 2,
    "track_name": "宗教",
    "url": "https://www.tiktok.com/@definvei",
    "sec_user_id": null,
    "created_at": "2025-12-10T11:35:59",
    "updated_at": "2025-12-10T11:35:59"
  }
]
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户ID |
| account | string | 用户账号 |
| track_id | integer | 赛道ID |
| track_name | string | 赛道名称 |
| url | string | 完整链接 |
| sec_user_id | string | Sec User ID |
| created_at | string | 创建时间 |
| updated_at | string | 更新时间 |

**示例**
```bash
curl "http://localhost:8000/api/users?track_id=1"
```

---

### 11. 获取单个用户（按ID）

根据用户ID获取用户信息。

**请求**
```http
GET /api/users/{user_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户ID |

**响应**
```json
{
  "id": 1,
  "account": "hoiuumbu",
  "track_id": 1,
  "track_name": "企鹅",
  "url": "https://www.tiktok.com/@hoiuumbu",
  "sec_user_id": null,
  "created_at": "2025-12-10T11:35:59",
  "updated_at": "2025-12-10T11:35:59"
}
```

**错误响应**
- `404`: 用户不存在

**示例**
```bash
curl http://localhost:8000/api/users/1
```

---

### 12. 获取单个用户（按账号）

根据账号获取用户信息。

**请求**
```http
GET /api/users/account/{account}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| account | string | 用户账号 |

**响应**
```json
{
  "id": 1,
  "account": "hoiuumbu",
  "track_id": 1,
  "track_name": "企鹅",
  "url": "https://www.tiktok.com/@hoiuumbu",
  "sec_user_id": null,
  "created_at": "2025-12-10T11:35:59",
  "updated_at": "2025-12-10T11:35:59"
}
```

**错误响应**
- `404`: 用户不存在

**示例**
```bash
curl http://localhost:8000/api/users/account/hoiuumbu
```

---

### 13. 更新用户

更新用户信息。

**请求**
```http
PUT /api/users/{user_id}
Content-Type: application/json
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户ID |

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| track_id | integer | 否 | 赛道ID |
| url | string | 否 | 完整链接 |
| sec_user_id | string | 否 | Sec User ID |

**请求示例**
```json
{
  "track_id": 2,
  "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi4",
  "sec_user_id": "MS4wLjABAAAA..."
}
```

**响应**
```json
{
  "id": 1,
  "account": "hoiuumbu",
  "track_id": 2,
  "track_name": "宗教",
  "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi4",
  "sec_user_id": "MS4wLjABAAAA...",
  "created_at": "2025-12-10T11:35:59",
  "updated_at": "2025-12-10T11:36:30"
}
```

**错误响应**
- `404`: 用户不存在或赛道不存在

**示例**
```bash
curl -X PUT http://localhost:8000/api/users/1 \
  -H "Content-Type: application/json" \
  -d '{
    "track_id": 2
  }'
```

---

### 14. 删除用户（按ID）

根据用户ID删除用户记录。

**请求**
```http
DELETE /api/users/{user_id}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | integer | 用户ID |

**响应**
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

**错误响应**
- `404`: 用户不存在

**示例**
```bash
curl -X DELETE http://localhost:8000/api/users/1
```

---

### 15. 删除用户（按账号）

根据用户账号删除用户记录。

**请求**
```http
DELETE /api/users/account/{account}
```

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| account | string | 用户账号 |

**响应**
```json
{
  "success": true,
  "message": "User deleted successfully"
}
```

**错误响应**
- `404`: 用户不存在

**示例**
```bash
curl -X DELETE http://localhost:8000/api/users/account/hoiuumbu
```

---

### 16. 根据URL更新Sec User ID

根据用户URL更新对应的Sec User ID。

**请求**
```http
PUT /api/update-sec-id
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 用户完整链接 |
| sec_user_id | string | 是 | Sec User ID |

**请求示例**
```json
{
  "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi3",
  "sec_user_id": "MS4wLjABAAAA..."
}
```

**响应**
```json
{
  "id": 1,
  "account": "hoiuumbu",
  "track_id": 1,
  "track_name": "企鹅",
  "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi3",
  "sec_user_id": "MS4wLjABAAAA...",
  "created_at": "2025-12-10T11:35:59",
  "updated_at": "2025-12-10T11:40:00"
}
```

**错误响应**
- `404`: 未找到对应URL的用户

**示例**
```bash
curl -X PUT http://localhost:8000/api/update-sec-id \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.tiktok.com/@hoiuumbu?_r=1&_t=ZS-924u51VcZi3",
    "sec_user_id": "MS4wLjABAAAA..."
  }'
```

---

## 用户历史记录接口

### 17. 获取用户历史记录

根据用户URL获取历史记录列表，支持分页查询。历史记录按入库时间倒序排列。

**请求**
```http
GET /api/history-user?url={url}&skip=0&limit=100
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 用户完整链接 |
| skip | integer | 否 | 跳过记录数，默认 0 |
| limit | integer | 否 | 返回记录数，默认 100，最大 100 |

**响应**
```json
[
  {
    "id": 1,
    "url": "https://www.tiktok.com/@hoiuumbu",
    "username": "hoiuumbu",
    "following": "7",
    "followers": "88700",
    "likes": "1200000",
    "video_count": "212",
    "videos": null,
    "user_info": null,
    "created_at": "2025-12-16T11:44:27"
  },
  {
    "id": 2,
    "url": "https://www.tiktok.com/@hoiuumbu",
    "username": "hoiuumbu",
    "following": "8",
    "followers": "89000",
    "likes": "1210000",
    "video_count": "215",
    "videos": null,
    "user_info": null,
    "created_at": "2025-12-16T11:04:08"
  }
]
```

**响应字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 历史记录ID |
| url | string | 用户完整链接 |
| username | string | 用户名 |
| following | string | 关注数 |
| followers | string | 粉丝数 |
| likes | string | 点赞数 |
| video_count | string | 视频数 |
| videos | object | 视频信息（JSON格式） |
| user_info | object | 用户详细信息（JSON格式） |
| created_at | string | 入库时间 |

**示例**
```bash
curl "http://localhost:8000/api/history-user?url=https://www.tiktok.com/@hoiuumbu&limit=10"
```

---

### 18. 创建用户历史记录

手动创建用户历史记录。爬虫接口会自动保存历史记录，此接口用于手动补充数据。

**请求**
```http
POST /api/history-user
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| url | string | 是 | 用户完整链接 |
| username | string | 否 | 用户名 |
| following | string | 否 | 关注数 |
| followers | string | 否 | 粉丝数 |
| likes | string | 否 | 点赞数 |
| video_count | string | 否 | 视频数 |
| videos | object | 否 | 视频信息（JSON格式） |
| user_info | object | 否 | 用户详细信息（JSON格式） |

**请求示例**
```json
{
  "url": "https://www.tiktok.com/@hoiuumbu",
  "username": "hoiuumbu",
  "following": "7",
  "followers": "88700",
  "likes": "1200000",
  "video_count": "212",
  "videos": null,
  "user_info": null
}
```

**响应**
```json
{
  "id": 1,
  "url": "https://www.tiktok.com/@hoiuumbu",
  "username": "hoiuumbu",
  "following": "7",
  "followers": "88700",
  "likes": "1200000",
  "video_count": "212",
  "videos": null,
  "user_info": null,
  "created_at": "2025-12-16T11:44:27"
}
```

**错误响应**
- `500`: 服务器内部错误

**示例**
```bash
curl -X POST http://localhost:8000/api/history-user \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.tiktok.com/@hoiuumbu",
    "username": "hoiuumbu",
    "following": "7",
    "followers": "88700",
    "likes": "1200000",
    "video_count": "212"
  }'
```

**说明**
- 每次调用爬虫接口 `/api/crawl_scrapy` 时，系统会自动将爬取结果保存到历史记录表
- 此接口主要用于手动补充历史数据或修复数据
- 历史记录以 `url` 作为唯一标识，同一URL可以有多条历史记录

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求错误（如账号已存在、赛道名称已存在、无法删除有用户的赛道） |
| 404 | 资源不存在 |
| 422 | 请求参数错误 |
| 500 | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "错误信息描述"
}
```

或

```json
{
  "detail": [
    {
      "loc": ["body", "urls"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 注意事项

1. **URL 格式**: 必须使用完整的 TikTok 用户主页 URL，格式为 `https://www.tiktok.com/@username`
2. **批量查询**: 支持同时查询多个用户，单次最多 50 个 URL，建议 10-20 个为最佳
3. **超时设置**: 每个请求最长等待 300 秒（5 分钟）
4. **赛道管理**: 
   - 创建用户时必须指定有效的 `track_id`
   - 删除赛道前需要先移除该赛道下的所有用户
   - 赛道名称必须唯一
5. **用户管理**:
   - 用户账号必须唯一
   - 可以通过 `track_id` 查询特定赛道下的用户
   - 更新用户时，如果指定 `track_id`，必须确保该赛道存在
6. **历史记录**:
   - 每次调用爬虫接口时，系统会自动保存历史记录
   - 历史记录以 `url` 作为唯一标识，同一URL可以有多条历史记录
   - 历史记录按入库时间倒序排列，便于查看最新数据
   - 支持通过 `GET /api/history-user` 查询指定用户的所有历史记录
7. **性能指标**: 
   - 单个URL: ~1.7秒 ⚡
   - 2个URL: ~2.7秒  
   - 5个URL: ~5.7秒
8. **异常处理**: 服务会自动处理所有错误，失败的URL返回空数据，不影响其他URL
9. **并发支持**: 支持多个API请求并发执行，互不影响
10. **日期过滤**: `start_date` 和 `end_date` 参数当前暂未使用

---

## 交互式文档

启动服务后，访问以下地址查看交互式 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 更新日志

### v1.3.0 (2025-12-16)
- ✨ **新增用户历史记录功能**: 
  - `GET /api/history-user` - 获取用户历史记录列表
  - `POST /api/history-user` - 手动创建历史记录
  - 爬虫接口自动保存历史记录
- 📊 **历史记录表**: 新增 `user_history` 表，存储用户信息和视频信息的变更历史
- 🔧 **接口路径优化**: `PUT /api/update-sec-id` 路径调整，避免路由冲突
- 📝 **数据追踪**: 支持按用户URL查询历史数据，便于分析用户数据变化趋势

### v1.2.0 (2025-12-11)
- ✨ **新增赛道管理接口**: 完整的赛道CRUD操作
- ✨ **赛道用户统计**: 自动统计每个赛道下的用户数量
- 🔧 **用户接口优化**: 使用 `track_id` 替代 `track` 字段，建立外键关系
- 📝 **响应增强**: 用户响应中包含 `track_name` 字段，方便前端显示
- 🔧 **新增接口**: 
  - `GET /api/tracks/{track_id}/users` - 获取赛道下的用户列表
  - 完整的赛道管理接口（创建、查询、更新、删除）

### v1.1.0 (2025-12-10)
- ✨ **新增用户管理接口**: 完整的用户CRUD操作
- 📝 **数据库扩展**: 添加url和sec_user_id字段
- 🔧 **新增接口**: PUT /api/update-sec-id 根据URL更新Sec User ID
- 🔧 **健康检查增强**: 返回版本号和数据库连接状态
- ⚡ **极速优化**: 单链接从3秒优化到1.7秒（提升43%）
- 🚀 **性能提升**: 页面加载策略优化，资源过滤增强
- 📈 **稳定性**: 连续测试成功率100%

### v1.0.0
- 初始版本
- 支持批量查询用户数据
- 使用 Scrapy + Playwright 爬取方式
