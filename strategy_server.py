from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import sys
import os

# Add project root to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Import our SMC and strategy modules
from smc_engine.smc import SMCAnalyzer
from ai_engine.predict import PredictionEngine
from strategy.hybrid_smc_ai_strategy import HybridSMCAIStrategy


app = Flask(__name__)

# Initialize SMC and AI components
smc_analyzer = SMCAnalyzer(lookback_period=20)
ai_engine = PredictionEngine()


class StrategyProcessor:
    """
    Processes market data and generates trading signals based on SMC + AI analysis
    """
    
    def __init__(self):
        self.smc_analyzer = SMCAnalyzer(lookback_period=20)
        self.ai_engine = PredictionEngine()

    def process_data(self, data: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        Process OHLCV data and return trading signal with entry, SL, and TP levels
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
                    'confidence': 0.0
                }
            
            # Run SMC analysis
            smc_result = self.smc_analyzer.analyze(df)
            
            # Get AI prediction
            closes = data.get('close', [])
            ai_result = self.ai_engine.get_prediction(closes)
            
            # Run risk management checks
            risk_ok = self.check_risk_management(df, smc_result)
            
            # Generate final signal based on SMC, AI and risk filters
            signal, confidence = self.generate_signal(smc_result, ai_result, risk_ok)
            
            # Calculate entry, stop loss, and take profit levels
            entry, sl, tp, explanation = self.calculate_levels(
                df, signal, smc_result, ai_result
            )
            
            return {
                'signal': signal,
                'entry': entry,
                'sl': sl,
                'tp': tp,
                'reason': explanation,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"Error in process_data: {str(e)}")
            return {
                'signal': 'NEUTRAL',
                'entry': None,
                'sl': None,
                'tp': None,
                'reason': f'ERROR: {str(e)}',
                'confidence': 0.0
            }

    def generate_signal(self, smc_result: Dict, ai_result: Dict, risk_ok: bool) -> tuple:
        """
        Generate signal based on SMC and AI combination
        """
        if not risk_ok:
            return 'NEUTRAL', 0.0
        
        smc_signal = smc_result.get('bias', 'NEUTRAL')
        ai_signal = ai_result.get('signal', 'NEUTRAL')
        ai_confidence = ai_result.get('confidence', 0.0)
        
        # Combine signals according to priority
        if smc_signal == 'NEUTRAL' and ai_signal == 'NEUTRAL':
            return 'NEUTRAL', 0.0
        elif smc_signal != 'NEUTRAL' and ai_signal != 'NEUTRAL':
            # Both signals agree
            if smc_signal == ai_signal:
                confidence = 0.8 * 0.7 + 0.2 * ai_confidence  # SMC weight 0.7, AI weight 0.3
                return smc_signal, min(1.0, confidence)
            else:
                # Conflict: SMC takes priority
                return smc_signal, 0.7
        elif smc_signal != 'NEUTRAL':
            # Only SMC has a signal
            return smc_signal, 0.6
        elif ai_signal != 'NEUTRAL':
            # Only AI has a signal
            return ai_signal, ai_confidence
        else:
            return 'NEUTRAL', 0.0

    def check_risk_management(self, df: pd.DataFrame, smc_result: Dict) -> bool:
        """
        Apply risk management checks
        """
        if len(df) < 200:
            return False
        
        current_price = df['close'].iloc[-1]
        
        # Check trend alignment and volatility metrics
        trend = smc_result.get('trend', 'NEUTRAL')
        market_phase = smc_result.get('market_phase', 'RANGING')
        
        # Additional risk checks could go here
        # For now, we'll return True if we have sufficient data and reasonable conditions
        return market_phase != 'INSUFFICIENT_DATA' and trend != 'NEUTRAL'

    def calculate_levels(self, df: pd.DataFrame, signal: str, 
                        smc_result: Dict, ai_result: Dict) -> tuple:
        """
        Calculate entry, stop loss, and take profit levels
        """
        if signal == 'NEUTRAL':
            return None, None, None, 'No signal generated'
        
        current_price = df['close'].iloc[-1]
        high_20 = df['high'].tail(20).max()
        low_20 = df['low'].tail(20).min()
        
        # Calculate ATR for risk management
        atr = self.calculate_atr(df)
        
        entry = None
        sl = None
        tp = None
        explanation = ""
        
        if signal == 'BUY':
            # For BUY signals: entry at current price, SL below recent swing low
            entry = current_price
            
            # Find recent swing lows for SL level
            swing_lows = smc_result.get('swing_lows', [])
            if swing_lows:
                recent_swing_low = max(swing_lows, key=lambda x: x['index']) if swing_lows else None
                if recent_swing_low:
                    sl = recent_swing_low['price'] - (atr * 0.5)  # SL below swing low
                else:
                    sl = current_price - (atr * 2)  # Fallback using ATR
            else:
                sl = current_price - (atr * 2)
            
            # Calculate TP based on risk-reward ratio (e.g., 1:2)
            risk_distance = abs(entry - sl) if sl else atr * 2
            tp = entry + (risk_distance * 2)  # 1:2 risk-reward ratio
            
            explanation = f"Buy signal: Entry at {entry:.5f}, SL at {sl:.5f}, TP at {tp:.5f}"
        
        elif signal == 'SELL':
            # For SELL signals: entry at current price, SL above recent swing high
            entry = current_price
            
            # Find recent swing highs for SL level
            swing_highs = smc_result.get('swing_highs', [])
            if swing_highs:
                recent_swing_high = max(swing_highs, key=lambda x: x['index']) if swing_highs else None
                if recent_swing_high:
                    sl = recent_swing_high['price'] + (atr * 0.5)  # SL above swing high
                else:
                    sl = current_price + (atr * 2)  # Fallback using ATR
            else:
                sl = current_price + (atr * 2)
            
            # Calculate TP based on risk-reward ratio (e.g., 1:2)
            risk_distance = abs(sl - entry) if sl else atr * 2
            tp = entry - (risk_distance * 2)  # 1:2 risk-reward ratio
            
            explanation = f"Sell signal: Entry at {entry:.5f}, SL at {sl:.5f}, TP at {tp:.5f}"
        
        return entry, sl, tp, explanation

    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate Average True Range for risk management
        """
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate ATR
        atr = true_range.rolling(window=period).mean().iloc[-1]
        
        return float(atr) if not np.isnan(atr) else 0.001  # Return small value if ATR is NaN


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
        result = processor.process_data(processed_data)
        
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
        'service': 'strategy_server',
        'timestamp': pd.Timestamp.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)