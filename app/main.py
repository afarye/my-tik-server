from fastapi import FastAPI, HTTPException, Depends, APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from typing import List, Optional, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
import asyncio
import sys
import os
import subprocess
import tempfile
import json as _json
import logging
import traceback
import httpx
from dotenv import load_dotenv

from app.tiktok_scraper.database.models import User, Track, UserHistory, init_db
from app.tiktok_scraper.database.db import get_db

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="TikTok Scraper API", version="1.4.0")
api_router = APIRouter(prefix="/api")

@app.on_event("startup")
async def startup_event():
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CrawlRequest(BaseModel):
    urls: List[str]
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    wait_time: Optional[float] = 2.0

    @validator('urls')
    def validate_urls(cls, v):
        if not v or len(v) == 0:
            raise ValueError('urls cannot be empty')
        if len(v) > 50:
            raise ValueError('maximum 50 urls per request')
        return v

class TrackCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TrackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class TrackResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_count: Optional[int] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    account: str
    track_id: int
    url: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[Any] = None

class UserUpdate(BaseModel):
    track_id: Optional[int] = None
    url: Optional[str] = None
    sec_user_id: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[Any] = None

class UpdateSecUserIdRequest(BaseModel):
    url: str
    sec_user_id: str

class UserHistoryCreate(BaseModel):
    url: str
    username: Optional[str] = None
    following: Optional[str] = None
    followers: Optional[str] = None
    likes: Optional[str] = None
    video_count: Optional[str] = None
    videos: Optional[List[Dict[str, Any]]] = None
    user_info: Optional[Dict[str, Any]] = None

class UserResponse(BaseModel):
    id: int
    account: str
    track_id: int
    track_name: Optional[str] = None
    url: Optional[str] = None
    sec_user_id: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[Any] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class UserHistoryResponse(BaseModel):
    id: int
    url: str
    username: Optional[str] = None
    following: Optional[str] = None
    followers: Optional[str] = None
    likes: Optional[str] = None
    video_count: Optional[str] = None
    videos: Optional[List[Dict[str, Any]]] = None
    user_info: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True

@app.get("/health")
async def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "version": "1.2.0",
        "database": db_status
    }

@api_router.post("/crawl_scrapy")
async def crawl_scrapy(request: CrawlRequest, db: Session = Depends(get_db)):
    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="scrapy_run_")
        output_json = os.path.join(tmpdir, "tiktok_result.json")
        
        urls_arg = ",".join(request.urls)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        app_dir = os.path.join(project_root, "app")
        scrapy_cfg_path = os.path.join(app_dir, "scrapy.cfg")
        
        if not os.path.exists(scrapy_cfg_path):
            with open(scrapy_cfg_path, "w") as f:
                f.write("[settings]\n")
                f.write("default = tiktok_scraper.settings\n\n")
                f.write("[deploy]\n")
                f.write("project = tiktok_scraper\n")
        
        cmd = [
            sys.executable, "-m", "scrapy", "crawl", "tiktok",
            "-a", f"urls={urls_arg}",
            "-a", f"start_date={request.start_date or ''}",
            "-a", f"end_date={request.end_date or ''}",
            "-o", output_json,
            "-s", f"SCRAPY_SETTINGS_MODULE=tiktok_scraper.settings"
        ]
        
        logger.info(f"Starting crawl for {len(request.urls)} URLs")
        
        def run_cmd():
            try:
                env = {**os.environ, "PYTHONUNBUFFERED": "1"}
                env["PYTHONPATH"] = f"{app_dir}:{env.get('PYTHONPATH', '')}"
                return subprocess.run(
                    cmd, 
                    cwd=app_dir, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    timeout=300,
                    env=env
                )
            except subprocess.TimeoutExpired as e:
                logger.error(f"Scrapy timeout: {e}")
                raise
            except Exception as e:
                logger.error(f"Subprocess error: {e}")
                raise
        
        proc = await asyncio.to_thread(run_cmd)
        
        if proc.returncode != 0:
            stderr = proc.stderr.decode(errors="ignore")
            logger.error(f"Scrapy error (exit {proc.returncode}): {stderr[:500]}")
            return {
                "success": False, 
                "error": f"Scraping failed (exit code {proc.returncode})",
                "details": stderr[:200] if stderr else "Unknown error"
            }
        
        if not os.path.exists(output_json):
            logger.error("Output file not found")
            return {"success": False, "error": "Output file not created"}
        
        try:
            with open(output_json, "r", encoding="utf-8") as f:
                data = _json.load(f)
            
            if not isinstance(data, list):
                data = [data] if data else []
            
            for item in data:
                try:
                    history = UserHistory(
                        url=item.get("url", ""),
                        username=item.get("username"),
                        following=item.get("following"),
                        followers=item.get("followers"),
                        likes=item.get("likes"),
                        video_count=item.get("video_count"),
                        videos=item.get("videos"),
                        user_info=item.get("user_info")
                    )
                    db.add(history)
                except Exception as e:
                    logger.error(f"Error saving history: {e}")
            
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"Error committing history: {e}")
            
            logger.info(f"Successfully crawled {len(data)} results")
            return {"success": True, "results": data, "count": len(data)}
            
        except _json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {"success": False, "error": "Invalid JSON output"}
        except Exception as e:
            logger.error(f"File read error: {e}")
            return {"success": False, "error": f"Failed to read results: {str(e)}"}
            
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        return {"success": False, "error": "Request timeout after 300 seconds"}
    except Exception as e:
        logger.error(f"Unexpected error: {traceback.format_exc()}")
        return {
            "success": False, 
            "error": "Internal server error",
            "details": str(e)[:200]
        }
    finally:
        if tmpdir:
            try:
                import shutil
                await asyncio.to_thread(shutil.rmtree, tmpdir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Cleanup error: {e}")

@api_router.post("/tracks", response_model=TrackResponse)
async def create_track(track: TrackCreate, db: Session = Depends(get_db)):
    try:
        existing_track = db.query(Track).filter(Track.name == track.name).first()
        if existing_track:
            raise HTTPException(status_code=400, detail="Track name already exists")
        
        db_track = Track(name=track.name, description=track.description)
        db.add(db_track)
        db.commit()
        db.refresh(db_track)
        
        return TrackResponse(
            id=db_track.id,
            name=db_track.name,
            description=db_track.description,
            user_count=0,
            created_at=db_track.created_at.isoformat(),
            updated_at=db_track.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating track: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tracks", response_model=List[TrackResponse])
async def get_tracks(
    skip: int = 0,
    limit: int = 100,
    name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Track)
        
        if name:
            query = query.filter(Track.name.like(f"%{name}%"))
        
        tracks = query.offset(skip).limit(limit).all()
        
        result = []
        for track in tracks:
            user_count = db.query(User).filter(User.track_id == track.id).count()
            result.append(TrackResponse(
                id=track.id,
                name=track.name,
                description=track.description,
                user_count=user_count,
                created_at=track.created_at.isoformat(),
                updated_at=track.updated_at.isoformat()
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error getting tracks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tracks/{track_id}", response_model=TrackResponse)
async def get_track(track_id: int, db: Session = Depends(get_db)):
    try:
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        user_count = db.query(User).filter(User.track_id == track_id).count()
        
        return TrackResponse(
            id=track.id,
            name=track.name,
            description=track.description,
            user_count=user_count,
            created_at=track.created_at.isoformat(),
            updated_at=track.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting track: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/tracks/{track_id}", response_model=TrackResponse)
async def update_track(track_id: int, track_update: TrackUpdate, db: Session = Depends(get_db)):
    try:
        db_track = db.query(Track).filter(Track.id == track_id).first()
        if not db_track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        if track_update.name is not None:
            existing = db.query(Track).filter(Track.name == track_update.name, Track.id != track_id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Track name already exists")
            db_track.name = track_update.name
        if track_update.description is not None:
            db_track.description = track_update.description
        
        db.commit()
        db.refresh(db_track)
        
        user_count = db.query(User).filter(User.track_id == track_id).count()
        
        return TrackResponse(
            id=db_track.id,
            name=db_track.name,
            description=db_track.description,
            user_count=user_count,
            created_at=db_track.created_at.isoformat(),
            updated_at=db_track.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating track: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/tracks/{track_id}")
async def delete_track(track_id: int, db: Session = Depends(get_db)):
    try:
        db_track = db.query(Track).filter(Track.id == track_id).first()
        if not db_track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        user_count = db.query(User).filter(User.track_id == track_id).count()
        if user_count > 0:
            raise HTTPException(status_code=400, detail=f"Cannot delete track with {user_count} users. Please reassign users first.")
        
        db.delete(db_track)
        db.commit()
        
        return {"success": True, "message": "Track deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting track: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tracks/{track_id}/users", response_model=List[UserResponse])
async def get_track_users(
    track_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        track = db.query(Track).filter(Track.id == track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        users = db.query(User).filter(User.track_id == track_id).offset(skip).limit(limit).all()
        
        return [
            UserResponse(
                id=u.id,
                account=u.account,
                track_id=u.track_id,
                track_name=track.name,
                url=u.url,
                sec_user_id=u.sec_user_id,
                region=u.region,
                tags=u.tags,
                created_at=u.created_at.isoformat(),
                updated_at=u.updated_at.isoformat()
            )
            for u in users
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting track users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing_user = db.query(User).filter(User.account == user.account).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="User account already exists")
        
        track = db.query(Track).filter(Track.id == user.track_id).first()
        if not track:
            raise HTTPException(status_code=404, detail="Track not found")
        
        db_user = User(
            account=user.account,
            track_id=user.track_id,
            url=user.url,
            region=user.region,
            tags=user.tags
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return UserResponse(
            id=db_user.id,
            account=db_user.account,
            track_id=db_user.track_id,
            track_name=track.name,
            url=db_user.url,
            sec_user_id=db_user.sec_user_id,
            region=db_user.region,
            tags=db_user.tags,
            created_at=db_user.created_at.isoformat(),
            updated_at=db_user.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    account: Optional[str] = None,
    track_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    try:
        query = db.query(User)
        
        if account:
            query = query.filter(User.account.like(f"%{account}%"))
        if track_id:
            query = query.filter(User.track_id == track_id)
        
        users = query.offset(skip).limit(limit).all()
        
        result = []
        for u in users:
            track = db.query(Track).filter(Track.id == u.track_id).first()
            result.append(UserResponse(
                id=u.id,
                account=u.account,
                track_id=u.track_id,
                track_name=track.name if track else None,
                url=u.url,
                sec_user_id=u.sec_user_id,
                region=u.region,
                tags=u.tags,
                created_at=u.created_at.isoformat(),
                updated_at=u.updated_at.isoformat()
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/users/{user_id:int}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        track = db.query(Track).filter(Track.id == user.track_id).first()
        
        return UserResponse(
            id=user.id,
            account=user.account,
            track_id=user.track_id,
            track_name=track.name if track else None,
            url=user.url,
            sec_user_id=user.sec_user_id,
            region=user.region,
            tags=user.tags,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user_update.track_id is not None:
            track = db.query(Track).filter(Track.id == user_update.track_id).first()
            if not track:
                raise HTTPException(status_code=404, detail="Track not found")
            db_user.track_id = user_update.track_id
        if user_update.url is not None:
            db_user.url = user_update.url
        if user_update.sec_user_id is not None:
            db_user.sec_user_id = user_update.sec_user_id
        if user_update.region is not None:
            db_user.region = user_update.region
        if user_update.tags is not None:
            db_user.tags = user_update.tags
        
        db.commit()
        db.refresh(db_user)
        
        track = db.query(Track).filter(Track.id == db_user.track_id).first()
        
        return UserResponse(
            id=db_user.id,
            account=db_user.account,
            track_id=db_user.track_id,
            track_name=track.name if track else None,
            url=db_user.url,
            sec_user_id=db_user.sec_user_id,
            region=db_user.region,
            tags=db_user.tags,
            created_at=db_user.created_at.isoformat(),
            updated_at=db_user.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(db_user)
        db.commit()
        
        return {"success": True, "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/users/account/{account}", response_model=UserResponse)
async def get_user_by_account(account: str, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.account == account).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        track = db.query(Track).filter(Track.id == user.track_id).first()
        
        return UserResponse(
            id=user.id,
            account=user.account,
            track_id=user.track_id,
            track_name=track.name if track else None,
            url=user.url,
            sec_user_id=user.sec_user_id,
            region=user.region,
            tags=user.tags,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user by account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/users/account/{account}")
async def delete_user_by_account(account: str, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.account == account).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(db_user)
        db.commit()
        
        return {"success": True, "message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user by account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/history-user", response_model=List[UserHistoryResponse])
async def get_user_history(
    url: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        history = db.query(UserHistory).filter(
            UserHistory.url == url
        ).order_by(
            UserHistory.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        return [
            UserHistoryResponse(
                id=h.id,
                url=h.url,
                username=h.username,
                following=h.following,
                followers=h.followers,
                likes=h.likes,
                video_count=h.video_count,
                videos=h.videos,
                user_info=h.user_info,
                created_at=h.created_at.isoformat()
            )
            for h in history
        ]
    except Exception as e:
        logger.error(f"Error getting user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/history-user", response_model=UserHistoryResponse)
async def create_user_history(history: UserHistoryCreate, db: Session = Depends(get_db)):
    try:
        db_history = UserHistory(
            url=history.url,
            username=history.username,
            following=history.following,
            followers=history.followers,
            likes=history.likes,
            video_count=history.video_count,
            videos=history.videos,
            user_info=history.user_info
        )
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        
        return UserHistoryResponse(
            id=db_history.id,
            url=db_history.url,
            username=db_history.username,
            following=db_history.following,
            followers=db_history.followers,
            likes=db_history.likes,
            video_count=db_history.video_count,
            videos=db_history.videos,
            user_info=db_history.user_info,
            created_at=db_history.created_at.isoformat()
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 兼容旧路径 /api/user-history
@api_router.get("/user-history", response_model=List[UserHistoryResponse])
async def get_user_history_legacy(
    url: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """兼容旧路径的GET接口"""
    return await get_user_history(url=url, skip=skip, limit=limit, db=db)

@api_router.post("/user-history", response_model=UserHistoryResponse)
async def create_user_history_legacy(history: UserHistoryCreate, db: Session = Depends(get_db)):
    """兼容旧路径的POST接口"""
    return await create_user_history(history=history, db=db)

@app.put("/api/update-sec-id", response_model=UserResponse)
async def update_sec_user_id(request: UpdateSecUserIdRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.url == request.url).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found with the given URL")
        
        user.sec_user_id = request.sec_user_id
        db.commit()
        db.refresh(user)
        
        track = db.query(Track).filter(Track.id == user.track_id).first()
        
        return UserResponse(
            id=user.id,
            account=user.account,
            track_id=user.track_id,
            track_name=track.name if track else None,
            url=user.url,
            sec_user_id=user.sec_user_id,
            region=user.region,
            tags=user.tags,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating sec_user_id: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/proxy/get-sec-user-id")
async def get_sec_user_id(url: str = Query(..., description="TikTok用户URL")):
    """转发请求到TikHub API获取sec_user_id"""
    tikhub_token = os.getenv("TIKHUB_TOKEN")
    if not tikhub_token:
        raise HTTPException(status_code=500, detail="TIKHUB_TOKEN环境变量未配置")
    
    tikhub_url = f"https://api.tikhub.io/api/v1/tiktok/web/get_sec_user_id?url={url}"
    headers = {
        "Authorization": f"Bearer {tikhub_token}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(tikhub_url, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"TikHub API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"TikHub API错误: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail=f"请求错误: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"未知错误: {str(e)}")

@api_router.get("/proxy/fetch-user-post-videos")
async def fetch_user_post_videos(
    sec_user_id: str = Query(..., description="用户sec_user_id"),
    unique_id: Optional[str] = Query(None, description="用户unique_id"),
    max_cursor: Optional[int] = Query(None, description="分页游标"),
    count: Optional[int] = Query(None, description="获取数量"),
    sort_type: Optional[int] = Query(None, description="排序类型")
):
    """转发请求到TikHub API获取主页视频数据"""
    tikhub_token = os.getenv("TIKHUB_TOKEN")
    if not tikhub_token:
        raise HTTPException(status_code=500, detail="TIKHUB_TOKEN环境变量未配置")
    
    params = {"sec_user_id": sec_user_id}
    if unique_id:
        params["unique_id"] = unique_id
    if max_cursor is not None:
        params["max_cursor"] = max_cursor
    if count is not None:
        params["count"] = count
    if sort_type is not None:
        params["sort_type"] = sort_type
    
    tikhub_url = "https://api.tikhub.io/api/v1/tiktok/app/v3/fetch_user_post_videos_v3"
    headers = {
        "Authorization": f"Bearer {tikhub_token}"
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(tikhub_url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"TikHub API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=f"TikHub API错误: {e.response.text}")
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail=f"请求错误: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"未知错误: {str(e)}")

app.include_router(api_router)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {traceback.format_exc()}")
    return {
        "success": False,
        "error": "Internal server error",
        "details": str(exc)[:200]
    }
