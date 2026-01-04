from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from geoalchemy2.elements import WKTElement

from database.connection import get_db_session
from database.models import Vehicle, LocationTracking
from database.influx_schema import influx_manager
from database.redis_manager import redis_manager
from backend.services.fusion.kalman_filter import KalmanFilter

# Dictionary to store Kalman Filter instances per vehicle (in-memory for demo)
# In production, this would be persisted to Redis or a state service
kf_storage = {}

router = APIRouter()


class TelemetryData(BaseModel):
    """Schema for incoming vehicle telemetry data."""
    vehicle_id: int
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = Field(None, ge=0)
    direction: Optional[float] = Field(None, ge=0, le=360)
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    acceleration: Optional[float] = None
    fuel_level: Optional[float] = Field(None, ge=0, le=100)
    timestamp: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "vehicle_id": 1,
                "latitude": 19.0760,
                "longitude": 72.8777,
                "speed": 45.5,
                "direction": 180.0,
                "accuracy": 5.0,
                "altitude": 14.0,
                "timestamp": "2024-01-03T12:00:00Z"
            }
        }


class BulkTelemetryData(BaseModel):
    """Schema for bulk telemetry data upload."""
    data: list[TelemetryData]


@router.post("/telemetry", status_code=201)
async def ingest_telemetry(
    telemetry: TelemetryData,
    db: Session = Depends(get_db_session)
):
    """
    Ingest vehicle GPS and sensor telemetry data.
    
    This endpoint receives real-time location and sensor data from vehicles,
    stores it in both PostgreSQL (for queries) and InfluxDB (for time-series analysis),
    and publishes updates to Redis for real-time tracking.
    """
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == telemetry.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle {telemetry.vehicle_id} not found")
    
    # Use current time if timestamp not provided
    timestamp = telemetry.timestamp or datetime.utcnow()
    
    # Create PostGIS POINT geometry
    # point_wkt = f'POINT({telemetry.longitude} {telemetry.latitude})'
    
    # 🧠 Position Correction using Kalman Filter
    if telemetry.vehicle_id not in kf_storage:
        kf_storage[telemetry.vehicle_id] = KalmanFilter()
    
    kf = kf_storage[telemetry.vehicle_id]
    smoothed_pos = kf.process([telemetry.latitude, telemetry.longitude])
    smoothed_lat, smoothed_lon = smoothed_pos[0], smoothed_pos[1]
    
    point_wkt = f'POINT({smoothed_lon} {smoothed_lat})'
    
    # Store in PostgreSQL
    location_record = LocationTracking(
        vehicle_id=telemetry.vehicle_id,
        position=WKTElement(point_wkt, srid=4326),
        latitude=smoothed_lat,
        longitude=smoothed_lon,
        speed=telemetry.speed,
        direction=telemetry.direction,
        accuracy=telemetry.accuracy,
        altitude=telemetry.altitude,
        timestamp=timestamp
    )
    
    db.add(location_record)
    db.commit()
    db.refresh(location_record)
    
    # Store in InfluxDB for time-series analysis
    influx_data = {
        'latitude': telemetry.latitude,
        'longitude': telemetry.longitude,
        'speed': telemetry.speed or 0,
        'direction': telemetry.direction or 0,
        'accuracy': telemetry.accuracy or 0,
        'altitude': telemetry.altitude or 0,
        'timestamp': timestamp
    }
    
    if telemetry.acceleration is not None:
        influx_data['acceleration'] = telemetry.acceleration
    if telemetry.fuel_level is not None:
        influx_data['fuel_level'] = telemetry.fuel_level
    
    influx_manager.write_telemetry(telemetry.vehicle_id, influx_data)
    
    # Cache latest location in Redis
    location_data = {
        'latitude': telemetry.latitude,
        'longitude': telemetry.longitude,
        'speed': telemetry.speed,
        'direction': telemetry.direction,
        'timestamp': timestamp.isoformat(),
        'vehicle_number': vehicle.vehicle_number
    }
    
    redis_manager.set_vehicle_location(telemetry.vehicle_id, location_data)
    
    # Publish to Redis pub/sub for real-time updates
    redis_manager.publish_location_update(telemetry.vehicle_id, location_data)
    
    return {
        "status": "success",
        "message": "Telemetry data ingested successfully",
        "track_id": location_record.track_id,
        "timestamp": timestamp.isoformat()
    }


@router.post("/telemetry/bulk", status_code=201)
async def ingest_bulk_telemetry(
    bulk_data: BulkTelemetryData,
    db: Session = Depends(get_db_session)
):
    """
    Ingest multiple telemetry records at once.
    Useful for batch uploads or catching up on offline data.
    """
    ingested_count = 0
    errors = []
    
    for telemetry in bulk_data.data:
        try:
            # Verify vehicle exists
            vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == telemetry.vehicle_id).first()
            if not vehicle:
                errors.append(f"Vehicle {telemetry.vehicle_id} not found")
                continue
            
            timestamp = telemetry.timestamp or datetime.utcnow()
            point_wkt = f'POINT({telemetry.longitude} {telemetry.latitude})'
            
            # Store in PostgreSQL
            location_record = LocationTracking(
                vehicle_id=telemetry.vehicle_id,
                position=WKTElement(point_wkt, srid=4326),
                latitude=telemetry.latitude,
                longitude=telemetry.longitude,
                speed=telemetry.speed,
                direction=telemetry.direction,
                accuracy=telemetry.accuracy,
                altitude=telemetry.altitude,
                timestamp=timestamp
            )
            
            db.add(location_record)
            
            # Store in InfluxDB
            influx_data = {
                'latitude': telemetry.latitude,
                'longitude': telemetry.longitude,
                'speed': telemetry.speed or 0,
                'direction': telemetry.direction or 0,
                'accuracy': telemetry.accuracy or 0,
                'altitude': telemetry.altitude or 0,
                'timestamp': timestamp
            }
            
            influx_manager.write_telemetry(telemetry.vehicle_id, influx_data)
            ingested_count += 1
            
        except Exception as e:
            errors.append(str(e))
    
    db.commit()
    
    return {
        "status": "success",
        "ingested_count": ingested_count,
        "total_records": len(bulk_data.data),
        "errors": errors if errors else None
    }


@router.get("/telemetry/history/{vehicle_id}")
async def get_telemetry_history(
    vehicle_id: int,
    hours: int = 24,
    db: Session = Depends(get_db_session)
):
    """
    Get historical telemetry data for a vehicle.
    
    Args:
        vehicle_id: Vehicle identifier
        hours: Number of hours to look back (default: 24)
    """
    # Verify vehicle exists
    vehicle = db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
    
    # Query from InfluxDB for time-series data
    result = influx_manager.query_vehicle_history(vehicle_id, hours)
    
    # Format the response
    history = []
    for table in result:
        for record in table.records:
            history.append({
                'timestamp': record.get_time().isoformat(),
                'field': record.get_field(),
                'value': record.get_value()
            })
    
    return {
        "vehicle_id": vehicle_id,
        "vehicle_number": vehicle.vehicle_number,
        "history": history,
        "hours": hours
    }
