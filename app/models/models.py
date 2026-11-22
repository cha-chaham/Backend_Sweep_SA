from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, JSON, func
from datetime import datetime
from app.database import Base

class CustomerModel(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Ditambahkan panjang (100)
    lat = Column(Numeric(10, 8), nullable=False)
    lon = Column(Numeric(10, 8), nullable=False)
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

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="driver") # Pilihan: "admin" atau "driver"