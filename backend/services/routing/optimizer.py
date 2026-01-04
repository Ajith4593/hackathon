from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database.models import Vehicle, LocationTracking, Route
from database.redis_manager import redis_manager
import requests
import os
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

OSRM_URL = os.getenv("OSRM_URL", "http://router.project-osrm.org")

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    vehicle_id: Optional[int] = None

class RouteResponse(BaseModel):
    geometry: str
    distance: float
    duration: float
    steps: List[dict]

@router.post("/optimize", response_model=RouteResponse)
async def get_optimized_route(request: RouteRequest):
    """
    Get an optimized route from A to B using OSRM.
    In a real system, this would also consider real-time traffic data from our DB.
    """
    # Build OSRM query
    coordinates = f"{request.start_lon},{request.start_lat};{request.end_lon},{request.end_lat}"
    url = f"{OSRM_URL}/route/v1/driving/{coordinates}?overview=full&geometries=polyline&steps=true"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["code"] != "Ok":
            raise HTTPException(status_code=400, detail="Could not calculate route")
            
        route = data["routes"][0]
        
        return RouteResponse(
            geometry=route["geometry"],
            distance=route["distance"],
            duration=route["duration"],
            steps=route["legs"][0]["steps"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/traffic/{vehicle_id}")
async def get_traffic_context(vehicle_id: int, db: Session = Depends(get_db_session)):
    """
    Look up recent traffic reports near the vehicle's current location.
    """
    location = redis_manager.get_vehicle_location(vehicle_id)
    if not location:
        raise HTTPException(status_code=404, detail="Vehicle location not found in cache")
    
    # In a full implementation, we would use PostGIS to find traffic_data records 
    # within N meters of point(location['longitude'], location['latitude'])
    
    return {"message": "Traffic context retrieval not fully implemented yet", "vehicle_location": location}
