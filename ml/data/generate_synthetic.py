import json
import time
import requests
import random
from datetime import datetime

# API Configuration
API_URL = "http://localhost:8000/api/v1"

def simulate_vehicle(vehicle_id, vehicle_number, start_lat, start_lon):
    """
    Simulate a vehicle moving along a path.
    """
    print(f"🚛 Starting simulation for vehicle {vehicle_number} (ID: {vehicle_id})")
    
    curr_lat = start_lat
    curr_lon = start_lon
    
    # Path increments (moving roughly North-East)
    d_lat = 0.001
    d_lon = 0.001
    
    for i in range(20):
        # Add some random noise to GPS
        noise_lat = random.uniform(-0.0005, 0.0005)
        noise_lon = random.uniform(-0.0005, 0.0005)
        
        payload = {
            "vehicle_id": vehicle_id,
            "latitude": curr_lat + noise_lat,
            "longitude": curr_lon + noise_lon,
            "speed": random.uniform(30, 60),
            "direction": random.uniform(0, 360),
            "accuracy": random.uniform(3, 10),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        try:
            response = requests.post(f"{API_URL}/telemetry", json=payload)
            if response.status_code == 201:
                res_data = response.json()
                print(f"📍 [{vehicle_number}] Step {i+1}: Lat={payload['latitude']:.4f}, Lon={payload['longitude']:.4f} | Smoothed: {res_data.get('track_id')}")
            else:
                print(f"❌ Failed to send telemetry: {response.text}")
        except Exception as e:
            print(f"⚠️ Error: {e}")
        
        # Update position for next step
        curr_lat += d_lat
        curr_lon += d_lon
        
        time.sleep(2) # Send update every 2 seconds

if __name__ == "__main__":
    # Simulate a few vehicles
    # Note: Requires the backend to be running and vehicles to exist in DB
    try:
        simulate_vehicle(1, "MH-01-AB-1234", 19.0760, 72.8777)
    except KeyboardInterrupt:
        print("\n👋 Simulation stopped")
