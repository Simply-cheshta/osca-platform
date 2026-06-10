from fastapi import Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.core.migrations import run_sqlite_migrations
from app.models import agent_run, issue, user  # noqa: F401
from app.schemas.bookmark import BookmarkCreate

Base.metadata.create_all(bind=engine)
run_sqlite_migrations()

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def read_root():
    return {
        "message": f"{settings.APP_NAME} Online",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/api/recommendations")
async def legacy_recommendations(
    profile_bio: str,
    language: str | None = None,
    db: Session = Depends(get_db),
):
    from app.api.v1.recommendations import get_recommendations

    return await get_recommendations(
        profile_bio=profile_bio, language=language, current_user=None, db=db
    )


@app.post("/api/bookmarks", status_code=201)
async def legacy_create_bookmark(
    bookmark: BookmarkCreate,
    db: Session = Depends(get_db),
):
    from app.api.v1.bookmarks import create_bookmark

    return await create_bookmark(bookmark=bookmark, db=db, current_user=None)


@app.get("/api/bookmarks")
async def legacy_get_bookmarks(db: Session = Depends(get_db)):
    from app.api.v1.bookmarks import get_bookmarks

    return await get_bookmarks(db=db, current_user=None)
