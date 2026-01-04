from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database.models import Vehicle, Anomaly
from database.redis_manager import redis_manager
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class AnomalyReport(BaseModel):
    vehicle_id: int
    anomaly_type: str
    severity: str
    description: str
    latitude: float
    longitude: float

@router.post("/detect")
async def report_anomaly(report: AnomalyReport, db: Session = Depends(get_db_session)):
    """
    Receive or manually report an anomaly.
    In real-time, this would be triggered by our Isolation Forest monitoring loop.
    """
    new_anomaly = Anomaly(
        vehicle_id=report.vehicle_id,
        anomaly_type=report.anomaly_type,
        severity=report.severity,
        description=report.description,
        status="active"
    )
    
    db.add(new_anomaly)
    db.commit()
    
    # Increment Redis counter
    redis_manager.increment_anomaly_count(report.vehicle_id)
    
    # Notify via pub/sub (the websocket in api_gateway handles this if we push to 'vehicle:updates:all')
    redis_manager.publish_location_update(report.vehicle_id, {
        "alert": report.anomaly_type,
        "severity": report.severity,
        "description": report.description
    })
    
    return {"status": "Anomaly logged and broadcasted"}

@router.get("/active/{vehicle_id}")
async def get_active_alerts(vehicle_id: int, db: Session = Depends(get_db_session)):
    """Get all active alerts for a vehicle."""
    alerts = db.query(Anomaly).filter(
        Anomaly.vehicle_id == vehicle_id,
        Anomaly.status == "active"
    ).all()
    
    return alerts
