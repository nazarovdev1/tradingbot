#!/usr/bin/env python3
"""
Test AI Prediction Pipeline
Tests the AI model to diagnose why it returns NEUTRAL with 0.00 confidence
"""
import os
import sys
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tensorflow.keras.models import load_model

def test_model_loading():
    """Test if model loads correctly"""
    print("=" * 60)
    print("TEST 1: Model Loading")
    print("=" * 60)
    
    model_path = project_root / 'models' / 'model.h5'
    print(f"Model path: {model_path}")
    print(f"Model exists: {model_path.exists()}")
    
    if not model_path.exists():
        print("❌ FAILED: Model file not found!")
        return None
    
    try:
        model = load_model(model_path)
        print("✅ SUCCESS: Model loaded successfully")
        print(f"\nModel Summary:")
        model.summary()
        return model
    except Exception as e:
        print(f"❌ FAILED: Error loading model: {e}")
        return None

def test_input_formatting():
    """Test input data formatting"""
    print("\n" + "=" * 60)
    print("TEST 2: Input Data Formatting")
    print("=" * 60)
    
    # Create sample close prices (20 values as expected by model)
    sample_closes = [
        1800.0, 1804.0, 1807.5, 1809.5, 1811.0,
        1813.5, 1814.0, 1816.5, 1818.0, 1819.5,
        1821.0, 1823.0, 1824.5, 1826.0, 1827.5,
        1828.5, 1829.0, 1830.5, 1832.0, 1833.5
    ]
    
    print(f"Sample closes (last 20 values): {sample_closes}")
    print(f"Length: {len(sample_closes)}")
    
    # Test normalization
    closes_array = np.array(sample_closes, dtype=np.float32)
    mean = float(closes_array.mean())
    std = float(closes_array.std()) or 1.0
    normalized = (closes_array - mean) / std
    
    print(f"\nNormalization:")
    print(f"  Mean: {mean:.4f}")
    print(f"  Std: {std:.4f}")
    print(f"  Normalized values (first 5): {normalized[:5]}")
    print(f"  Normalized values (last 5): {normalized[-5:]}")
    
    # Reshape for LSTM
    reshaped = normalized.reshape(1, 20, 1)
    print(f"\nReshaped for LSTM: {reshaped.shape}")
    print(f"  Expected shape: (1, 20, 1)")
    
    if reshaped.shape == (1, 20, 1):
        print("✅ SUCCESS: Input shape is correct")
        return reshaped
    else:
        print("❌ FAILED: Input shape is incorrect")
        return None

def test_prediction(model, input_data):
    """Test model prediction"""
    print("\n" + "=" * 60)
    print("TEST 3: Model Prediction")
    print("=" * 60)
    
    if model is None or input_data is None:
        print("❌ FAILED: Cannot test prediction (model or input is None)")
        return
    
    try:
        # Make prediction
        prediction = model.predict(input_data, verbose=0)
        raw_prediction = float(prediction.squeeze())
        
        print(f"Raw prediction output: {raw_prediction}")
        print(f"Prediction shape: {prediction.shape}")
        
        # Map to signal
        if raw_prediction > 0.6:
            signal = 'BUY'
        elif raw_prediction < -0.6:
            signal = 'SELL'
        else:
            signal = 'NEUTRAL'
        
        confidence = min(1.0, abs(raw_prediction))
        
        print(f"\nMapped Signal: {signal}")
        print(f"Confidence: {confidence:.4f} ({confidence*100:.2f}%)")
        
        # Diagnosis
        print("\n" + "-" * 60)
        print("DIAGNOSIS:")
        if abs(raw_prediction) < 0.01:
            print("⚠️  WARNING: Prediction is very close to zero!")
            print("   This suggests the model may not be properly trained")
            print("   or the input data is not in the expected format.")
        elif signal == 'NEUTRAL':
            print("ℹ️  INFO: Prediction is NEUTRAL (between -0.6 and 0.6)")
            print(f"   Raw value: {raw_prediction:.4f}")
        else:
            print(f"✅ SUCCESS: Model produced a {signal} signal")
        
        return signal, confidence, raw_prediction
        
    except Exception as e:
        print(f"❌ FAILED: Error during prediction: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_with_trending_data(model):
    """Test with clearly trending data"""
    print("\n" + "=" * 60)
    print("TEST 4: Prediction with Trending Data")
    print("=" * 60)
    
    # Create uptrend data
    uptrend_closes = [1800 + i*2 for i in range(20)]  # Clear uptrend
    print(f"Uptrend data: {uptrend_closes[:5]} ... {uptrend_closes[-5:]}")
    
    closes_array = np.array(uptrend_closes, dtype=np.float32)
    mean = float(closes_array.mean())
    std = float(closes_array.std()) or 1.0
    normalized = (closes_array - mean) / std
    reshaped = normalized.reshape(1, 20, 1)
    
    prediction = model.predict(reshaped, verbose=0)
    raw_prediction = float(prediction.squeeze())
    
    print(f"Uptrend prediction: {raw_prediction:.4f}")
    
    # Create downtrend data
    downtrend_closes = [1900 - i*2 for i in range(20)]  # Clear downtrend
    print(f"\nDowntrend data: {downtrend_closes[:5]} ... {downtrend_closes[-5:]}")
    
    closes_array = np.array(downtrend_closes, dtype=np.float32)
    mean = float(closes_array.mean())
    std = float(closes_array.std()) or 1.0
    normalized = (closes_array - mean) / std
    reshaped = normalized.reshape(1, 20, 1)
    
    prediction = model.predict(reshaped, verbose=0)
    raw_prediction = float(prediction.squeeze())
    
    print(f"Downtrend prediction: {raw_prediction:.4f}")
    
    print("\n" + "-" * 60)
    print("DIAGNOSIS:")
    print("If both predictions are close to 0, the model needs retraining.")
    print("If predictions are reasonable, the issue is with input data formatting.")

def main():
    print("\n" + "=" * 60)
    print("AI PREDICTION PIPELINE TEST")
    print("=" * 60)
    
    # Test 1: Model loading
    model = test_model_loading()
    
    # Test 2: Input formatting
    input_data = test_input_formatting()
    
    # Test 3: Prediction
    test_prediction(model, input_data)
    
    # Test 4: Trending data
    if model is not None:
        test_with_trending_data(model)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
