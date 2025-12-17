#!/bin/bash

API_URL="${1:-http://localhost:8888}"

echo "=== 测试用户管理 API ==="
echo ""

echo "1. 创建用户"
curl -X POST ${API_URL}/users \
  -H "Content-Type: application/json" \
  -d '{"account": "test_user_001", "track": "美妆"}' | python3 -m json.tool

echo ""
echo "2. 查询所有用户"
curl -X GET ${API_URL}/users | python3 -m json.tool

echo ""
echo "3. 根据账号查询"
curl -X GET ${API_URL}/users/account/test_user_001 | python3 -m json.tool

echo ""
echo "4. 更新用户赛道"
curl -X PUT ${API_URL}/users/1 \
  -H "Content-Type: application/json" \
  -d '{"track": "时尚"}' | python3 -m json.tool

echo ""
echo "5. 健康检查（包含数据库状态）"
curl -X GET ${API_URL}/health | python3 -m json.tool

