from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db_session
from database.models import Vehicle, Prediction
from database.redis_manager import redis_manager
from pydantic import BaseModel
from datetime import datetime, timedelta
import random 
import math

router = APIRouter()

class ETARequest(BaseModel):
    vehicle_id: int
    destination_lat: float
    destination_lon: float

@router.post("/eta")
async def predict_eta(request: ETARequest, db: Session = Depends(get_db_session)):
    """
    Predict Estimated Time of Arrival.
    This would ideally use a trained LSTM model.
    """
    # Check cache first
    cached = redis_manager.get_cached_prediction(request.vehicle_id, "eta")
    if cached:
        return cached

    # Get current location
    curr_loc = redis_manager.get_vehicle_location(request.vehicle_id)
    if not curr_loc:
        raise HTTPException(status_code=404, detail="Vehicle position unknown")

    # Calculate Haversine distance
    R = 6371  # Earth radius in km
    dlat = math.radians(request.destination_lat - curr_loc['lat'])
    dlon = math.radians(request.destination_lon - curr_loc['lon'])
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(curr_loc['lat'])) * math.cos(math.radians(request.destination_lat)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.asin(math.sqrt(a))
    distance_km = R * c
    
    # Estimate speed (mocked but realistic varies by traffic)
    # Base speed 40 km/h, +/- traffic noise
    avg_speed_kmh = 40.0 * random.uniform(0.8, 1.2)
    
    predicted_hours = distance_km / avg_speed_kmh
    predicted_minutes = int(predicted_hours * 60)
    
    arrival_time = datetime.utcnow() + timedelta(minutes=predicted_minutes)
    
    prediction_data = {
        "distance_km": round(distance_km, 2),
        "avg_speed_kmh": round(avg_speed_kmh, 1),
        "predicted_minutes": predicted_minutes,
        "estimated_arrival": arrival_time.isoformat(),
        "confidence": 0.92 if distance_km < 50 else 0.75
    }

    # Store in cache
    redis_manager.cache_prediction(request.vehicle_id, "eta", prediction_data)
    
    # Store in DB
    new_prediction = Prediction(
        vehicle_id=request.vehicle_id,
        prediction_type="eta",
        predicted_value=prediction_data,
        confidence_score=prediction_data["confidence"],
        valid_until=arrival_time
    )
    db.add(new_prediction)
    db.commit()

    return prediction_data

@router.get("/congestion/{zone_id}")
async def forecast_congestion(zone_id: str):
    """
    Forecast congestion in a specific area.
    """
    return {
        "zone_id": zone_id,
        "forecast": "Moderate",
        "trend": "Increasing",
        "predicted_speed_reduction": "15%"
    }
