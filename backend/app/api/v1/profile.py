from fastapi import APIRouter, Header, HTTPException, status
from app.services.github_client import GitHubClient

router = APIRouter(prefix="/profile", tags=["User Profile"])

@router.get("/analyze")
async def analyze_profile(authorization: str = Header(None)):
    """
    Accepts a GitHub Access Token in the request headers, downloads data,
    and calculates baseline developer metrics.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Must use 'Bearer <token>' format."
        )
    
    token = authorization.split(" ")[1]
    github = GitHubClient(token)
    
    user_info = await github.get_user_data()
    repos = await github.get_user_repos()
    
    languages_count = {}
    total_stars = 0
    has_readme = 1 if user_info.get("bio") else 0
    
    for repo in repos:
        total_stars += repo.get("stargazers_count", 0)
        lang = repo.get("language")
        if lang:
            languages_count[lang] = languages_count.get(lang, 0) + 1

    frontend_languages = {"JavaScript", "TypeScript", "HTML", "CSS", "Vue", "Svelte"}
    backend_languages = {"Python", "Java", "Go", "Rust", "Ruby", "C#", "C++", "PHP"}
    
    fe_commits = sum(count for lang, count in languages_count.items() if lang in frontend_languages)
    be_commits = sum(count for lang, count in languages_count.items() if lang in backend_languages)
    total_languages = sum(languages_count.values()) or 1

    frontend_score = round(min((fe_commits / total_languages) * 10, 10.0), 1)
    backend_score = round(min((be_commits / total_languages) * 10, 10.0), 1)
  
    dsa_score = round(min((languages_count.get("C++", 0) + languages_count.get("Java", 0) + languages_count.get("Python", 0)) / total_languages * 7 + 3.0, 10.0), 1)
    
    repo_weight = min(len(repos) * 5, 40)  
    star_weight = min(total_stars * 2, 20)  
    bio_weight = has_readme * 20            
    os_readiness = min(repo_weight + star_weight + bio_weight + 20, 100) 
    
    return {
        "github_username": user_info.get("login"),
        "avatar_url": user_info.get("avatar_url"),
        "public_repos": user_info.get("public_repos"),
        "top_languages": sorted(languages_count, key=languages_count.get, reverse=True)[:3],
        "metrics": {
            "frontend_score": frontend_score,
            "backend_score": backend_score,
            "dsa_score": dsa_score,
            "open_source_readiness": f"{os_readiness}%"
        }
    }