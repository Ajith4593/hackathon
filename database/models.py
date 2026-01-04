from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime

Base = declarative_base()


class Vehicle(Base):
    __tablename__ = 'vehicles'
    
    vehicle_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_number = Column(String(50), unique=True, nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    owner_id = Column(Integer)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    locations = relationship("LocationTracking", back_populates="vehicle", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="vehicle")
    anomalies = relationship("Anomaly", back_populates="vehicle")
    predictions = relationship("Prediction", back_populates="vehicle")


class LocationTracking(Base):
    __tablename__ = 'location_tracking'
    
    track_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id', ondelete='CASCADE'))
    position = Column(Geometry('POINT', srid=4326), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float)
    direction = Column(Float)
    accuracy = Column(Float)
    altitude = Column(Float)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="locations")


class Route(Base):
    __tablename__ = 'routes'
    
    route_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'))
    route_name = Column(String(100))
    start_location = Column(Geometry('POINT', srid=4326))
    end_location = Column(Geometry('POINT', srid=4326))
    route_geometry = Column(Geometry('LINESTRING', srid=4326))
    distance_km = Column(Float)
    estimated_duration_minutes = Column(Integer)
    traffic_score = Column(Float)
    status = Column(String(20), default='planned')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="routes")


class TrafficData(Base):
    __tablename__ = 'traffic_data'
    
    traffic_id = Column(Integer, primary_key=True, autoincrement=True)
    road_segment = Column(Geometry('LINESTRING', srid=4326))
    congestion_level = Column(String(20))
    average_speed = Column(Float)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)


class Anomaly(Base):
    __tablename__ = 'anomalies'
    
    anomaly_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'))
    anomaly_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text)
    location = Column(Geometry('POINT', srid=4326))
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    status = Column(String(20), default='active')
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="anomalies")


class Prediction(Base):
    __tablename__ = 'predictions'
    
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.vehicle_id'))
    prediction_type = Column(String(50), nullable=False)
    predicted_value = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    
    # Relationship
    vehicle = relationship("Vehicle", back_populates="predictions")


class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
