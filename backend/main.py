from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.services.vector_service import VectorService

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_service = VectorService()

@app.get("/")
def root():
    return {"status": "online"}

@app.get("/api/recommendations")
def get_recommendations(profile_bio: str):
    if not profile_bio:
        return {"error": "Missing profile_bio"}

    user_embedding = vector_service.get_embedding(profile_bio)
    ranked_issues = []
    
    for issue in MOCK_GITHUB_ISSUES:
        issue_text = f"{issue['title']} {issue['description']}"
        issue_embedding = vector_service.get_embedding(issue_text)
        similarity_score = vector_service.calculate_similarity(user_embedding, issue_embedding)
        
        ranked_issues.append({
            **issue,
            "match_score": round(similarity_score * 100, 2)
        })
    
    ranked_issues.sort(key=lambda x: x["match_score"], reverse=True)
    return {"recommendations": ranked_issues}