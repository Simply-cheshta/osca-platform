import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/login")
def github_login():
    """
    Step 1: Redirect the user to GitHub's official OAuth authorization window.
    """
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user,repo" 
    )
    return RedirectResponse(url=github_url)

@router.get("/callback")
async def github_callback(code: str = None):
    """
    Step 2: GitHub redirects back here with a temporary authorization string (?code=...).
    We send a secure POST request to exchange it for a functional User Access Token.
    """
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Authorization code missing from callback parameters."
        )

    token_url = "https://github.com/login/oauth/access_token"
    payload = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.GITHUB_REDIRECT_URI
    }
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.post(token_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to communicate with GitHub servers."
            )
            
        token_data = response.json()
        
        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=token_data.get("error_description", "OAuth handshake rejected.")
            )

    access_token = token_data.get("access_token")
    
    return {
        "status": "authenticated",
        "message": "GitHub login handshake successful!",
        "access_token": access_token,
        "scope": token_data.get("scope")
    }