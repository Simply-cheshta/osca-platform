from fastapi import FastAPI, Header, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from typing import Optional
from sqlalchemy.orm import Session


from app.core.database import engine, Base, get_db
import app.models.issue as issue_model
from app.models.issue import BookmarkedIssue
from app.schemas.bookmark import BookmarkCreate

from app.services.github_client import GitHubClient
from app.services.vector_service import VectorService

Base.metadata.create_all(bind=engine)

MOCK_GITHUB_ISSUES = [
    {
        "id": 1,
        "title": "Build dynamic user dashboard using React and Tailwind",
        "description": "We need an engineer to design a highly interactive frontend data management UI with responsive components.",
        "labels": ["frontend", "react", "ui"],
        "html_url": "https://github.com/example/repo/issues/1"
    },
    {
        "id": 2,
        "title": "Optimize slow database indexing and raw SQL pipelines",
        "description": "Refactor nested PostgreSQL transactions, tune connection pools, and design efficient background caching layers.",
        "labels": ["backend", "postgres", "database"],
        "html_url": "https://github.com/example/repo/issues/2"
    },
    {
        "id": 3,
        "title": "Train custom text classification models for user tags",
        "description": "Implement data pipeline to vectorize incoming issue text using numpy and cluster semantic tags automatically.",
        "labels": ["data-science", "python", "machine-learning"],
        "html_url": "https://github.com/example/repo/issues/3"
    }
]

app = FastAPI(title="OSCA Platform API")
vector_service = VectorService()

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Globally intercepts unhandled operational exceptions across all endpoints
    and wraps them into a clean, safe JSON payload response.
    """
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "Client Error", "detail": exc.detail}
        )

    return JSONResponse(
      status_code=500,
      content={
          "error": "Internal Server Error",
          "detail": "An unexpected error occurred within the platform matching systems.",
          "system_message": str(exc)
      }
  )


@app.get("/")
def read_root():
    return {"message": "OSCA Platform Backend Engine is running smoothly"}

@app.get("/api/recommendations")
async def get_recommendations(profile_bio: str, language: Optional[str] = None, authorization: str = Header(None)):
    """
    Takes a developer bio, fetches live issues from GitHub, and uses the 
    local ML model to score and sort recommendations based on semantic meaning.
    Optional: Filters incoming issues by matching language tags.
    """
    token = authorization.split(" ")[1] if authorization and " " in authorization else authorization
    
    if token:
        client = GitHubClient(access_token=token)
        live_issues = await client.fetch_live_issues(query_label="good-first-issue")
    else:
        live_issues = []

    if not live_issues:
        live_issues = MOCK_GITHUB_ISSUES

    if language:
        target_lang = language.lower()
        filtered_pool = []
        for issue in live_issues:
            labels_text = " ".join([l.lower() for l in issue.get("labels", [])])
            combined_text = f"{issue['title']} {issue['description']} {labels_text}".lower()
            
            if target_lang in combined_text:
                filtered_pool.append(issue)
        live_issues = filtered_pool

    scored_issues = []
    for issue in live_issues:
        score = vector_service.calculate_similarity(
            vector_service.get_embedding(profile_bio),
            vector_service.get_embedding(f"{issue['title']} {issue['description']}")
        )
        
        issue_copy = issue.copy()
        issue_copy["match_score"] = round(score * 100, 2)
        scored_issues.append(issue_copy)

    scored_issues.sort(key=lambda x: x["match_score"], reverse=True)

    return {"recommendations": scored_issues}

@app.post("/api/bookmarks", status_code=201)
async def create_bookmark(bookmark: BookmarkCreate, db: Session = Depends(get_db)):
    """
    Saves an open-source issue to the local SQLite database so the developer 
    can reference or work on it later.
    """
    existing = db.query(BookmarkedIssue).filter(BookmarkedIssue.github_issue_id == bookmark.github_issue_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="This issue is already bookmarked.")

    db_bookmark = BookmarkedIssue(
        github_issue_id=bookmark.github_issue_id,
        title=bookmark.title,
        description=bookmark.description,
        labels=bookmark.labels,
        html_url=bookmark.html_url
    )
    
    db.add(db_bookmark)
    db.commit()
    db.refresh(db_bookmark)
    
    return {"message": "Issue successfully bookmarked!", "bookmark_id": db_bookmark.id}
@app.get("/api/bookmarks")
async def get_bookmarks(db: Session = Depends(get_db)):
    """
    Queries the local SQLite database and returns a complete list of 
    all open-source issues saved by the contributor.
    """
    bookmarks = db.query(BookmarkedIssue).all()
    
    formatted_bookmarks = []
    for item in bookmarks:
        formatted_bookmarks.append({
            "id": item.id,
            "github_issue_id": item.github_issue_id,
            "title": item.title,
            "description": item.description,
            "labels": item.labels.split(",") if item.labels else [],
            "html_url": item.html_url
        })
        
    return {"bookmarked_issues": formatted_bookmarks}