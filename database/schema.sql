-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Vehicles table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id SERIAL PRIMARY KEY,
    vehicle_number VARCHAR(50) UNIQUE NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    owner_id INTEGER,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Location tracking table with spatial data
CREATE TABLE IF NOT EXISTS location_tracking (
    track_id BIGSERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    position GEOMETRY(POINT, 4326) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    speed DOUBLE PRECISION,
    direction DOUBLE PRECISION,
    accuracy DOUBLE PRECISION,
    altitude DOUBLE PRECISION,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index for fast geospatial queries
CREATE INDEX IF NOT EXISTS idx_location_position ON location_tracking USING GIST(position);
CREATE INDEX IF NOT EXISTS idx_location_vehicle_time ON location_tracking(vehicle_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_location_timestamp ON location_tracking USING BRIN(timestamp);

-- Routes table
CREATE TABLE IF NOT EXISTS routes (
    route_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    route_name VARCHAR(100),
    start_location GEOMETRY(POINT, 4326),
    end_location GEOMETRY(POINT, 4326),
    route_geometry GEOMETRY(LINESTRING, 4326),
    distance_km DOUBLE PRECISION,
    estimated_duration_minutes INTEGER,
    traffic_score DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_routes_geometry ON routes USING GIST(route_geometry);
CREATE INDEX IF NOT EXISTS idx_routes_vehicle ON routes(vehicle_id);

-- Traffic data table
CREATE TABLE IF NOT EXISTS traffic_data (
    traffic_id SERIAL PRIMARY KEY,
    road_segment GEOMETRY(LINESTRING, 4326),
    congestion_level VARCHAR(20),
    average_speed DOUBLE PRECISION,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_traffic_segment ON traffic_data USING GIST(road_segment);
CREATE INDEX IF NOT EXISTS idx_traffic_timestamp ON traffic_data USING BRIN(timestamp);

-- Anomalies table
CREATE TABLE IF NOT EXISTS anomalies (
    anomaly_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT,
    location GEOMETRY(POINT, 4326),
    detected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_anomalies_vehicle ON anomalies(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_anomalies_timestamp ON anomalies(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_anomalies_status ON anomalies(status);

-- Predictions table for caching ML predictions
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id SERIAL PRIMARY KEY,
    vehicle_id INTEGER REFERENCES vehicles(vehicle_id),
    prediction_type VARCHAR(50) NOT NULL,
    predicted_value JSONB,
    confidence_score DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_predictions_vehicle ON predictions(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_predictions_type ON predictions(prediction_type);
CREATE INDEX IF NOT EXISTS idx_predictions_valid ON predictions(valid_until);

-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Insert sample vehicles for demo
INSERT INTO vehicles (vehicle_number, vehicle_type, owner_id, status) VALUES
    ('MH-01-AB-1234', 'truck', 1, 'active'),
    ('MH-02-CD-5678', 'van', 1, 'active'),
    ('DL-03-EF-9012', 'truck', 2, 'active'),
    ('KA-04-GH-3456', 'car', 2, 'active'),
    ('TN-05-IJ-7890', 'truck', 3, 'active')
ON CONFLICT (vehicle_number) DO NOTHING;

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for auto-updating timestamps
CREATE TRIGGER update_vehicles_updated_at BEFORE UPDATE ON vehicles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
