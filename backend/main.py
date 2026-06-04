from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import router as auth_router
from app.api.v1.profile import router as profile_router  

app = FastAPI(
    title="OSCA API",
    description="Backend services for the Open Source Contribution Agent",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")  

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "project": "Open Source Contribution Agent (OSCA)",
        "message": "Backend server is online!"
    }