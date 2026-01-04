from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Tuple
from services.fusion.kalman_filter import KalmanFilter
import numpy as np

router = APIRouter()

# Store filter instances in memory for simplicity (in prod, use Redis or robust state management)
# Key: vehicle_id, Value: KalmanFilter instance
vehicle_filters = {}

class GeoPoint(BaseModel):
    lat: float
    lon: float

class CorrectionRequest(BaseModel):
    vehicle_id: str
    measurement: GeoPoint

@router.post("/correct", response_model=GeoPoint)
async def correct_position(request: CorrectionRequest):
    """
    Apply Kalman Filter to incoming raw GPS data to reduce noise.
    """
    vid = request.vehicle_id
    
    # Initialize filter if not present
    if vid not in vehicle_filters:
        # Tuning parameters: process_noise depends on vehicle dynamics, measurement_noise on GPS quality
        vehicle_filters[vid] = KalmanFilter(process_noise=0.0001, measurement_noise=0.01)
    
    kf = vehicle_filters[vid]
    
    # Update and predict
    corrected = kf.process([request.measurement.lat, request.measurement.lon])
    
    return GeoPoint(lat=corrected[0], lon=corrected[1])

@router.delete("/reset/{vehicle_id}")
async def reset_filter(vehicle_id: str):
    """
    Reset the filter for a specific vehicle.
    """
    if vehicle_id in vehicle_filters:
        del vehicle_filters[vehicle_id]
        return {"status": "reset", "vehicle_id": vehicle_id}
    raise HTTPException(status_code=404, detail="Vehicle filter not found")
