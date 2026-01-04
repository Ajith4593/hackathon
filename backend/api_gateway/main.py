from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json
import asyncio

# ===============================
# Internal imports (FIXED PATHS)
# ===============================
from database.connection import get_db_session
from database.models import Vehicle, LocationTracking
from database.redis_manager import redis_manager

from backend.services.ingestion.service import router as ingestion_router
from backend.services.routing.optimizer import router as routing_router
from backend.services.prediction.service import router as prediction_router
from backend.services.alerts.notification import router as alerts_router
from backend.services.fusion.service import router as fusion_router

# ===============================
# FastAPI App
# ===============================
app = FastAPI(
    title="Vehicle Tracking System API",
    description="High-Precision Position-Based Vehicle Transportation Tracking System",
    version="1.0.0"
)

# ===============================
# CORS
# ===============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# Routers
# ===============================
app.include_router(ingestion_router, prefix="/api/v1", tags=["Data Ingestion"])
app.include_router(routing_router, prefix="/api/v1", tags=["Routing"])
app.include_router(prediction_router, prefix="/api/v1", tags=["Predictions"])
app.include_router(alerts_router, prefix="/api/v1", tags=["Alerts"])
app.include_router(fusion_router, prefix="/api/v1", tags=["Data Fusion"])

# ===============================
# WebSocket Manager
# ===============================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()

# ===============================
# REST ENDPOINTS
# ===============================
@app.get("/")
async def root():
    return {
        "name": "Vehicle Tracking System API",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/v1/vehicles")
def get_all_vehicles(db: Session = Depends(get_db_session)):
    vehicles = db.query(Vehicle).filter(Vehicle.status == "active").all()

    response = []
    for vehicle in vehicles:
        location = redis_manager.get_vehicle_location(vehicle.vehicle_id)

        response.append({
            "vehicle_id": vehicle.vehicle_id,
            "vehicle_number": vehicle.vehicle_number,
            "vehicle_type": vehicle.vehicle_type,
            "status": vehicle.status,
            "latest_location": location
        })

    return response


@app.get("/api/v1/vehicles/{vehicle_id}")
def get_vehicle_details(vehicle_id: int, db: Session = Depends(get_db_session)):
    vehicle = db.query(Vehicle).filter(
        Vehicle.vehicle_id == vehicle_id
    ).first()

    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    location = redis_manager.get_vehicle_location(vehicle_id)

    recent_locations = (
        db.query(LocationTracking)
        .filter(LocationTracking.vehicle_id == vehicle_id)
        .order_by(LocationTracking.timestamp.desc())
        .limit(10)
        .all()
    )

    return {
        "vehicle_id": vehicle.vehicle_id,
        "vehicle_number": vehicle.vehicle_number,
        "vehicle_type": vehicle.vehicle_type,
        "status": vehicle.status,
        "current_location": location,
        "recent_path": [
            {
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "speed": loc.speed,
                "timestamp": loc.timestamp.isoformat()
            }
            for loc in recent_locations
        ]
    }

# ===============================
# WebSocket Endpoint
# ===============================
@app.websocket("/ws/tracking")
async def websocket_tracking(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        redis_manager.subscribe_to_all_vehicles()

        while True:
            message = redis_manager.get_message()

            if message and message["type"] == "message":
                data = json.loads(message["data"])
                await manager.broadcast(data)

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ===============================
# Lifecycle Events
# ===============================
@app.on_event("startup")
async def startup_event():
    print("🚀 Vehicle Tracking System API starting up...")
    print("✅ Database connected")
    print("✅ Redis connected")
    print("✅ WebSocket ready")


@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Shutting down API...")
    redis_manager.close()
