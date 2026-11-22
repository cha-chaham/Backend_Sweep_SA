# ⚙️ Logistik Palu — Backend Optimization & REST API

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![REST API](https://img.shields.io/badge/REST_API-JSON-blue?style=for-the-badge)

A Python backend service and custom mathematical optimization engine built to solve the **Multi-Trip Capacitated Vehicle Routing Problem with Time Windows (MT-CVRPTW)**. Built completely from scratch without third-party solver libraries or paid routing APIs, it powers daily delivery route optimization for perishable goods (**UMKM Air Tahu Gurih**).

---

## ✨ Key Features

### 1. From-Scratch Hybrid VRP Optimization Engine (`vrp_engine.py`)
* **Haversine Distance Matrix Pre-Computation:** Automatically calculates great-circle distances ($R = 6371.0\text{ km}$) between the central depot and all active customer coordinates, caching them into an $O(1)$ lookup matrix to accelerate thousands of optimization iterations.
* **Polar-Angle Spatial Clustering (Sweep Algorithm):** Groups retail outlets into geographically isolated delivery clusters using `math.atan2(d_lat, d_lon)` relative to the depot while strictly enforcing the **50-bottle maximum fleet capacity** per trip.
* **Multi-Trip Route Refinement (Simulated Annealing):** Optimizes visit sequences using calibrated hyperparameters ($T_0 = 1000$, $\alpha = 0.99$, $T_{\text{final}} = 0.001$) and dual neighborhood operators (**Intra-Route Swap** & **Inter-Route Swap**) with the Metropolis acceptance criterion to escape local optima.

### 2. Strict Operational & Perishability Validation
* **Hard Capacity Constraint:** Guarantees zero vehicle overload across every generated trip ($\text{Load} \le 50\text{ bottles}$).
* **Shelf-Life Time Window Validation:** Automatically calculates cumulative travel time ($30\text{ km/h}$ average speed) plus unloading service time ($10\text{ mins/stop}$) to ensure every trip finishes well within the **120-minute room-temperature spoilage limit**.
* **Centralized Business Rules:** Locks core operational parameters (depot coordinates, fleet capacity, average speed, and spoilage threshold) securely on the backend while accepting dynamic daily customer lists and order quantities from the frontend.

### 3. Automated Navigation Deep-Link Generator
* **Zero Paid Maps API Dependency:** Dynamically constructs ready-to-use **Google Maps Directions URLs** (`https://www.google.com/maps/dir/?api=1...`) populated with ordered `waypoints` for each trip, enabling instant turn-by-turn courier navigation on mobile devices.

### 4. Customer Master Management & Smart URL Parser
* **Full CRUD Operations:** RESTful endpoints (`GET`, `POST`, `PUT`, `DELETE`) to manage partner retail stores, default demand volumes, and store location photos.
* **Google Maps Link Coordinate Extractor:** Automatically parses and extracts `latitude` and `longitude` coordinates directly from pasted Google Maps share URLs when registering new stores.

---

## 📂 Project Structure

```text
backend/
├── vrp_engine.py           # Core Hybrid Sweep & Simulated Annealing engine
├── main.py                 # FastAPI routes, request validation, & CORS setup
├── models.py               # Database schemas & ORM models
├── database.py             # Database connection & session management
├── utils.py                # Google Maps URL coordinate parser & helpers
└── requirements.txt        # Python package dependencies
