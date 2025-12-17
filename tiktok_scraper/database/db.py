from sqlalchemy.orm import Session
from tiktok_scraper.database.models import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

