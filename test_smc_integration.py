#!/usr/bin/env python3
"""
Test SMC Integration
Tests the SMC engine to diagnose why no zones are detected
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from smc_engine import SMCEngine

def test_with_sample_data():
    """Test SMC engine with sample CSV data"""
    print("=" * 60)
    print("TEST 1: SMC Analysis with Sample Data")
    print("=" * 60)
    
    # Load sample data
    sample_file = project_root / 'sample_data.csv'
    print(f"Loading data from: {sample_file}")
    
    if not sample_file.exists():
        print("❌ FAILED: Sample data file not found!")
        return None
    
    df = pd.read_csv(sample_file)
    print(f"✅ Loaded {len(df)} candles")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst 5 rows:")
    print(df.head())
    print(f"\nLast 5 rows:")
    print(df.tail())
    
    # Analyze with SMC engine
    engine = SMCEngine()
    result = engine.analyze_market_structure(df)
    
    print("\n" + "-" * 60)
    print("SMC ANALYSIS RESULTS:")
    print("-" * 60)
    print(f"Trend: {result['trend']}")
    print(f"Bias: {result['bias']}")
    print(f"Entry: {result['entry']}")
    print(f"Stop Loss: {result['sl']}")
    print(f"Take Profit: {result['tp']}")
    print(f"\nBOS (Break of Structure):")
    print(f"  Bullish: {result['bos']['bullish']}")
    print(f"  Bearish: {result['bos']['bearish']}")
    print(f"\nCHOCH (Change of Character):")
    print(f"  Bullish: {result['choch']['bullish']}")
    print(f"  Bearish: {result['choch']['bearish']}")
    print(f"\nFVG Zones: {len(result['fvgZones'])} detected")
    if result['fvgZones']:
        for i, fvg in enumerate(result['fvgZones'][:3]):  # Show first 3
            print(f"  FVG {i+1}: {fvg}")
    print(f"\nOrder Blocks: {len(result['orderBlocks'])} detected")
    if result['orderBlocks']:
        for i, ob in enumerate(result['orderBlocks'][:3]):  # Show first 3
            print(f"  OB {i+1}: {ob}")
    print(f"\nLiquidity Swept: {result['liquiditySwept']}")
    print(f"\nExplanation: {result['explanation']}")
    
    return result

def test_with_trending_data():
    """Test SMC engine with synthetic trending data"""
    print("\n" + "=" * 60)
    print("TEST 2: SMC Analysis with Synthetic Trending Data")
    print("=" * 60)
    
    # Create uptrend with clear swing points
    np.random.seed(42)
    base_price = 1800
    candles = []
    
    for i in range(100):
        # Create uptrend with volatility
        trend = i * 0.5  # Uptrend
        noise = np.random.randn() * 2
        close = base_price + trend + noise
        high = close + abs(np.random.randn() * 1)
        low = close - abs(np.random.randn() * 1)
        open_price = low + (high - low) * np.random.rand()
        
        candles.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        })
    
    df = pd.DataFrame(candles)
    print(f"Created {len(df)} synthetic candles with uptrend")
    print(f"Price range: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # Analyze
    engine = SMCEngine()
    result = engine.analyze_market_structure(df)
    
    print("\n" + "-" * 60)
    print("SMC ANALYSIS RESULTS:")
    print("-" * 60)
    print(f"Trend: {result['trend']}")
    print(f"Bias: {result['bias']}")
    print(f"FVG Zones: {len(result['fvgZones'])} detected")
    print(f"Order Blocks: {len(result['orderBlocks'])} detected")
    
    return result

def test_with_real_api_format():
    """Test with data in the format from TwelveData API"""
    print("\n" + "=" * 60)
    print("TEST 3: SMC Analysis with API-like Data Format")
    print("=" * 60)
    
    # Simulate data from TwelveData API (reversed chronological)
    # Then reversed to chronological as done in index.js
    candles = []
    base_price = 2000
    
    for i in range(50):
        close = base_price + i * 0.3 + np.random.randn() * 1.5
        high = close + abs(np.random.randn() * 0.8)
        low = close - abs(np.random.randn() * 0.8)
        open_price = low + (high - low) * np.random.rand()
        
        candles.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        })
    
    df = pd.DataFrame(candles)
    print(f"Created {len(df)} candles (API format)")
    print(f"Current price (last close): {df['close'].iloc[-1]:.2f}")
    
    # Analyze
    engine = SMCEngine()
    result = engine.analyze_market_structure(df)
    
    print("\n" + "-" * 60)
    print("SMC ANALYSIS RESULTS:")
    print("-" * 60)
    print(f"Trend: {result['trend']}")
    print(f"Bias: {result['bias']}")
    print(f"Entry: {result['entry']}")
    
    # Check if current price is in any zone
    current_price = df['close'].iloc[-1]
    print(f"\nCurrent Price: {current_price:.2f}")
    
    in_zone = False
    if result['orderBlocks']:
        for ob in result['orderBlocks']:
            if 'low' in ob and 'high' in ob:
                if ob['low'] <= current_price <= ob['high']:
                    print(f"✅ Price is in Order Block: {ob}")
                    in_zone = True
                    break
    
    if not in_zone and result['fvgZones']:
        for fvg in result['fvgZones']:
            if fvg['low'] <= current_price <= fvg['high']:
                print(f"✅ Price is in FVG Zone: {fvg}")
                in_zone = True
                break
    
    if not in_zone:
        print("⚠️  Price is NOT in any SMC zone")
        print("   This is why the bot returns 'No valid SMC zone detected'")
    
    return result

def diagnose_results(result):
    """Diagnose why no signals are generated"""
    print("\n" + "=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    
    issues = []
    
    if result['bias'] == 'NEUTRAL':
        issues.append("Bias is NEUTRAL - no clear signal")
    
    if not result['bos']['bullish'] and not result['bos']['bearish']:
        issues.append("No BOS (Break of Structure) detected")
    
    if not result['choch']['bullish'] and not result['choch']['bearish']:
        issues.append("No CHOCH (Change of Character) detected")
    
    if len(result['fvgZones']) == 0:
        issues.append("No FVG (Fair Value Gap) zones detected")
    
    if len(result['orderBlocks']) == 0:
        issues.append("No Order Blocks detected")
    
    if issues:
        print("⚠️  ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        
        print("\n💡 RECOMMENDATIONS:")
        print("   - Check if swing detection parameters are too strict")
        print("   - Verify FVG detection logic (gap between candles)")
        print("   - Ensure enough data is provided (need at least 50+ candles)")
        print("   - Consider adjusting detection thresholds in smc_engine.py")
    else:
        print("✅ SMC engine is working correctly!")
        print(f"   Bias: {result['bias']}")
        print(f"   Entry: {result['entry']}")

def main():
    print("\n" + "=" * 60)
    print("SMC INTEGRATION TEST")
    print("=" * 60)
    
    # Test 1: Sample data
    result1 = test_with_sample_data()
    
    # Test 2: Trending data
    result2 = test_with_trending_data()
    
    # Test 3: API-like data
    result3 = test_with_real_api_format()
    
    # Diagnosis
    if result3:
        diagnose_results(result3)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
