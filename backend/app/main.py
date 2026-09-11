from fastapi import FastAPI
from app.auth_routes import router as auth_router
from app.quiz import router as quiz_router

app = FastAPI(title="Adaptive Learning Platform API")

app.include_router(auth_router)
app.include_router(quiz_router)


@app.get("/")
def health_check():
    return {"status": "running"}