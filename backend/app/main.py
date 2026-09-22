from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth_routes import router as auth_router
from app.quiz import router as quiz_router
from app.assessment_routes import router as assessment_router
from app.path_planning_routes import router as path_planning_router

app = FastAPI(title="Adaptive Learning Platform API")

# Enable CORS for React frontend (Vite default ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(quiz_router)
app.include_router(assessment_router)
app.include_router(path_planning_router)


@app.get("/")
def health_check():
    return {"status": "running"}

