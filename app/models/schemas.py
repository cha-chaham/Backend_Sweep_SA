from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date

class Customer(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    demand: int = Field(..., ge=0, description="Permintaan botol harian")
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class CustomerUpdate(BaseModel):
    customers: List[Customer]

class CustomerUpdateSingle(BaseModel):
    name: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    demand: Optional[int] = None
    image_url: Optional[str] = None

class CustomerCreate(BaseModel):
    name: str
    demand: int = Field(..., ge=0, description="Permintaan botol harian")
    lat: Optional[float] = None
    lon: Optional[float] = None
    gmaps_link: Optional[str] = None

class RouteDetail(BaseModel):
    trip_id: int
    route: List[str]
    total_demand: int
    total_distance_km: float
    total_time_minutes: float
    is_feasible: bool

class OptimizationResponse(BaseModel):
    status: str
    depot: Dict[str, Any]  # Diubah dari Dict[str, float] ke Dict[str, Any]
    total_trips: int
    routes: List[RouteDetail]

class ScheduledRouteCreate(BaseModel):
    title: str
    delivery_date: date
    assigned_driver: Optional[str] = None
    routes_data: Any  # Menerima seluruh objek hasil VRP (array trips, total jarak, dll)

class ScheduledRouteResponse(ScheduledRouteCreate):
    id: int
    status: str
    created_at: Any

    class Config:
        from_attributes = True

class OptimizationRequest(BaseModel):
    customers: List[CustomerCreate]

class OptimizationItem(BaseModel):
    id: Optional[int] = None
    name: str
    demand: int
    lat: float
    lon: float
    gmaps_link: Optional[str] = None

# Skema Pydantic untuk Validasi Input
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "driver" # default driver

class UserLogin(BaseModel):
    username: str
    password: str