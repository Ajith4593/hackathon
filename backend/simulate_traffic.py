
import asyncio
import aiohttp
import random
import time
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000/api/v1"
HUBS = [
    {'name': 'Mumbai', 'lat': 19.0760, 'lng': 72.8777},
    {'name': 'Delhi', 'lat': 28.6139, 'lng': 77.2090},
    {'name': 'Bangalore', 'lat': 12.9716, 'lng': 77.5946},
    {'name': 'Chennai', 'lat': 13.0827, 'lng': 80.2707},
    {'name': 'Kolkata', 'lat': 22.5726, 'lng': 88.3639},
    {'name': 'Hyderabad', 'lat': 17.3850, 'lng': 78.4867},
    {'name': 'Ahmedabad', 'lat': 23.0225, 'lng': 72.5714}
]

VEHICLES = []

def generate_initial_fleet():
    """Generates a static list of vehicles across hubs."""
    fleet = []
    id_counter = 100
    
    for hub in HUBS:
        # Create 5 vehicles per hub
        for i in range(5):
            fleet.append({
                'vehicle_id': id_counter,
                'vehicle_number': f"IND-{hub['name'][:2].upper()}-{id_counter}",
                'lat': hub['lat'] + (random.random() - 0.5) * 0.05,
                'lng': hub['lng'] + (random.random() - 0.5) * 0.05,
                'speed': random.randint(30, 80),
                'direction': random.uniform(0, 360),
                'status': 'active'
            })
            id_counter += 1
    return fleet

async def register_vehicles(session, fleet):
    """(Optional) In a real app, we'd register these vehicles first. 
       For this demo, we assume the system accepts telemetry for any ID 
       or we might get 404s if validation is strict. 
       
       NOTE: The current ingestion service checks `db.query(Vehicle)...`.
       So we MUST assume these vehicles exist in the DB.
       
       Since we can't easily seed the SQL DB from here without direct access,
       we will assume the User has a seeded DB or we just simulate the 'Movement' 
       and hope the backend validation ignores non-existent vehicles 
       OR we use a 'bulk' endpoint if it auto-creates.
       
       *Looking at ingestion/service.py*: It DOES check `Vehicle` existence.
       
       Workaround: We will just log what we are sending. 
       If 404s occur, the user needs to seed the DB.
    """
    pass

async def simulate_movement(fleet):
    async with aiohttp.ClientSession() as session:
        print(f"🚀 Starting traffic simulation for {len(fleet)} vehicles...")
        
        while True:
            tasks = []
            for v in fleet:
                # Update position (simple random walk)
                v['lat'] += (random.random() - 0.5) * 0.001
                v['lng'] += (random.random() - 0.5) * 0.001
                v['speed'] = max(0, min(100, v['speed'] + (random.random() - 0.5) * 5))
                v['direction'] = (v['direction'] + (random.random() - 0.5) * 10) % 360
                
                payload = {
                    "vehicle_id": v['vehicle_id'],
                    "latitude": v['lat'],
                    "longitude": v['lng'],
                    "speed": v['speed'],
                    "direction": v['direction'],
                    "accuracy": 5.0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send telemetry
                tasks.append(post_telemetry(session, payload))
            
            # Send in batches
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r == True)
            print(f"📡 Sent {success_count}/{len(fleet)} updates. (If 0, check if vehicles exist in DB)")
            
            await asyncio.sleep(2) # Update every 2 seconds

async def post_telemetry(session, payload):
    try:
        async with session.post(f"{API_URL}/ingestion/telemetry", json=payload) as resp:
            if resp.status == 201:
                return True
            else:
                # print(f"Failed to send for {payload['vehicle_id']}: {resp.status}")
                return False
    except Exception as e:
        print(f"Connection error: {e}")
        return False

if __name__ == "__main__":
    VEHICLES = generate_initial_fleet()
    try:
        asyncio.run(simulate_movement(VEHICLES))
    except KeyboardInterrupt:
        print("🛑 Simulation stopped.")
