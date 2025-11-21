import os
# Suppress TensorFlow logs before importing TensorFlow
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import sys
import os

# Add project root to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Add path to the new backtrader strategy
sys.path.append(os.path.join(os.path.dirname(__file__), 'deep_leraning', 'backtrader-pullback-window-xauusd', 'src', 'strategy'))

# Import the new strategy class from the backtrader-pullback-window-xauusd repository
from sunrise_ogle_xauusd import SunriseOgle
# Import other components assuming they exist in the project
from smc_engine.smc import SMCAnalyzer
from ai_engine.predict import PredictionEngine


app = Flask(__name__)

class StrategyProcessor:
    """
    Processes market data and generates trading signals based on the new SunriseOgle strategy
    """

    def __init__(self):
        # We'll create a simplified version of the strategy logic that works for real-time analysis
        # instead of the full backtrader framework
        pass

    def __init__(self):
        # Initialize the AI engine to be used for prediction
        self.ai_engine = PredictionEngine()

    def process_data(self, data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Process OHLCV data and return trading signal with entry, SL, and TP levels
        Using simplified logic based on the SunriseOgle strategy and AI prediction
        """
        try:
            # Create DataFrame from received data
            df = pd.DataFrame({
                'open': data.get('open', []),
                'high': data.get('high', []),
                'low': data.get('low', []),
                'close': data.get('close', []),
                'volume': data.get('volume', [])
            })

            if df.empty or len(df) < 50:  # Need minimum data for analysis
                return {
                    'signal': 'NEUTRAL',
                    'entry': None,
                    'sl': None,
                    'tp': None,
                    'reason': 'INSUFFICIENT_DATA',
                    'confidence': 0.0,
                    'aiSignal': 'NEUTRAL',
                    'aiConfidence': 0.0
                }

            # Analyze using a simplified version of the SunriseOgle strategy logic
            signal, entry, sl, tp, reason, confidence = self._analyze_with_sunrise_ogle_logic(df)

            # Get AI prediction
            closes = data.get('close', [])
            if closes:
                try:
                    ai_result = self.ai_engine.get_prediction(closes)
                    ai_signal = ai_result.get('signal', 'NEUTRAL')
                    ai_confidence = ai_result.get('confidence', 0.0)
                except Exception as e:
                    print(f"Error getting AI prediction: {str(e)}")
                    ai_signal = 'NEUTRAL'
                    ai_confidence = 0.0
            else:
                ai_signal = 'NEUTRAL'
                ai_confidence = 0.0

            return {
                'signal': signal,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'reason': reason,
                'confidence': confidence,
                'aiSignal': ai_signal,
                'aiConfidence': ai_confidence
            }

        except Exception as e:
            print(f"Error in process_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'signal': 'NEUTRAL',
                'entry': None,
                'sl': None,
                'tp': None,
                'reason': f'ERROR: {str(e)}',
                'confidence': 0.0
            }

    def _analyze_with_sunrise_ogle_logic(self, df: pd.DataFrame) -> tuple:
        """
        Simplified version of the SunriseOgle strategy logic adapted for real-time analysis
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
            # EMA calculations (from the strategy parameters)
            ema_fast = df['close'].rolling(window=14).mean().iloc[-1]
            ema_medium = df['close'].rolling(window=18).mean().iloc[-1]
            ema_slow = df['close'].rolling(window=24).mean().iloc[-1]
            ema_confirm = df['close'].rolling(window=1).mean().iloc[-1]  # Effectively current close

            # Calculate ATR for volatility filtering (similar to strategy)
            # For XAU/USD, we need to use appropriate parameters
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift()).fillna(0)
            low_close = abs(df['low'] - df['close'].shift()).fillna(0)
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = true_range.rolling(window=10).mean().iloc[-1]

            # For XAU/USD, ensure we have realistic price ranges
            current_price = df['close'].iloc[-1]
            # XAU/USD (gold) typically trades between $1200-$2500, with some extreme ranges possible
            if current_price < 1200 or current_price > 2800:
                return 'NEUTRAL', None, None, None, f'PRICE_OUT_OF_RANGE: Current price {current_price} seems unrealistic for XAU/USD', 0.0

            # Check for EMA crossovers (core strategy logic from SunriseOgle)
            # LONG signal: confirmation EMA crosses above other EMAs (with conditions)
            long_signal = (
                (ema_confirm > ema_fast or ema_confirm > ema_medium or ema_confirm > ema_slow) and
                (prev_close > prev_open)  # Previous candle bullish (candle direction filter)
            )

            # SHORT signal: confirmation EMA crosses below other EMAs
            short_signal = (
                (ema_confirm < ema_fast or ema_confirm < ema_medium or ema_confirm < ema_slow) and
                (prev_close < prev_open)  # Previous candle bearish (candle direction filter)
            )

            # Apply basic ATR volatility filter (from strategy parameters)
            # Adjust for XAU/USD which has different price ranges than forex pairs
            atr_min_threshold = 5.0   # Minimum ATR for XAU/USD (in price units)
            atr_max_threshold = 50.0  # Maximum ATR for XAU/USD (in price units)

            if pd.isna(atr) or atr < atr_min_threshold or atr > atr_max_threshold:
                return 'NEUTRAL', None, None, None, f'ATR_FILTERED: {atr:.6f} outside range', 0.0

            # Determine signal based on the strategy's core logic
            if long_signal and not short_signal:
                # Calculate entry, SL, TP based on strategy's risk management
                entry = current_close
                # Using strategy's default multipliers: long_atr_sl_multiplier=4.5, long_atr_tp_multiplier=6.5
                sl = current_low - (atr * 4.5)  # Stop loss below recent low with multiplier
                tp = current_high + (atr * 6.5)  # Take profit based on ATR
                reason = f'LONG_SIGNAL: EMA crossover with bullish confirmation, ATR={atr:.6f}'
                confidence = min(0.9, atr * 5000)  # Use ATR as a proxy for confidence

                return 'BUY', entry, sl, tp, reason, confidence

            elif short_signal and not long_signal:
                # Calculate entry, SL, TP for short based on strategy's risk management
                entry = current_close
                # Using strategy's default multipliers for short: short_atr_sl_multiplier=2.5, short_atr_tp_multiplier=6.5
                sl = current_high + (atr * 2.5)  # SL above for short
                tp = current_low - (atr * 6.5)   # TP below for short
                reason = f'SHORT_SIGNAL: EMA crossover with bearish confirmation, ATR={atr:.6f}'
                confidence = min(0.9, atr * 5000)  # Use ATR as a proxy for confidence

                return 'SELL', entry, sl, tp, reason, confidence

            else:
                # Check for pullback conditions (similar to phase 2 of strategy)
                lookback_period = min(20, len(df))
                recent_highs = df['high'].tail(lookback_period)
                recent_lows = df['low'].tail(lookback_period)

                # Check for potential long setup after pullback to support
                if current_close > recent_lows.min() and current_close < recent_highs.max():
                    # Possible long setup after pullback to support
                    if current_close > ema_fast and current_close > ema_medium and current_close > ema_slow:
                        entry = current_close
                        sl = recent_lows.min() - (atr * 0.5)
                        tp = current_high + (atr * 3.0)
                        reason = f'LONG_PULLBACK: Price holding above support after pullback, ATR={atr:.6f}'
                        confidence = 0.6

                        return 'BUY', entry, sl, tp, reason, confidence

                # Check for potential short setup after pullback to resistance
                elif current_close < recent_highs.max() and current_close > recent_lows.min():
                    # Possible short setup after pullback to resistance
                    if current_close < ema_fast and current_close < ema_medium and current_close < ema_slow:
                        entry = current_close
                        sl = recent_highs.max() + (atr * 0.5)
                        tp = current_low - (atr * 3.0)
                        reason = f'SHORT_PULLBACK: Price holding below resistance after pullback, ATR={atr:.6f}'
                        confidence = 0.6

                        return 'SELL', entry, sl, tp, reason, confidence

            # If we reach here, no clear signal was found
            return 'NEUTRAL', None, None, None, f'NO_CLEAR_SIGNAL: ATR={atr:.6f}', 0.3

        except Exception as e:
            print(f"Error in simplified SunriseOgle analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return 'NEUTRAL', None, None, None, f'ANALYSIS_ERROR: {str(e)}', 0.0


# Initialize strategy processor
processor = StrategyProcessor()


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint to analyze market data and return trading signals
    Expected JSON format: {
        "symbol": "XAUUSDT",
        "candles": [
            {"open": 2000.0, "high": 2010.0, "low": 1995.0, "close": 2005.0, "volume": 1000.0}
        ]
    }
    OR
    {
        "symbol": "XAUUSDT",
        "open": [2000, 2001, ...],
        "high": [2010, 2012, ...],
        "low": [1995, 1998, ...],
        "close": [2005, 2008, ...],
        "volume": [1000, 1200, ...]
    }
    """
    try:
        print("DEBUG: Received request to /analyze endpoint")
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        symbol = data.get('symbol', 'XAUUSDT')
        
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
        
        # Process the data to get signal
        print(f"DEBUG: Calling processor with data lengths - open: {len(processed_data['open'])}, high: {len(processed_data['high'])}, low: {len(processed_data['low'])}, close: {len(processed_data['close'])}, volume: {len(processed_data['volume'])}")
        result = processor.process_data(processed_data)
        print(f"DEBUG: Got result from processor - signal: {result['signal']}, entry: {result['entry']}, confidence: {result['confidence']}")
        
        # Return the result with symbol information
        response = {
            'symbol': symbol,
            'signal': result['signal'],
            'entry': result['entry'],
            'sl': result['sl'],
            'tp': result['tp'],
            'reason': result['reason'],
            'confidence': result['confidence'],
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        return jsonify(response)

    except Exception as e:
        print(f"ERROR in /analyze endpoint: {str(e)}")
        import traceback
        traceback.print_exc()  # Full error stack to see what's wrong

        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'signal': 'NEUTRAL',
            'entry': None,
            'sl': None,
            'tp': None,
            'reason': f'ERROR: {str(e)}',
            'confidence': 0.0,
            'aiSignal': 'NEUTRAL',
            'aiConfidence': 0.0
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """
    Health check endpoint
    """
    return jsonify({
        'status': 'healthy',
        'service': 'strategy_server',
        'timestamp': pd.Timestamp.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)