#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tiktok_scraper.database.models import init_db, engine
from sqlalchemy import text

def init_tables():
    print("开始初始化数据库表...")
    try:
        init_db()
        print("✓ 数据库表创建成功")
        
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            print(f"✓ 当前数据库中的表: {', '.join(tables)}")
            
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"  - {table}: {count} 条记录")
        
        print("\n数据库初始化完成！")
    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    init_tables()
