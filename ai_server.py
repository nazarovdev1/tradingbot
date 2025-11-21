import os
# Suppress TensorFlow logs before importing TensorFlow
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from pathlib import Path
from typing import List

import numpy as np
from fastapi import FastAPI, HTTPException
import pydantic
from pydantic.v1 import BaseModel, Field, validator

from utils.preprocessing import normalize_series, reshape_for_lstm

MODEL_PATH = Path(os.getenv('AI_MODEL_PATH', Path(__file__).resolve().parent / 'models' / 'model.h5'))
if MODEL_PATH.exists():
    try:
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
    except Exception as e:
        print(f"Failed to load model: {e}. Using fallback mode.")
        model = None
else:
    model = None
    print("No model file found. Using fallback mode.")
app = FastAPI(title="XAU/USD LSTM Inference API", version="1.0.0")


class PredictPayload(BaseModel):
    closes: List[float] = Field(..., min_items=20, description="Chronological close prices")
    normalize: bool = Field(default=True, description="Whether to z-score normalize inputs before inference")

    @validator('closes')
    def validate_closes(cls, v):
        if any(not np.isfinite(price) for price in v):
            raise ValueError("All close prices must be finite numbers")
        return v


class PredictResponse(BaseModel):
    signal: str
    confidence: float
    raw_prediction: float


def map_signal(prediction: float) -> str:
    # More practical thresholds for trading signals
    # Using smaller thresholds to catch more trading opportunities
    if prediction > 0.1:
        return 'BUY'
    if prediction < -0.1:
        return 'SELL'
    return 'NEUTRAL'


@app.post('/predict', response_model=PredictResponse)
async def predict(payload: PredictPayload):
    if model is None:
        # Fallback mode: return NEUTRAL with random prediction
        prediction = np.random.normal(0, 0.5)
    else:
        try:
            closes = np.asarray(payload.closes, dtype=np.float32)
            if payload.normalize:
                closes, _, _ = normalize_series(closes)
            else:
                closes = closes.astype(np.float32)
            reshaped = reshape_for_lstm(closes)
            prediction = float(model.predict(reshaped, verbose=0).squeeze())
        except Exception as exc:  # pylint: disable=broad-except
            raise HTTPException(status_code=400, detail=f"Failed to run inference: {exc}") from exc

    signal = map_signal(prediction)
    confidence = float(min(1.0, abs(prediction)))
    return PredictResponse(signal=signal, confidence=confidence, raw_prediction=prediction)


@app.get('/health')
async def health():
    return {'status': 'ok'}


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('ai_server:app', host='0.0.0.0', port=int(os.getenv('AI_SERVER_PORT', 5001)), reload=False)
