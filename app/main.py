from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, get_db, Base
from app.models.models import CustomerModel
from app.models.schemas import CustomerUpdate, OptimizationResponse, Customer, CustomerCreate
from app.services.vrp_engine import VRPEngine
from app.services.datastore import DEPOT, INITIAL_CUSTOMERS
from app.services.gmaps_parser import parse_google_maps_url

# Inisialisasi tabel database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VRP API - Air Tahu Gurih Palu",
    description="REST API Vehicle Routing Problem dengan MySQL & SQLAlchemy",
    version="1.1.0"
)

# KONFIGURASI CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Izinkan origin frontend Vite
    allow_credentials=True,
    allow_methods=["*"],  # Izinkan semua metode (GET, POST, PUT, DELETE, dll)
    allow_headers=["*"],  # Izinkan semua headers
)

@app.on_event("startup")
def startup_event():
    # Seeding data awal jika tabel masih kosong
    db = next(get_db())
    count = db.query(CustomerModel).count()
    if count == 0:
        for c in INITIAL_CUSTOMERS:
            db_item = CustomerModel(**c)
            db.add(db_item)
        db.commit()

@app.get("/")
def read_root():
    return {"message": "Sistem VRP Air Tahu Gurih Palu Aktif dengan MySQL", "docs": "/docs"}

# GET ALL CUSTOMERS
@app.get("/api/customers", response_model=List[Customer])
def get_all_customers(db: Session = Depends(get_db)):
    customers = db.query(CustomerModel).all()
    return customers

# GET CUSTOMER BY NAME (SEARCH)
@app.get("/api/customers/search")
def search_customers(name: str, db: Session = Depends(get_db)):
    customers = db.query(CustomerModel).filter(CustomerModel.name.ilike(f"%{name}%")).all()
    return customers

# GET CUSTOMER BY ID
@app.get("/api/customers/{customer_id}", response_model=Customer)
def get_customer_by_id(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Data pelanggan tidak ditemukan.")
    return customer


# 2. Endpoint PUT: Memperbarui data pelanggan
@app.put("/api/customers")
def update_customers(payload: CustomerUpdate, db: Session = Depends(get_db)):
    db.query(CustomerModel).delete()
    for c in payload.customers:
        db_item = CustomerModel(id=c.id, name=c.name, lat=c.lat, lon=c.lon, demand=c.demand)
        db.add(db_item)
    db.commit()
    return {"status": "success", "message": f"Berhasil memperbarui {len(payload.customers)} data pelanggan ke database."}

# 3. Endpoint POST: Menjalankan optimasi VRP
@app.post("/api/optimize")
def run_optimization(db: Session = Depends(get_db)):
    # Ambil seluruh data pelanggan langsung dari database (Get All Customers)
    db_customers = db.query(CustomerModel).all()

    if not db_customers:
        raise HTTPException(status_code=400, detail="Data pelanggan di database kosong.")

    # Inisialisasi engine VRP dengan data dari database
    vrp = VRPEngine(db_customers)
    result = vrp.run_optimization()

    return result

@app.post("/api/customers", response_model=Customer)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)):
    lat = payload.lat
    lon = payload.lon

    # Jika user memberikan link Google Maps, ekstrak lat & lon secara otomatis
    if payload.gmaps_link:
        parsed_lat, parsed_lon = parse_google_maps_url(payload.gmaps_link)
        if parsed_lat is not None and parsed_lon is not None:
            lat = parsed_lat
            lon = parsed_lon
        else:
            raise HTTPException(
                status_code=400,
                detail="Gagal mengekstrak koordinat dari link Google Maps. Pastikan link valid."
            )

    if lat is None or lon is None:
        raise HTTPException(
            status_code=400,
            detail="Latitude & Longitude atau Link Google Maps wajib diisi."
        )

    db_item = CustomerModel(
        name=payload.name,
        lat=lat,
        lon=lon,
        demand=payload.demand
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item