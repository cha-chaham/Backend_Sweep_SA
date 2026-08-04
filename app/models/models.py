from sqlalchemy import Column, Integer, String, Float, DateTime, Text
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

class OptimizationHistoryModel(Base):
    __tablename__ = "optimization_history"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    total_trips = Column(Integer)
    summary_data = Column(Text) if hasattr(Base, 'Text') else Column(String(1000)) # Diubah menjadi String dengan panjang (1000) atau Text