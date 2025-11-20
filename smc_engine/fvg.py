import numpy as np
from typing import List, Dict


class FVGDetector:
    """
    Detects Fair Value Gaps (FVG) in price action
    FVG is a gap between candles that gets filled
    """
    
    def detect_fvg(self, opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """
        Detect Fair Value Gaps in the price data
        """
        fvg_zones = []
        
        # Look for FVGs by checking gaps between candles
        for i in range(2, len(highs) - 1):
            # Define the three candles involved in potential FVG
            prev_candle = {
                'high': highs[i-2],
                'low': lows[i-2],
                'open': opens[i-2],
                'close': closes[i-2]
            }
            
            middle_candle = {
                'high': highs[i-1],
                'low': lows[i-1],
                'open': opens[i-1],
                'close': closes[i-1]
            }
            
            next_candle = {
                'high': highs[i],
                'low': lows[i],
                'open': opens[i],
                'close': closes[i]
            }
            
            # Check for Bullish FVG: previous candle's low < next candle's high, 
            # and middle candle doesn't fill the gap
            if (prev_candle['high'] < next_candle['low'] and 
                middle_candle['high'] <= next_candle['low'] and 
                middle_candle['low'] >= prev_candle['high']):
                
                fvg_zones.append({
                    'index': i-1,
                    'type': 'bullish_fvg',
                    'high': next_candle['low'],  # Upper bound of the gap
                    'low': prev_candle['high'],  # Lower bound of the gap
                    'entry': (next_candle['low'] + prev_candle['high']) / 2,
                    'gap_size': next_candle['low'] - prev_candle['high']
                })
            
            # Check for Bearish FVG: previous candle's high > next candle's low,
            # and middle candle doesn't fill the gap
            elif (prev_candle['low'] > next_candle['high'] and 
                  middle_candle['high'] <= prev_candle['low'] and 
                  middle_candle['low'] >= next_candle['high']):
                
                fvg_zones.append({
                    'index': i-1,
                    'type': 'bearish_fvg',
                    'high': prev_candle['low'],  # Upper bound of the gap
                    'low': next_candle['high'],  # Lower bound of the gap
                    'entry': (prev_candle['low'] + next_candle['high']) / 2,
                    'gap_size': prev_candle['low'] - next_candle['high']
                })
        
        return fvg_zones


class ImpulsePullbackDetector:
    """
    Detects impulse and pullback patterns in price action
    """
    
    def detect_impulse_pullback(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> List[Dict]:
        """
        Detect impulse moves followed by pullbacks
        """
        patterns = []
        
        if len(closes) < 10:
            return patterns
        
        # Calculate simple momentum
        momentum = np.diff(closes)
        
        # Look for potential impulse moves (strong consecutive moves in one direction)
        for i in range(5, len(momentum) - 5):
            # Check for bullish impulse (4+ consecutive positive moves)
            if all(m > 0 for m in momentum[i-4:i+1]) and momentum[i-5] < 0:
                # Check for pullback (opposite direction move)
                if momentum[i+1] < 0 and momentum[i+2] < 0:
                    patterns.append({
                        'index': i,
                        'type': 'bullish_impulse_pullback',
                        'impulse_start': i-4,
                        'impulse_end': i,
                        'pullback_start': i+1,
                        'pullback_end': i+2
                    })
            
            # Check for bearish impulse (4+ consecutive negative moves)
            elif all(m < 0 for m in momentum[i-4:i+1]) and momentum[i-5] > 0:
                # Check for pullback (opposite direction move)
                if momentum[i+1] > 0 and momentum[i+2] > 0:
                    patterns.append({
                        'index': i,
                        'type': 'bearish_impulse_pullback',
                        'impulse_start': i-4,
                        'impulse_end': i,
                        'pullback_start': i+1,
                        'pullback_end': i+2
                    })
        
        return patterns