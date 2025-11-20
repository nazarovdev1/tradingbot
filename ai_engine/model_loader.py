import os
import numpy as np
from pathlib import Path
from typing import List, Tuple

from tensorflow.keras.models import load_model


class ModelLoader:
    """
    Loads and manages the AI model
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path or Path(__file__).resolve().parent.parent / 'models' / 'model.h5'
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """
        Load the trained model from file
        """
        if os.path.exists(self.model_path):
            try:
                self.model = load_model(self.model_path)
                print(f"AI Model loaded successfully from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}. Using fallback mode.")
                self.model = None
        else:
            print(f"Model file not found at {self.model_path}. Using fallback mode.")
            self.model = None
    
    def get_model(self):
        """
        Return the loaded model
        """
        return self.model


class FeatureBuilder:
    """
    Builds features for the AI model from price data
    """
    
    def __init__(self):
        pass
    
    def build_features(self, closes: List[float], sequence_length: int = 20) -> np.ndarray:
        """
        Build features for the AI model from closing prices
        """
        if len(closes) < sequence_length:
            # Pad with zeros if not enough data
            padded_closes = [0.0] * (sequence_length - len(closes)) + closes
        else:
            padded_closes = closes[-sequence_length:]
        
        # Normalize the data
        closes_array = np.array(padded_closes, dtype=np.float32)
        mean = float(closes_array.mean())
        std = float(closes_array.std()) or 1.0
        normalized = (closes_array - mean) / std
        
        # Reshape for LSTM input (batch_size, timesteps, features)
        return normalized.reshape(1, sequence_length, 1)


class AIPredictor:
    """
    Makes predictions using the AI model
    """
    
    def __init__(self, model_loader: ModelLoader):
        self.model_loader = model_loader
    
    def predict(self, closes: List[float]) -> Tuple[str, float, float]:
        """
        Make a prediction using the AI model
        Returns: (signal, confidence, raw_prediction)
        """
        model = self.model_loader.get_model()
        
        if model is None:
            # Fallback: return neutral with random prediction
            raw_prediction = np.random.normal(0, 0.1)
        else:
            try:
                features = FeatureBuilder().build_features(closes)
                raw_prediction = float(model.predict(features, verbose=0).squeeze())
            except Exception as e:
                print(f"Failed to run AI prediction: {e}")
                raw_prediction = np.random.normal(0, 0.1)
        
        signal = self.map_prediction_to_signal(raw_prediction)
        confidence = min(1.0, abs(raw_prediction))
        
        return signal, confidence, raw_prediction
    
    def map_prediction_to_signal(self, prediction: float) -> str:
        """
        Map the raw prediction to a trading signal
        """
        if prediction > 0.6:
            return 'BUY'
        elif prediction < -0.6:
            return 'SELL'
        else:
            return 'NEUTRAL'