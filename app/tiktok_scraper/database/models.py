from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from pytz import timezone
import os

def dubai_now():
    """获取迪拜当前时间"""
    dubai_tz = timezone('Asia/Dubai')
    return datetime.now(dubai_tz)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/tiktok_db?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True, nullable=False, comment="赛道名称")
    description = Column(String(500), nullable=True, comment="赛道描述")
    created_at = Column(DateTime, default=dubai_now, comment="创建时间")
    updated_at = Column(DateTime, default=dubai_now, onupdate=dubai_now, comment="更新时间")
    
    users = relationship("User", back_populates="track_rel")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    account = Column(String(255), unique=True, index=True, nullable=False, comment="用户账号")
    track_id = Column(Integer, ForeignKey("tracks.id"), nullable=False, index=True, comment="赛道ID")
    url = Column(String(500), nullable=True, comment="完整链接")
    sec_user_id = Column(String(255), nullable=True, comment="Sec User ID")
    region = Column(String(100), nullable=True, comment="地区")
    tags = Column(JSON, nullable=True, comment="标签")
    created_at = Column(DateTime, default=dubai_now, comment="创建时间")
    updated_at = Column(DateTime, default=dubai_now, onupdate=dubai_now, comment="更新时间")
    
    track_rel = relationship("Track", back_populates="users")

class UserHistory(Base):
    __tablename__ = "user_history"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(String(500), nullable=False, index=True, comment="用户URL")
    username = Column(String(255), nullable=True, comment="用户名")
    following = Column(String(50), nullable=True, comment="关注数")
    followers = Column(String(50), nullable=True, comment="粉丝数")
    likes = Column(String(50), nullable=True, comment="点赞数")
    video_count = Column(String(50), nullable=True, comment="视频数")
    videos = Column(JSON, nullable=True, comment="视频信息")
    user_info = Column(JSON, nullable=True, comment="用户详细信息")
    created_at = Column(DateTime, default=dubai_now, comment="入库时间")
    
    __table_args__ = (
        {"comment": "用户历史记录表"},
    )

def init_db():
    Base.metadata.create_all(bind=engine)

