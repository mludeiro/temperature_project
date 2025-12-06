from fastapi import FastAPI

app = FastAPI(title="Temperature API", description="FastAPI + SQLModel + Pandas + Celery ETL API")

@app.get("/")
async def root():
    return {"message": "Temperature API is running", "status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

