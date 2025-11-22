import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import the StrategyProcessor from strategy_server
try:
    from strategy_server import StrategyProcessor
    print("✅ Successfully imported StrategyProcessor")
except ImportError as e:
    print(f"❌ Failed to import StrategyProcessor: {e}")
    sys.exit(1)

def create_sample_data(trend='bullish'):
    """Create sample OHLCV data"""
    print(f"Creating {trend} sample data...")
    candles = []
    base_price = 2000.0
    
    for i in range(100):
        if trend == 'bullish':
            # Create uptrend
            change = np.random.normal(1.0, 2.0) # Positive mean
        elif trend == 'bearish':
            # Create downtrend
            change = np.random.normal(-1.0, 2.0) # Negative mean
        else:
            # Range
            change = np.random.normal(0, 2.0)
            
        close = base_price + change
        high = close + abs(np.random.normal(0, 1.0))
        low = close - abs(np.random.normal(0, 1.0))
        open_p = low + (high - low) * np.random.random()
        
        base_price = close
        
        candles.append({
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': 1000
        })
        
    return {
        'open': [c['open'] for c in candles],
        'high': [c['high'] for c in candles],
        'low': [c['low'] for c in candles],
        'close': [c['close'] for c in candles],
        'volume': [c['volume'] for c in candles]
    }

def test_processor():
    print("\n" + "="*50)
    print("TESTING STRATEGY PROCESSOR")
    print("="*50)
    
    try:
        processor = StrategyProcessor()
        
        # Test 1: Bullish Data
        print("\n--- Test 1: Bullish Data ---")
        data_bullish = create_sample_data('bullish')
        result_bullish = processor.process_data(data_bullish)
        print(f"Signal: {result_bullish['signal']}")
        print(f"Confidence: {result_bullish['confidence']}")
        print(f"Reason: {result_bullish['reason']}")
        print(f"AI Signal: {result_bullish['aiSignal']}")
        
        # Test 2: Bearish Data
        print("\n--- Test 2: Bearish Data ---")
        data_bearish = create_sample_data('bearish')
        result_bearish = processor.process_data(data_bearish)
        print(f"Signal: {result_bearish['signal']}")
        print(f"Confidence: {result_bearish['confidence']}")
        print(f"Reason: {result_bearish['reason']}")
        print(f"AI Signal: {result_bearish['aiSignal']}")
        
        # Test 3: Check SMC Details presence
        print("\n--- Test 3: SMC Details ---")
        if 'smc_details' in result_bullish:
            print("✅ SMC Details present in response")
            details = result_bullish['smc_details']
            print(f"Trend detected: {details.get('trend')}")
            print(f"Bias detected: {details.get('bias')}")
        else:
            print("❌ SMC Details MISSING in response")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_processor()
