#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tiktok_scraper.database.models import engine, Track
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.tiktok_scraper.database.db import SessionLocal

def complete_migration():
    db = SessionLocal()
    try:
        print("完成迁移...")
        
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
            
            if not track_map:
                default_track = db.query(Track).first()
                if not default_track:
                    default_track = Track(name="默认赛道")
                    db.add(default_track)
                    db.commit()
                    db.refresh(default_track)
                track_map[""] = default_track.id
                print(f"✓ 使用默认赛道 (ID: {default_track.id})")
        
        with engine.connect() as conn:
            for track_name, track_id in track_map.items():
                if track_name:
                    conn.execute(
                        text("UPDATE users SET track_id = :track_id WHERE track = :track_name AND (track_id IS NULL OR track_id = 0)"),
                        {"track_id": track_id, "track_name": track_name}
                    )
                else:
                    conn.execute(
                        text("UPDATE users SET track_id = :track_id WHERE (track IS NULL OR track = '') AND (track_id IS NULL OR track_id = 0)"),
                        {"track_id": track_id}
                    )
            conn.commit()
            print("✓ 更新 track_id 值")
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE track_id IS NULL OR track_id = 0"))
            null_count = result.scalar()
            if null_count > 0:
                default_track_id = list(track_map.values())[0]
                conn.execute(text("UPDATE users SET track_id = :track_id WHERE track_id IS NULL OR track_id = 0"), {"track_id": default_track_id})
                conn.commit()
                print(f"✓ 为 {null_count} 条记录设置默认 track_id")
        
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users MODIFY track_id INT NOT NULL"))
                conn.commit()
                print("✓ 设置 track_id 为 NOT NULL")
            except Exception as e:
                if "already" in str(e).lower():
                    print("✓ track_id 已为 NOT NULL")
                else:
                    raise
        
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users ADD CONSTRAINT fk_user_track FOREIGN KEY (track_id) REFERENCES tracks(id)"))
                conn.commit()
                print("✓ 添加外键约束")
            except Exception as e:
                if "Duplicate" in str(e) or "already exists" in str(e).lower():
                    print("✓ 外键约束已存在")
                else:
                    raise
        
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users DROP COLUMN track"))
                conn.commit()
                print("✓ 删除旧的 track 字段")
            except Exception as e:
                if "doesn't exist" in str(e).lower() or "Unknown column" in str(e):
                    print("✓ track 字段已删除")
                else:
                    raise
        
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
    complete_migration()
