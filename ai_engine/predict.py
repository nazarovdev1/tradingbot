from typing import List, Dict
from .model_loader import AIPredictor, ModelLoader


class PredictionEngine:
    """
    Main interface for the AI prediction system
    """
    
    def __init__(self, model_path: str = None):
        self.model_loader = ModelLoader(model_path)
        self.ai_predictor = AIPredictor(self.model_loader)
    
    def get_prediction(self, closes: List[float]) -> dict:
        """
        Get prediction from the AI model
        """
        signal, confidence, raw_prediction = self.ai_predictor.predict(closes)
        
        return {
            'signal': signal,
            'confidence': confidence,
            'raw_prediction': raw_prediction
        }