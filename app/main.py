from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List
from sqlmodel import Field, SQLModel, Session, create_engine, select
import pandas as pd
import os
from datetime import datetime
from .celery_app import celery
from .config import DATABASE_URL, DATA_DIR

app = FastAPI(title="Temperature API", description="FastAPI + SQLModel + Pandas + Celery ETL API")

# Database setup
engine = create_engine(DATABASE_URL)


# Models
class CityTemperature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    city: str
    year: int
    avg_temperature: float


class CityTemperatureRead(SQLModel):
    id: int
    city: str
    year: int
    avg_temperature: float


class ETLResponse(SQLModel):
    status: str
    task_id: str


class ETLStatusResponse(SQLModel):
    status: str
    task_id: str
    result: Optional[str] = None
    error: Optional[str] = None


class TemperatureListResponse(SQLModel):
    page: int
    total_pages: int
    data: List[CityTemperatureRead]


# Create tables
def init_db():
    SQLModel.metadata.create_all(engine)


# Basic endpoints
@app.get("/")
async def root():
    return {"message": "Temperature API is running", "status": "ok"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Upload CSV endpoint
@app.post("/datasets", response_model=ETLResponse)
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and trigger ETL process"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"temperature_data_{timestamp}.csv"
    filepath = os.path.join(DATA_DIR, filename)
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Save file
    with open(filepath, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Trigger ETL task
    task = celery.send_task('process_temperature_data', args=[filepath])
    
    return ETLResponse(status="enqueued", task_id=task.id)


@app.get("/etl/status/{task_id}", response_model=ETLStatusResponse)
async def get_etl_status(task_id: str):
    """Get the status of an ETL task"""
    task = celery.AsyncResult(task_id)
    
    status = task.state
    result = None
    error = None
    
    if task.state == 'SUCCESS':
        result = str(task.result)
    elif task.state == 'FAILURE':
        error = str(task.result)
    
    return ETLStatusResponse(status=status, task_id=task_id, result=result, error=error)


@app.get("/temperatures", response_model=TemperatureListResponse)
async def get_temperatures(
    page: int = Query(1, ge=1),
    city: Optional[str] = Query(None),
    year: Optional[int] = Query(None)
):
    """Get paginated temperature data with optional filters"""
    page_size = 20
    offset = (page - 1) * page_size
    
    with Session(engine) as session:
        query = select(CityTemperature)
        
        # Apply filters
        if city:
            query = query.where(CityTemperature.city.ilike(f"%{city}%"))
        if year:
            query = query.where(CityTemperature.year == year)
        
        # Get total count
        count_query = select(CityTemperature)
        if city:
            count_query = count_query.where(CityTemperature.city.ilike(f"%{city}%"))
        if year:
            count_query = count_query.where(CityTemperature.year == year)
        
        total_count = len(session.exec(count_query).all())
        total_pages = (total_count + page_size - 1) // page_size
        
        # Get paginated results
        query = query.offset(offset).limit(page_size)
        results = session.exec(query).all()
        
        data = [CityTemperatureRead(**result.dict()) for result in results]
        
        return TemperatureListResponse(
            page=page,
            total_pages=total_pages,
            data=data
        )


@app.get("/temperatures/{temperature_id}", response_model=CityTemperatureRead)
async def get_temperature_by_id(temperature_id: int):
    """Get a specific temperature record by ID"""
    with Session(engine) as session:
        temperature = session.get(CityTemperature, temperature_id)
        if not temperature:
            raise HTTPException(status_code=404, detail="Temperature record not found")
        
        return CityTemperatureRead(**temperature.dict())


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
