from sqlalchemy.orm import Session
from app.tiktok_scraper.database.models import SessionLocal

def get_db():
    """
    获取数据库会话的依赖注入函数
    
    这是一个生成器函数，用于在FastAPI等Web框架中管理SQLAlchemy数据库会话。
    使用yield语法实现上下文管理器，确保数据库会话的正确创建和清理。
    
    Yields:
        Session: SQLAlchemy数据库会话对象
    
    Returns:
        Generator[Session, None, None]: 生成器，产生数据库会话对象
    
    Usage:
        # 在FastAPI路由中使用
        @app.get("/users/")
        def get_users(db: Session = Depends(get_db)):
            # 在路由函数中使用db会话
            users = db.query(User).all()
            return users
    """
    db = SessionLocal()  # 创建新的数据库会话实例
    try:
        yield db  # 暂停执行，将数据库会话对象返回给调用方
    finally:
        db.close()  # 无论是否发生异常，都会执行会话清理操作