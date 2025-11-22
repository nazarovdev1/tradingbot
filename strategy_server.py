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

# Import the SMC Engine (renamed to smc_logic to avoid conflict)
from smc_logic import SMCEngine
from ai_engine.predict import PredictionEngine


app = Flask(__name__)

class StrategyProcessor:
    """
    Processes market data and generates trading signals based on SMC and AI
    """

    def __init__(self):
        # Initialize the SMC engine
        self.smc_engine = SMCEngine()
        # Initialize the AI engine
        self.ai_engine = PredictionEngine()
        print("Strategy Processor Initialized with SMC and AI")

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
                    'confidence': 0.0,
                    'aiSignal': 'NEUTRAL',
                    'aiConfidence': 0.0
                }

            # 1. Run SMC Analysis
            smc_result = self.smc_engine.analyze_market_structure(df)
            
            # 2. Run AI Prediction
            closes = data.get('close', [])
            ai_signal = 'NEUTRAL'
            ai_confidence = 0.0
            
            try:
                ai_result = self.ai_engine.get_prediction(closes)
                ai_signal = ai_result.get('signal', 'NEUTRAL')
                ai_confidence = ai_result.get('confidence', 0.0)
            except Exception as e:
                print(f"Error getting AI prediction: {str(e)}")

            # 3. Combine Signals
            final_signal = 'NEUTRAL'
            confidence = 0.0
            reason = smc_result.get('explanation', '')
            
            smc_bias = smc_result.get('bias', 'NEUTRAL')
            
            # Logic for combining signals
            if smc_bias == 'BUY':
                if ai_signal == 'BUY':
                    final_signal = 'BUY'
                    confidence = 0.9  # Strong confirmation
                    reason += " | AI Confirms BUY"
                elif ai_signal == 'NEUTRAL':
                    final_signal = 'BUY'
                    confidence = 0.7  # Standard SMC buy
                else: # AI says SELL
                    final_signal = 'NEUTRAL'
                    confidence = 0.3
                    reason += " | AI Divergence (Bearish)"
                    
            elif smc_bias == 'SELL':
                if ai_signal == 'SELL':
                    final_signal = 'SELL'
                    confidence = 0.9  # Strong confirmation
                    reason += " | AI Confirms SELL"
                elif ai_signal == 'NEUTRAL':
                    final_signal = 'SELL'
                    confidence = 0.7  # Standard SMC sell
                else: # AI says BUY
                    final_signal = 'NEUTRAL'
                    confidence = 0.3
                    reason += " | AI Divergence (Bullish)"
            
            # If SMC is Neutral but AI is very confident?
            # Usually better to wait for SMC structure, so we keep it Neutral or check for lower timeframe structure
            # For now, we prioritize SMC structure.

            return {
                'signal': final_signal,
                'entry': smc_result.get('entry'),
                'sl': smc_result.get('sl'),
                'tp': smc_result.get('tp'),
                'reason': reason,
                'confidence': confidence,
                'aiSignal': ai_signal,
                'aiConfidence': ai_confidence,
                'smc_details': smc_result # Pass full details for frontend
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


# Initialize strategy processor
processor = StrategyProcessor()


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint to analyze market data and return trading signals
    """
    try:
        print("DEBUG: Received request to /analyze endpoint")
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        symbol = data.get('symbol', 'XAUUSDT')
        
        # Handle two different data formats
        if 'candles' in data and isinstance(data['candles'], list):
            candles = data['candles']
            if not candles:
                return jsonify({'error': 'No candle data provided'}), 400
            open_prices = [c['open'] for c in candles]
            high_prices = [c['high'] for c in candles]
            low_prices = [c['low'] for c in candles]
            close_prices = [c['close'] for c in candles]
            volumes = [c.get('volume', 0) for c in candles]
            
        elif all(key in data for key in ['open', 'high', 'low', 'close']):
            open_prices = data['open']
            high_prices = data['high']
            low_prices = data['low']
            close_prices = data['close']
            volumes = data.get('volume', [0] * len(close_prices))
            
        else:
            return jsonify({'error': 'Invalid data format'}), 400
        
        processed_data = {
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }
        
        # Process the data
        result = processor.process_data(processed_data)
        print(f"DEBUG: Result - Signal: {result['signal']}, Confidence: {result['confidence']}")
        
        # Return the result
        response = {
            'symbol': symbol,
            'signal': result['signal'],
            'entry': result['entry'],
            'sl': result['sl'],
            'tp': result['tp'],
            'reason': result['reason'],
            'confidence': result['confidence'],
            'aiSignal': result['aiSignal'],
            'aiConfidence': result['aiConfidence'],
            'smc_details': result.get('smc_details', {}),
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        return jsonify(response)

    except Exception as e:
        print(f"ERROR in /analyze endpoint: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'error': f'Analysis failed: {str(e)}',
            'signal': 'NEUTRAL',
            'confidence': 0.0
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'strategy_server',
        'timestamp': pd.Timestamp.now().isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)