from typing import Optional, List
from sqlmodel import Field, SQLModel


class CityTemperature(SQLModel, table=True, table_name="citytemperature"):
    __table_args__ = {"extend_existing": True}
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
