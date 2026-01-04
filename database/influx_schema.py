from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class InfluxDBManager:
    """Manager for InfluxDB time-series data operations."""
    
    def __init__(self):
        self.url = os.getenv('INFLUXDB_URL')
        self.token = os.getenv('INFLUXDB_TOKEN')
        self.org = os.getenv('INFLUXDB_ORG')
        self.bucket = os.getenv('INFLUXDB_BUCKET')
        
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
    
    def write_telemetry(self, vehicle_id: int, data: dict):
        """
        Write vehicle telemetry data to InfluxDB.
        
        Args:
            vehicle_id: Vehicle identifier
            data: Dictionary containing telemetry data (speed, acceleration, etc.)
        """
        point = (
            Point("vehicle_telemetry")
            .tag("vehicle_id", str(vehicle_id))
            .field("speed", float(data.get('speed', 0)))
            .field("latitude", float(data.get('latitude', 0)))
            .field("longitude", float(data.get('longitude', 0)))
            .field("direction", float(data.get('direction', 0)))
            .field("accuracy", float(data.get('accuracy', 0)))
            .field("altitude", float(data.get('altitude', 0)))
            .time(data.get('timestamp', datetime.utcnow()), WritePrecision.NS)
        )
        
        # Add optional fields if present
        if 'acceleration' in data:
            point.field("acceleration", float(data['acceleration']))
        if 'fuel_level' in data:
            point.field("fuel_level", float(data['fuel_level']))
        
        self.write_api.write(bucket=self.bucket, org=self.org, record=point)
    
    def query_vehicle_history(self, vehicle_id: int, hours: int = 24):
        """
        Query vehicle telemetry history.
        
        Args:
            vehicle_id: Vehicle identifier
            hours: Number of hours to look back
            
        Returns:
            Query results as list of records
        """
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{hours}h)
            |> filter(fn: (r) => r["_measurement"] == "vehicle_telemetry")
            |> filter(fn: (r) => r["vehicle_id"] == "{vehicle_id}")
        '''
        
        result = self.query_api.query(org=self.org, query=query)
        return result
    
    def get_average_speed(self, vehicle_id: int, minutes: int = 30):
        """Get average speed for a vehicle over the last N minutes."""
        query = f'''
        from(bucket: "{self.bucket}")
            |> range(start: -{minutes}m)
            |> filter(fn: (r) => r["_measurement"] == "vehicle_telemetry")
            |> filter(fn: (r) => r["vehicle_id"] == "{vehicle_id}")
            |> filter(fn: (r) => r["_field"] == "speed")
            |> mean()
        '''
        
        result = self.query_api.query(org=self.org, query=query)
        
        for table in result:
            for record in table.records:
                return record.get_value()
        return 0.0
    
    def close(self):
        """Close the InfluxDB client connection."""
        self.client.close()


# Global instance
influx_manager = InfluxDBManager()
