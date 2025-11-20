"""
Strategy Interface for backtrader-pullback-window-xauusd
This creates a Flask API to interface with the new backtrader strategy
"""
import sys
import os
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from datetime import datetime
import json

# Add the path to the backtrader strategy
sys.path.append(os.path.join(os.path.dirname(__file__), 'deep_leraning', 'backtrader-pullback-window-xauusd', 'src', 'strategy'))

from sunrise_ogle_xauusd import SunriseOgle
import backtrader as bt

app = Flask(__name__)

class StrategyAdapter:
    """
    Adapts the backtrader strategy for real-time API usage
    """
    
    def __init__(self):
        self.strategy = None
        self.cerebro = None
        
    def analyze(self, data):
        """
        Analyze market data using the backtrader strategy logic
        data: dict with keys 'open', 'high', 'low', 'close', 'volume'
        """
        try:
            # Create a DataFrame from the input data
            df = pd.DataFrame({
                'open': data.get('open', []),
                'high': data.get('high', []),
                'low': data.get('low', []),
                'close': data.get('close', []),
                'volume': data.get('volume', [])
            })
            
            if df.empty or len(df) < 50:  # Need minimum data for strategy
                return {
                    'signal': 'NEUTRAL',
                    'entry': None,
                    'sl': None,
                    'tp': None,
                    'reason': 'INSUFFICIENT_DATA',
                    'confidence': 0.0
                }
            
            # Create a minimal version of the strategy decision logic
            # This is a simplified version focusing on the core signal detection logic
            signal, entry, sl, tp, reason, confidence = self._analyze_with_simplified_logic(df)
            
            return {
                'signal': signal,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'reason': reason,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"Error in analyze: {str(e)}")
            return {
                'signal': 'NEUTRAL',
                'entry': None,
                'sl': None,
                'tp': None,
                'reason': f'ERROR: {str(e)}',
                'confidence': 0.0
            }
    
    def _analyze_with_simplified_logic(self, df):
        """
        Simplified version of the strategy logic that mimics the core decision process
        without requiring the full backtrader framework for real-time analysis
        """
        try:
            # Get the latest data points
            current_close = df['close'].iloc[-1]
            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]
            current_open = df['open'].iloc[-1]
            
            # Get previous candle data for direction confirmation
            if len(df) < 2:
                return 'NEUTRAL', None, None, None, 'INSUFFICIENT_DATA', 0.0
                
            prev_close = df['close'].iloc[-2]
            prev_open = df['open'].iloc[-2]
            
            # Calculate basic indicators that the strategy uses
            # EMA calculations (simplified version)
            ema_fast = df['close'].rolling(window=14).mean().iloc[-1]
            ema_medium = df['close'].rolling(window=18).mean().iloc[-1]  
            ema_slow = df['close'].rolling(window=24).mean().iloc[-1]
            ema_confirm = df['close'].rolling(window=1).mean().iloc[-1]  # Effectively current close
            
            # Calculate ATR for volatility filtering
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=10).mean().iloc[-1]
            
            # Check for EMA crossovers (core strategy logic)
            # LONG signal: confirmation EMA crosses above other EMAs
            long_signal = (
                ema_confirm > ema_fast and ema_confirm > ema_medium and ema_confirm > ema_slow
            ) or (
                (ema_confirm > ema_fast or ema_confirm > ema_medium or ema_confirm > ema_slow) and
                prev_close > prev_open  # Previous candle bullish (if using candle direction filter)
            )
            
            # SHORT signal: confirmation EMA crosses below other EMAs  
            short_signal = (
                ema_confirm < ema_fast and ema_confirm < ema_medium and ema_confirm < ema_slow
            ) or (
                (ema_confirm < ema_fast or ema_confirm < ema_medium or ema_confirm < ema_slow) and
                prev_close < prev_open  # Previous candle bearish (if using candle direction filter)
            )
            
            # Apply basic ATR volatility filter (simplified)
            atr_min_threshold = 0.0001  # Minimum ATR for Gold
            atr_max_threshold = 0.0010  # Maximum ATR for Gold
            
            if atr < atr_min_threshold or atr > atr_max_threshold:
                return 'NEUTRAL', None, None, None, f'ATR_FILTERED: {atr:.6f} outside range', 0.0
            
            # Determine signal
            if long_signal and not short_signal:
                # Calculate entry, SL, TP based on strategy logic
                entry = current_close
                sl = current_low - (atr * 2.5)  # Based on strategy's SL multiplier
                tp = current_high + (atr * 6.5)  # Based on strategy's TP multiplier
                reason = f'LONG_SIGNAL: EMA crossover confirmed, ATR={atr:.6f}'
                confidence = min(0.9, atr * 10000)  # Use ATR as a proxy for confidence
                
                return 'BUY', entry, sl, tp, reason, confidence
                
            elif short_signal and not long_signal:
                # Calculate entry, SL, TP based on strategy logic  
                entry = current_close
                sl = current_high + (atr * 2.5)  # SL above for short
                tp = current_low - (atr * 6.5)   # TP below for short
                reason = f'SHORT_SIGNAL: EMA crossover confirmed, ATR={atr:.6f}'
                confidence = min(0.9, atr * 10000)  # Use ATR as a proxy for confidence
                
                return 'SELL', entry, sl, tp, reason, confidence
                
            else:
                # Check for pullback conditions (simplified)
                # Look for potential reversal patterns
                lookback_period = min(20, len(df))
                recent_highs = df['high'].tail(lookback_period)
                recent_lows = df['low'].tail(lookback_period)
                
                # Check for potential long setup after pullback
                if current_close > recent_lows.min() and current_close < recent_highs.max():
                    # Possible long setup after pullback to support
                    if current_close > ema_fast and current_close > ema_medium and current_close > ema_slow:
                        entry = current_close
                        sl = recent_lows.min() - (atr * 0.5)
                        tp = current_high + (atr * 3.0)
                        reason = f'LONG_PULLBACK: Price holding above support, ATR={atr:.6f}'
                        confidence = 0.6
                        
                        return 'BUY', entry, sl, tp, reason, confidence
                
                # Check for potential short setup after pullback  
                elif current_close < recent_highs.max() and current_close > recent_lows.min():
                    # Possible short setup after pullback to resistance
                    if current_close < ema_fast and current_close < ema_medium and current_close < ema_slow:
                        entry = current_close
                        sl = recent_highs.max() + (atr * 0.5)
                        tp = current_low - (atr * 3.0)
                        reason = f'SHORT_PULLBACK: Price holding below resistance, ATR={atr:.6f}'
                        confidence = 0.6
                        
                        return 'SELL', entry, sl, tp, reason, confidence

            # No clear signal
            return 'NEUTRAL', None, None, None, f'NO_CLEAR_SIGNAL: ATR={atr:.6f}', 0.3
            
        except Exception as e:
            print(f"Error in simplified analysis: {str(e)}")
            return 'NEUTRAL', None, None, None, f'ANALYSIS_ERROR: {str(e)}', 0.0


# Create global strategy adapter instance
adapter = StrategyAdapter()


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint to analyze market data and return trading signals
    Expected JSON format: {
        "symbol": "XAU/USD",
        "candles": [
            {"open": 2000.0, "high": 2010.0, "low": 1995.0, "close": 2005.0, "volume": 1000.0}
        ]
    }
    OR
    {
        "symbol": "XAU/USD", 
        "open": [2000, 2001, ...],
        "high": [2010, 2012, ...],
        "low": [1995, 1998, ...],
        "close": [2005, 2008, ...],
        "volume": [1000, 1200, ...]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        symbol = data.get('symbol', 'XAU/USD')
        
        # Handle two different data formats
        if 'candles' in data and isinstance(data['candles'], list):
            # Format with candles array
            candles = data['candles']
            
            if not candles:
                return jsonify({'error': 'No candle data provided'}), 400
            
            # Extract OHLCV from candles array
            open_prices = [c['open'] for c in candles]
            high_prices = [c['high'] for c in candles]
            low_prices = [c['low'] for c in candles]
            close_prices = [c['close'] for c in candles]
            volumes = [c.get('volume', 0) for c in candles]  # Volume is optional
            
        elif all(key in data for key in ['open', 'high', 'low', 'close']):
            # Format with separate arrays
            open_prices = data['open']
            high_prices = data['high']
            low_prices = data['low']
            close_prices = data['close']
            volumes = data.get('volume', [0] * len(close_prices))
            
        else:
            return jsonify({'error': 'Invalid data format. Provide either "candles" array or separate OHLCV arrays'}), 400
        
        # Validate data lengths
        if not (len(open_prices) == len(high_prices) == len(low_prices) == len(close_prices)):
            return jsonify({'error': 'All price arrays must have the same length'}), 400
        
        if len(volumes) != len(close_prices):
            return jsonify({'error': 'Volume array must have the same length as price arrays'}), 400
        
        # Create the processed data dict
        processed_data = {
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }
        
        # Analyze using the strategy adapter
        result = adapter.analyze(processed_data)
        
        # Return the result with symbol information
        response = {
            'symbol': symbol,
            'signal': result['signal'],
            'entry': result['entry'],
            'sl': result['sl'],
            'tp': result['tp'],
            'reason': result['reason'],
            'confidence': result['confidence'],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in /analyze endpoint: {str(e)}")
        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'signal': 'NEUTRAL',
            'entry': None,
            'sl': None,
            'tp': None,
            'reason': f'ERROR: {str(e)}',
            'confidence': 0.0
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'service': 'strategy_interface',
        'strategy': 'backtrader-pullback-window-xauusd',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("Starting Strategy Interface Server for XAU/USD...")
    app.run(host='0.0.0.0', port=5000, debug=False)