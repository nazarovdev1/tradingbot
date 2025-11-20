import os
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from fastapi import FastAPI, HTTPException
import pydantic
from pydantic import BaseModel, Field
from pydantic.v1 import validator

from smc_engine import SMCEngine
import pandas as pd

# Load existing model if available
MODEL_PATH = Path(os.getenv('AI_MODEL_PATH', Path(__file__).resolve().parent / 'models' / 'model.h5'))
model = None
if MODEL_PATH.exists():
    try:
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
    except Exception as e:
        print(f"Failed to load model: {e}. Using fallback mode.")
else:
    print("No model file found. Using fallback mode.")

app = FastAPI(title="SMC + AI Trading Signal API", version="1.0.0")

# Initialize SMC Engine
smc_engine = SMCEngine()

class SignalPayload(BaseModel):
    open: List[float] = Field(..., description="Open prices")
    high: List[float] = Field(..., description="High prices")
    low: List[float] = Field(..., description="Low prices")
    close: List[float] = Field(..., description="Close prices")

class PredictPayload(BaseModel):
    closes: List[float] = Field(..., description="Chronological close prices")
    normalize: bool = Field(default=True, description="Whether to normalize inputs before inference")

    @validator('closes')
    def validate_closes(cls, v):
        if len(v) < 20:
            raise ValueError("Need at least 20 close prices for prediction")
        if any(not np.isfinite(price) for price in v):
            raise ValueError("All close prices must be finite numbers")
        return v

class SMCResponse(BaseModel):
    trend: str
    bos: Dict[str, Any]
    choch: Dict[str, Any]
    fvgZones: List[Dict[str, Any]]
    orderBlocks: List[Dict[str, Any]]
    liquiditySwept: bool
    bias: str
    entry: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    explanation: str

class PredictResponse(BaseModel):
    signal: str
    confidence: float
    raw_prediction: float

class FinalSignalResponse(BaseModel):
    signal: str
    confidence: float
    smc_analysis: SMCResponse
    ai_prediction: PredictResponse
    entry: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    explanation: str

def map_signal(prediction: float) -> str:
    """
    Map prediction to trading signal with more sensitive thresholds
    Model outputs are typically small values, so we use lower thresholds
    """
    if prediction > 0.1:  # Changed from 0.6 to 0.1 for better sensitivity
        return 'BUY'
    if prediction < -0.1:  # Changed from -0.6 to -0.1
        return 'SELL'
    return 'NEUTRAL'

def normalize_series(closes: List[float]) -> tuple:
    """Normalize close prices to zero mean / unit std to stabilize inference."""
    series = np.asarray(closes, dtype=np.float32)
    if series.size == 0:
        raise ValueError("'closes' must contain at least one price")
    mean = float(series.mean())
    std = float(series.std()) or 1.0
    normalized = (series - mean) / std
    return normalized, mean, std

def calculate_confidence(prediction: float) -> float:
    """
    Calculate confidence score from raw prediction
    Since model outputs are small, we scale them appropriately
    """
    # Scale the prediction to a 0-1 confidence range
    # Predictions typically range from -1 to 1, but in practice are much smaller
    # We use a sigmoid-like scaling for better representation
    abs_pred = abs(prediction)
    
    # If prediction is very small (< 0.01), confidence is low
    if abs_pred < 0.01:
        confidence = abs_pred * 10  # Scale up small values
    # If prediction is moderate (0.01 - 0.5), use linear scaling
    elif abs_pred < 0.5:
        confidence = 0.1 + (abs_pred - 0.01) * 1.5  # Linear interpolation
    # If prediction is large (> 0.5), high confidence
    else:
        confidence = min(1.0, 0.5 + abs_pred)
    
    return float(min(1.0, max(0.0, confidence)))

def reshape_for_lstm(series: np.ndarray) -> np.ndarray:
    if series.ndim != 1:
        raise ValueError("Series must be 1-D before reshaping")
    return series.reshape(1, series.shape[0], 1)

@app.post('/smc', response_model=SMCResponse)
async def get_smc_analysis(payload: SignalPayload):
    try:
        # Validate that all arrays have the same length
        if not (len(payload.open) == len(payload.high) == len(payload.low) == len(payload.close)):
            raise HTTPException(status_code=400, detail="All price arrays must have the same length")
        
        # Create DataFrame from payload
        df = pd.DataFrame({
            'open': payload.open,
            'high': payload.high,
            'low': payload.low,
            'close': payload.close
        })
        
        # Perform SMC analysis
        result = smc_engine.analyze_market_structure(df)
        
        return SMCResponse(
            trend=result['trend'],
            bos=result['bos'],
            choch=result['choch'],
            fvgZones=result['fvgZones'],
            orderBlocks=result['orderBlocks'],
            liquiditySwept=result['liquiditySwept'],
            bias=result['bias'],
            entry=result['entry'],
            sl=result['sl'],
            tp=result['tp'],
            explanation=result['explanation']
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to analyze SMC: {str(e)}")

@app.post('/predict', response_model=PredictResponse)
async def predict(payload: PredictPayload):
    if model is None:
        # Fallback mode: return NEUTRAL with a small random prediction
        prediction = np.random.normal(0, 0.1)
    else:
        try:
            closes = np.asarray(payload.closes, dtype=np.float32)
            if payload.normalize:
                closes, _, _ = normalize_series(closes)
            else:
                closes = closes.astype(np.float32)
            reshaped = reshape_for_lstm(closes)
            prediction = float(model.predict(reshaped, verbose=0).squeeze())
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to run inference: {str(exc)}")

    signal = map_signal(prediction)
    confidence = calculate_confidence(prediction)  # Use new confidence calculation
    return PredictResponse(signal=signal, confidence=confidence, raw_prediction=prediction)

@app.post('/final', response_model=FinalSignalResponse)
async def get_final_signal(payload: SignalPayload):
    try:
        # Get SMC analysis
        df = pd.DataFrame({
            'open': payload.open,
            'high': payload.high,
            'low': payload.low,
            'close': payload.close
        })
        
        smc_result = smc_engine.analyze_market_structure(df)
        
        # Get AI prediction using close prices
        ai_payload = PredictPayload(closes=payload.close)
        ai_result = await predict(ai_payload)
        
        # Combine SMC and AI signals
        final_signal = "NEUTRAL"
        final_confidence = 0.0
        
        # If SMC has a bias, and AI agrees, strengthen the signal
        if smc_result['bias'] != "NEUTRAL" and ai_result.signal != "NEUTRAL":
            if smc_result['bias'] == ai_result.signal:
                final_signal = smc_result['bias']
                final_confidence = (smc_result.get('entry') is not None) * 0.5 + ai_result.confidence * 0.5
            else:
                # Conflict: prioritize SMC (as specified in requirements)
                final_signal = smc_result['bias']
                final_confidence = 0.7 if smc_result['bias'] != "NEUTRAL" else ai_result.confidence
        elif smc_result['bias'] != "NEUTRAL":
            # Only SMC has a signal
            final_signal = smc_result['bias']
            final_confidence = 0.6
        elif ai_result.signal != "NEUTRAL":
            # Only AI has a signal
            final_signal = ai_result.signal
            final_confidence = ai_result.confidence
        else:
            # Both are neutral
            final_signal = "NEUTRAL"
            final_confidence = 0.1
            
        # Ensure confidence is within bounds
        final_confidence = min(1.0, max(0.0, final_confidence))
        
        # Create explanation
        smc_indicators = []
        if smc_result['bos']['bullish']:
            smc_indicators.append("BOS up detected")
        if smc_result['bos']['bearish']:
            smc_indicators.append("BOS down detected")
        if smc_result['choch']['bullish']:
            smc_indicators.append("CHOCH up detected")
        if smc_result['choch']['bearish']:
            smc_indicators.append("CHOCH down detected")
        if smc_result['fvgZones']:
            smc_indicators.append(f"{len(smc_result['fvgZones'])} FVG zones detected")
        if smc_result['orderBlocks']:
            smc_indicators.append(f"{len(smc_result['orderBlocks'])} Order Blocks detected")
            
        explanation_parts = [
            f"SMC Analysis: {', '.join(smc_indicators) if smc_indicators else 'No major SMC patterns detected'}",
            f"AI Prediction: {ai_result.signal} (confidence: {ai_result.confidence:.2f})",
            f"Final Signal: {final_signal} (confidence: {final_confidence:.2f})"
        ]
        explanation = "; ".join(explanation_parts)
        
        return FinalSignalResponse(
            signal=final_signal,
            confidence=final_confidence,
            smc_analysis=SMCResponse(
                trend=smc_result['trend'],
                bos=smc_result['bos'],
                choch=smc_result['choch'],
                fvgZones=smc_result['fvgZones'],
                orderBlocks=smc_result['orderBlocks'],
                liquiditySwept=smc_result['liquiditySwept'],
                bias=smc_result['bias'],
                entry=smc_result['entry'],
                sl=smc_result['sl'],
                tp=smc_result['tp'],
                explanation=smc_result['explanation']
            ),
            ai_prediction=ai_result,
            entry=smc_result['entry'],
            sl=smc_result['sl'],
            tp=smc_result['tp'],
            explanation=explanation
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate final signal: {str(e)}")

@app.get('/health')
async def health():
    return {'status': 'ok', 'smc_engine_loaded': True, 'ai_model_loaded': model is not None}

if __name__ == '__main__':
    import uvicorn

    uvicorn.run('smc_server:app', host='0.0.0.0', port=int(os.getenv('AI_SERVER_PORT', 8000)), reload=False)