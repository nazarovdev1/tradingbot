
import pandas as pd
from smc_logic import SMCEngine

def test_fvg_logic():
    engine = SMCEngine()
    
    # Create a clear Bullish FVG pattern
    # Candle 1: High 100
    # Candle 2: Big Green (Low 99, High 110)
    # Candle 3: Low 105
    # Gap: 100 - 105
    
    highs = [100.0, 110.0, 115.0, 120.0]
    lows =  [90.0,  99.0,  105.0, 112.0]
    opens = [95.0,  100.0, 108.0, 115.0]
    closes =[98.0,  108.0, 114.0, 118.0]
    
    print("Testing Bullish FVG:")
    print(f"Candle 1 High: {highs[0]}")
    print(f"Candle 2 High: {highs[1]}")
    print(f"Candle 3 Low: {lows[2]}")
    print(f"Expected Gap: {highs[0]} - {lows[2]}")
    
    fvg_zones = engine.detect_fvg(opens, highs, lows, closes)
    print(f"Detected FVGs: {len(fvg_zones)}")
    for zone in fvg_zones:
        print(zone)

    # Check the specific condition I suspected was wrong
    # if next_low > prev_high and middle_high <= next_low and middle_low >= prev_high:
    prev_high = highs[0] # 100
    middle_high = highs[1] # 110
    next_low = lows[2] # 105
    
    print("\nDebug Conditions:")
    print(f"next_low > prev_high: {next_low > prev_high} (105 > 100)")
    print(f"middle_high <= next_low: {middle_high <= next_low} (110 <= 105) <--- SUSPECTED FAILURE")
    print(f"middle_low >= prev_high: {lows[1] >= prev_high} (99 >= 100)")

if __name__ == "__main__":
    test_fvg_logic()
