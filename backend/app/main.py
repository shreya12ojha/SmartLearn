from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth_routes import router as auth_router
from app.quiz import router as quiz_router
from app.assessment_routes import router as assessment_router

app = FastAPI(title="Adaptive Learning Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(quiz_router)
app.include_router(assessment_router)


@app.get("/")
def health_check():
    return {"status": "running"}