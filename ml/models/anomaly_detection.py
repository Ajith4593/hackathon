from sklearn.ensemble import IsolationForest
import numpy as np
import joblib
import os

class AnomalyDetector:
    """
    Anomaly detection for vehicle behavior using Isolation Forest.
    Features: [speed_deviation, route_deviation, acceleration, braking_force]
    """
    def __init__(self, contamination=0.05):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.scaler = None
        
    def train(self, X):
        """Train the model with normal driving data."""
        self.model.fit(X)
        
    def predict(self, x):
        """
        Predict if a data point is an anomaly.
        Returns: -1 for anomaly, 1 for normal
        """
        return self.model.predict(x)

    def save(self, path='ml/models/saved/anomaly_model.joblib'):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        print(f"✅ Anomaly model saved to {path}")

def train_demo_detector():
    """Train a demo detector with some synthetic data."""
    print("⚠️ Training demo Isolation Forest for anomaly detection...")
    
    # Synthetic normal data: low speed, steady movement
    normal = np.random.normal(0, 0.1, (100, 4))
    
    detector = AnomalyDetector()
    detector.train(normal)
    detector.save()

if __name__ == "__main__":
    train_demo_detector()
