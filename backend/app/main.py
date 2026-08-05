from fastapi import FastAPI

app = FastAPI(title="Adaptive Learning Platform API")

@app.get("/")
def health_check():
    return {"status": "running"}