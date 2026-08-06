from sqlalchemy import Column, Integer, String, Float, DateTime, Date, JSON, func
from datetime import datetime
from app.database import Base

class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Ditambahkan panjang (100)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    demand = Column(Integer, default=0)
    image_url = Column(String(500), nullable=True)

class ScheduledRouteModel(Base):
    __tablename__ = "scheduled_routes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)          # Contoh: "Pengiriman Rute Pusat - Senin"
    delivery_date = Column(Date, nullable=False)         # Tanggal pelaksanaan pengiriman
    assigned_driver = Column(String(100), nullable=True) # Nama driver / user yang bertugas
    status = Column(String(50), default="Scheduled")     # Status: Scheduled, On Progress, Completed

    # Menyimpan seluruh struktur JSON hasil optimasi (array of trips)
    routes_data = Column(JSON, nullable=False)

    created_at = Column(DateTime, server_default=func.now())