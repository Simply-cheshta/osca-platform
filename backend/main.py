from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "project": "Open Source Contribution Agent (OSCA)",
        "message": "Backend server is online and running smoothly!"
    }