from celery import Celery
from .config import CELERY_BROKER_URL, CELERY_RESULT_BACKEND, DATABASE_URL
from sqlmodel import Session, create_engine
import pandas as pd
import os
from datetime import datetime
from .models import CityTemperature

# Convert async URL to sync URL for SQLModel
SYNC_DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

# Database setup
engine = create_engine(SYNC_DATABASE_URL)

celery = Celery(
    "temperature_project",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery.task(name='process_temperature_data')
def process_temperature_data(file_path: str):
    """Process temperature CSV data using Pandas and save to database"""
    try:
        # Extract: Load CSV with Pandas
        df = pd.read_csv(file_path)
        
        # Transform: Clean and aggregate data
        # Remove rows where temperature is null
        df = df.dropna(subset=['AverageTemperature'])
        
        # Keep only records from after year 1900
        if 'dt' in df.columns:
            df['year'] = pd.to_datetime(df['dt']).dt.year
            df = df[df['year'] > 1900]
        
        # Normalize city names (strip whitespace)
        if 'City' in df.columns:
            df['City'] = df['City'].str.strip()
        
        # Group by city and year, calculate average temperature
        if 'City' in df.columns and 'year' in df.columns and 'AverageTemperature' in df.columns:
            grouped_df = df.groupby(['City', 'year'])['AverageTemperature'].mean().reset_index()
            grouped_df.columns = ['city', 'year', 'avg_temperature']
        else:
            raise ValueError("CSV must contain 'City', 'dt', and 'AverageTemperature' columns")
        
        # Load: Save to database
        with Session(engine) as session:
            for _, row in grouped_df.iterrows():
                city_temp = CityTemperature(
                    city=row['city'],
                    year=int(row['year']),
                    avg_temperature=float(row['avg_temperature'])
                )
                session.add(city_temp)
            
            session.commit()
        
        # Clean up uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return f"Successfully processed {len(grouped_df)} temperature records"
        
    except Exception as e:
        # Clean up uploaded file even if there's an error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise e


@celery.task(name='health_check_task')
def health_check_task():
    """Simple health check task for Celery"""
    return "Celery worker is healthy"