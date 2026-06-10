import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, encrypt_token
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.github_client import GitHubClient

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/login")
def github_login():
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET.",
        )
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user,repo"
    )
    return RedirectResponse(url=github_url)


@router.get("/callback")
async def github_callback(code: str = None, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code missing.")

    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url, json=payload, headers={"Accept": "application/json"}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed.")
        token_data = response.json()

    if "error" in token_data:
        raise HTTPException(status_code=400, detail=token_data.get("error_description", "OAuth rejected."))

    access_token = token_data.get("access_token")
    github = GitHubClient(access_token)
    user_info = await github.get_user_data()

    user = db.query(User).filter(User.github_id == user_info["id"]).first()
    if not user:
        user = User(
            github_id=user_info["id"],
            github_username=user_info["login"],
        )
        db.add(user)

    user.avatar_url = user_info.get("avatar_url")
    user.bio = user_info.get("bio")
    user.email = user_info.get("email")
    user.access_token_encrypted = encrypt_token(access_token)
    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(user.id, user.github_username)
    base = settings.FRONTEND_URL.rstrip("/")
    sep = "&" if "?" in base else "?"
    redirect_url = f"{base}{sep}token={jwt_token}"
    return RedirectResponse(url=redirect_url)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
