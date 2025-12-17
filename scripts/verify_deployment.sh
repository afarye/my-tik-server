#!/bin/bash

echo "======================================"
echo "TikTok Scraper 部署验证脚本 v1.1.0"
echo "======================================"
echo ""

API_URL="${1:-http://localhost:8000}"
PASSED=0
FAILED=0

check_test() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
        PASSED=$((PASSED + 1))
    else
        echo "❌ $1"
        FAILED=$((FAILED + 1))
    fi
}

echo "1️⃣  检查服务健康状态..."
HEALTH=$(curl -s "${API_URL}/health" 2>/dev/null)
echo "$HEALTH" | grep -q '"status":"ok"'
check_test "健康检查"

echo ""
echo "2️⃣  检查版本信息..."
echo "$HEALTH" | grep -q '"version":"1.1.0"'
check_test "版本验证 (v1.1.0)"

echo ""
echo "3️⃣  检查CORS配置..."
CORS=$(curl -s -I -X OPTIONS "${API_URL}/health" \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: GET" 2>/dev/null)
echo "$CORS" | grep -qi "access-control-allow-origin"
check_test "CORS跨域支持"

echo ""
echo "4️⃣  测试参数验证..."
EMPTY=$(curl -s -X POST "${API_URL}/crawl_scrapy" \
  -H "Content-Type: application/json" \
  -d '{"urls": []}' 2>/dev/null)
echo "$EMPTY" | grep -q "urls cannot be empty"
check_test "空URL验证"

echo ""
echo "5️⃣  测试API响应格式..."
RESPONSE=$(curl -s -X POST "${API_URL}/crawl_scrapy" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.tiktok.com/@test"]}' 2>/dev/null)
echo "$RESPONSE" | grep -q '"success"'
check_test "API响应格式"

echo ""
echo "6️⃣  测试字段完整性..."
echo "$RESPONSE" | grep -q '"username"' && \
echo "$RESPONSE" | grep -q '"followers"' && \
echo "$RESPONSE" | grep -q '"video_count"'
check_test "响应字段完整性 (包含video_count)"

echo ""
echo "7️⃣  测试异常处理（无效URL）..."
ERROR_RESP=$(curl -s -X POST "${API_URL}/crawl_scrapy" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://invalid"]}' 2>/dev/null)
echo "$ERROR_RESP" | grep -q '"success":true'
check_test "异常处理不崩溃"

echo ""
echo "======================================"
echo "测试结果汇总"
echo "======================================"
echo "通过: ${PASSED}"
echo "失败: ${FAILED}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 所有测试通过！服务部署成功！"
    exit 0
else
    echo "⚠️  部分测试失败，请检查日志"
    exit 1
fi

