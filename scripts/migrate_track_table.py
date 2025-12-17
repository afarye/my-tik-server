#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tiktok_scraper.database.models import engine, Track, User
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.tiktok_scraper.database.db import SessionLocal

def migrate():
    db = SessionLocal()
    try:
        print("开始迁移赛道表...")
        
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tracks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE COMMENT '赛道名称',
                    description VARCHAR(500) NULL COMMENT '赛道描述',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_name (name)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='赛道表'
            """))
            conn.commit()
            print("✓ 创建 tracks 表")
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DISTINCT track FROM users WHERE track IS NOT NULL AND track != ''"))
            tracks = [row[0] for row in result]
            
            track_map = {}
            for track_name in tracks:
                existing = db.query(Track).filter(Track.name == track_name).first()
                if not existing:
                    track = Track(name=track_name)
                    db.add(track)
                    db.commit()
                    db.refresh(track)
                    track_map[track_name] = track.id
                    print(f"✓ 创建赛道: {track_name} (ID: {track.id})")
                else:
                    track_map[track_name] = existing.id
                    print(f"✓ 赛道已存在: {track_name} (ID: {existing.id})")
        
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN track_id INT NULL AFTER track"))
                conn.commit()
                print("✓ 添加 track_id 字段")
            except Exception as e:
                if "Duplicate column name" in str(e):
                    print("✓ track_id 字段已存在")
                else:
                    raise
        
        with engine.connect() as conn:
            for track_name, track_id in track_map.items():
                conn.execute(
                    text("UPDATE users SET track_id = :track_id WHERE track = :track_name"),
                    {"track_id": track_id, "track_name": track_name}
                )
            conn.commit()
            print("✓ 更新 track_id 值")
        
        with engine.connect() as conn:
            conn.execute(text("UPDATE users SET track_id = 1 WHERE track_id IS NULL"))
            conn.commit()
            print("✓ 为 NULL 的 track_id 设置默认值")
        
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users MODIFY track_id INT NOT NULL"))
            conn.commit()
            print("✓ 设置 track_id 为 NOT NULL")
        
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users ADD CONSTRAINT fk_user_track FOREIGN KEY (track_id) REFERENCES tracks(id)"))
                conn.commit()
                print("✓ 添加外键约束")
            except Exception as e:
                if "Duplicate key name" in str(e) or "already exists" in str(e):
                    print("✓ 外键约束已存在")
                else:
                    raise
        
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users DROP COLUMN track"))
            conn.commit()
            print("✓ 删除旧的 track 字段")
        
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users DROP INDEX IF EXISTS idx_track"))
            conn.commit()
            print("✓ 删除旧的 track 索引")
        
        print("\n迁移完成！")
        
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
