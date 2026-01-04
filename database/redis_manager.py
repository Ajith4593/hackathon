import redis
import json
import os
from dotenv import load_dotenv
from typing import Any, Optional

load_dotenv()


class RedisManager:
    """Manager for Redis caching and pub/sub operations."""
    
    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.password = os.getenv('REDIS_PASSWORD')
        
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            password=self.password,
            decode_responses=True
        )
        
        self.pubsub = self.client.pubsub()
    
    def set_vehicle_location(self, vehicle_id: int, location_data: dict, ttl: int = 300):
        """
        Cache latest vehicle location.
        
        Args:
            vehicle_id: Vehicle identifier
            location_data: Location data dictionary
            ttl: Time to live in seconds (default 5 minutes)
        """
        key = f"vehicle:location:{vehicle_id}"
        self.client.setex(key, ttl, json.dumps(location_data))
    
    def get_vehicle_location(self, vehicle_id: int) -> Optional[dict]:
        """Get cached vehicle location."""
        key = f"vehicle:location:{vehicle_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def publish_location_update(self, vehicle_id: int, location_data: dict):
        """
        Publish location update to Redis pub/sub channel.
        
        Args:
            vehicle_id: Vehicle identifier
            location_data: Location data to publish
        """
        channel = f"vehicle:updates:{vehicle_id}"
        self.client.publish(channel, json.dumps(location_data))
        
        # Also publish to global channel
        self.client.publish("vehicle:updates:all", json.dumps({
            'vehicle_id': vehicle_id,
            **location_data
        }))
    
    def subscribe_to_vehicle(self, vehicle_id: int):
        """Subscribe to vehicle location updates."""
        channel = f"vehicle:updates:{vehicle_id}"
        self.pubsub.subscribe(channel)
    
    def subscribe_to_all_vehicles(self):
        """Subscribe to all vehicle updates."""
        self.pubsub.subscribe("vehicle:updates:all")
    
    def get_message(self):
        """Get next message from subscribed channels."""
        return self.pubsub.get_message()
    
    def cache_prediction(self, vehicle_id: int, prediction_type: str, value: Any, ttl: int = 600):
        """
        Cache ML prediction result.
        
        Args:
            vehicle_id: Vehicle identifier
            prediction_type: Type of prediction (eta, congestion, etc.)
            value: Prediction value
            ttl: Time to live in seconds (default 10 minutes)
        """
        key = f"prediction:{prediction_type}:{vehicle_id}"
        self.client.setex(key, ttl, json.dumps(value))
    
    def get_cached_prediction(self, vehicle_id: int, prediction_type: str) -> Optional[Any]:
        """Get cached prediction if available."""
        key = f"prediction:{prediction_type}:{vehicle_id}"
        data = self.client.get(key)
        return json.loads(data) if data else None
    
    def increment_anomaly_count(self, vehicle_id: int):
        """Increment anomaly counter for a vehicle."""
        key = f"anomaly:count:{vehicle_id}"
        self.client.incr(key)
        self.client.expire(key, 86400)  # Expire after 24 hours
    
    def get_anomaly_count(self, vehicle_id: int) -> int:
        """Get anomaly count for a vehicle."""
        key = f"anomaly:count:{vehicle_id}"
        count = self.client.get(key)
        return int(count) if count else 0
    
    def close(self):
        """Close Redis connection."""
        self.client.close()


# Global instance
redis_manager = RedisManager()
