#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tiktok_scraper.database.models import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN region VARCHAR(100) NULL COMMENT '地区' AFTER sec_user_id"))
        conn.commit()
        print("成功添加 region 字段")
except Exception as e:
    if "Duplicate column name" in str(e) or "already exists" in str(e):
        print("region 字段已存在")
    else:
        print(f"错误: {e}")
        sys.exit(1)

