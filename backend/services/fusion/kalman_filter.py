import numpy as np

class KalmanFilter:
    """
    A simple 2D Kalman Filter for smoothing GPS coordinates (Latitude, Longitude).
    State vector: [lat, lon, v_lat, v_lon]
    Measurement vector: [lat, lon]
    """
    def __init__(self, process_noise=0.001, measurement_noise=0.001):
        # Time step (constant for simplicity, can be dynamic)
        self.dt = 1.0
        
        # State transition matrix (A)
        self.A = np.array([
            [1, 0, self.dt, 0],
            [0, 1, 0, self.dt],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # Measurement matrix (H)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # Process noise covariance (Q)
        self.Q = np.eye(4) * process_noise
        
        # Measurement noise covariance (R)
        self.R = np.eye(2) * measurement_noise
        
        # Error covariance matrix (P)
        self.P = np.eye(4)
        
        # Initial state (x)
        self.x = np.zeros(4)
        self.initialized = False

    def predict(self):
        """Predict the next state."""
        self.x = np.dot(self.A, self.x)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        return self.x[:2]

    def update(self, measurement):
        """Update the state with a new measurement."""
        z = np.array(measurement)
        
        if not self.initialized:
            self.x[:2] = z
            self.x[2:] = 0 # Assume zero initial velocity
            self.initialized = True
            return self.x[:2]
        
        # Kalman gain (K)
        S = np.dot(np.dot(self.H, self.P), self.H.T) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))
        
        # Innovation (y)
        y = z - np.dot(self.H, self.x)
        
        # Updated state (x)
        self.x = self.x + np.dot(K, y)
        
        # Updated error covariance (P)
        I = np.eye(4)
        self.P = np.dot(I - np.dot(K, self.H), self.P)
        
        return self.x[:2]

    def process(self, measurement):
        """Predict and update in one step."""
        self.predict()
        return self.update(measurement)
