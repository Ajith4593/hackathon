import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

def create_lstm_model(input_shape):
    """
    Create an LSTM model for ETA prediction.
    Input: Sequence of [lat, lon, speed, time_delta]
    Output: Predicted travel time (minutes)
    """
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1) # Travel time in minutes
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def train_mock_model():
    """Generate dummy data and train a mock model for the hackathon demo."""
    print("🚀 Training mock LSTM model for ETA prediction...")
    
    # Generate 1000 sequences of 10 steps each
    n_samples = 1000
    seq_len = 10
    n_features = 4 # lat, lon, speed, hour_of_day
    
    X = np.random.rand(n_samples, seq_len, n_features)
    y = np.random.rand(n_samples, 1) * 60 # 0-60 minutes
    
    model = create_lstm_model((seq_len, n_features))
    model.fit(X, y, epochs=1, verbose=0) # Quick train for demo
    
    # Save model
    os.makedirs('ml/models/saved', exist_ok=True)
    model.save('ml/models/saved/eta_lstm_v1.h5')
    print("✅ LSTM model saved to ml/models/saved/eta_lstm_v1.h5")

if __name__ == "__main__":
    train_mock_model()
