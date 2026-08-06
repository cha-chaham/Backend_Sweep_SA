from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form, Header, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv

from app.database import engine, get_db, Base
from app.models.models import CustomerModel
from app.models.schemas import CustomerUpdate, OptimizationResponse, Customer, CustomerCreate, CustomerUpdateSingle
from app.services.vrp_engine import VRPEngine
from app.services.datastore import DEPOT, INITIAL_CUSTOMERS
from app.services.gmaps_parser import parse_google_maps_url

# Inisialisasi tabel database
Base.metadata.create_all(bind=engine)
load_dotenv()  # Memuat variabel lingkungan dari file .env

app = FastAPI(
    title="VRP API - Air Tahu Gurih Palu",
    description="REST API Vehicle Routing Problem dengan MySQL & SQLAlchemy",
    version="1.1.0"
)

ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static" / "images"

STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# KONFIGURASI CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Izinkan origin frontend Vite
    allow_credentials=True,
    allow_methods=["*"],  # Izinkan semua metode (GET, POST, PUT, DELETE, dll)
    allow_headers=["*"],  # Izinkan semua headers
)

from fastapi import Header, HTTPException, status

def verify_admin_role(x_admin_passcode: str = Header(None, alias="x-admin-passcode")):
    # Debugging: Cek apa yang benar-benar diterima oleh backend
    print(f"DEBUG - Header x-admin-passcode yang diterima: {x_admin_passcode}")
    print(f"DEBUG - Passcode di ENV: {ADMIN_PASSCODE}")

    if not x_admin_passcode or x_admin_passcode != ADMIN_PASSCODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak. Passcode Admin salah atau tidak valid."
        )
    return True

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

# @app.get("/")
# def read_root():
#     return {"message": "Sistem VRP Air Tahu Gurih Palu Aktif dengan MySQL", "docs": "/docs"}

# GET ALL CUSTOMERS
@app.get("/api/customers", response_model=List[Customer], tags=["Customer Management"])
def get_all_customers(db: Session = Depends(get_db)):
    """
    Mendapatkan seluruh data pelanggan dari database.
    """
    customers = db.query(CustomerModel).all()
    return customers

# GET CUSTOMER BY NAME (SEARCH)
@app.get("/api/customers/search", tags=["Customer Management"])
def search_customers(name: str, db: Session = Depends(get_db)):
    """
    Mendapatkan data pelanggan tertentu berdasarkan nama.
    """
    customers = db.query(CustomerModel).filter(CustomerModel.name.ilike(f"%{name}%")).all()
    return customers

# GET CUSTOMER BY ID
@app.get("/api/customers/{customer_id}", response_model=Customer, tags=["Customer Management"])
def get_customer_by_id(customer_id: int, db: Session = Depends(get_db)):
    """
    Mendapatkan data pelanggan tertentu berdasarkan ID.
    """
    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Data pelanggan tidak ditemukan.")
    return customer


@app.put("/api/customers/{customer_id}", response_model=Customer, tags=["Customer Management"])
def update_single_customer(customer_id: int, payload: CustomerUpdateSingle, db: Session = Depends(get_db), isAdmin: str = Depends(verify_admin_role)):
    """
    Memperbarui data pelanggan tertentu berdasarkan ID.
    """
    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan.")

    # Perbarui hanya field yang dikirimkan (tidak kosong/None)
    if payload.name is not None:
        customer.name = payload.name
    if payload.lat is not None:
        customer.lat = payload.lat
    if payload.lon is not None:
        customer.lon = payload.lon
    if payload.demand is not None:
        customer.demand = payload.demand
    if payload.image_url is not None:
        customer.image_url = payload.image_url

    db.commit()
    db.refresh(customer)
    return customer

@app.delete("/api/customers/{customer_id}", tags=["Customer Management"])
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    isAdmin: str = Depends(verify_admin_role)):

    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan.")

    # Hapus file gambar fisik dari server jika ada
    if customer.image_url:
        # Konversi path relatif database (/static/images/xxx.jpg) menjadi path absolut server
        old_file_path = BASE_DIR / customer.image_url.lstrip("/")
        if old_file_path.exists():
            old_file_path.unlink() # Menghapus file fisik

    db.delete(customer)
    db.commit()
    return {"status": "success", "message": f"Pelanggan dengan ID {customer_id} dan fotonya berhasil dihapus."}

@app.post("/api/customers", response_model=Customer, tags=["Customer Management"])
async def create_customer(
    name: str = Form(...),
    gmaps_link: str = Form(...),
    demand: int = Form(...),
    image: UploadFile = File(None),  # Menerima file gambar opsional
    db: Session = Depends(get_db),
    isAdmin: str = Depends(verify_admin_role)  # Memeriksa hak akses Admin
):
    # Ekstrak koordinat dari link Google Maps
    lat, lon = parse_google_maps_url(gmaps_link)
    if lat is None or lon is None:
        raise HTTPException(
            status_code=400,
            detail="Gagal mengekstrak koordinat dari link Google Maps."
        )

    image_path = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"

        # Simpan menggunakan path absolut yang pasti benar
        file_path = STATIC_DIR / filename

        contents = await image.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        # Path yang disimpan ke database (relatif untuk diakses browser)
        image_path = f"/static/images/{filename}"

    db_item = CustomerModel(
        name=name,
        lat=lat,
        lon=lon,
        demand=demand,
        image_url=image_path
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

# 3. Endpoint POST: Menjalankan optimasi VRP
@app.post("/api/optimize", tags=["Optimization"])
def run_optimization(db: Session = Depends(get_db)):
    """
    Menjalankan optimasi Sweep dan Simulated Annealing.
    """
    # Ambil seluruh data pelanggan langsung dari database (Get All Customers)
    db_customers = db.query(CustomerModel).all()

    if not db_customers:
        raise HTTPException(status_code=400, detail="Data pelanggan di database kosong.")

    # Inisialisasi engine VRP dengan data dari database
    vrp = VRPEngine(db_customers)
    result = vrp.run_optimization()

    return result