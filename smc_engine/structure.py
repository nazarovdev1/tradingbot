import numpy as np
from typing import List, Dict, Tuple


class SwingDetector:
    """
    Detects swing highs and lows based on fractal pattern
    """
    
    def __init__(self, lookback_period: int = 5):
        self.lookback_period = lookback_period
    
    def detect_swings(self, highs: np.ndarray, lows: np.ndarray) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect swing highs and lows
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(self.lookback_period, len(highs) - self.lookback_period):
            # Check for swing high (highest high in lookback range)
            is_swing_high = True
            for j in range(i - self.lookback_period, i + self.lookback_period + 1):
                if highs[i] < highs[j] and j != i:
                    is_swing_high = False
                    break
            if is_swing_high:
                swing_highs.append({
                    'index': i,
                    'price': highs[i],
                    'high': highs[i],
                    'low': lows[i],
                    'time': i  # Using index as time for now
                })
            
            # Check for swing low (lowest low in lookback range)
            is_swing_low = True
            for j in range(i - self.lookback_period, i + self.lookback_period + 1):
                if lows[i] > lows[j] and j != i:
                    is_swing_low = False
                    break
            if is_swing_low:
                swing_lows.append({
                    'index': i,
                    'price': lows[i],
                    'high': highs[i],
                    'low': lows[i],
                    'time': i  # Using index as time for now
                })
        
        return swing_highs, swing_lows
    
    def detect_fractals(self, highs: np.ndarray, lows: np.ndarray, lookback: int = 2) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect fractals based on MT5 logic (2 bars on each side)
        """
        bullish_fractals = []
        bearish_fractals = []
        
        for i in range(lookback, len(highs) - lookback):
            # Bullish fractal (low fractal) - lowest low at middle
            is_bullish = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and lows[i] > lows[j]:
                    is_bullish = False
                    break
            if is_bullish:
                bearish_fractals.append({
                    'index': i,
                    'price': lows[i],
                    'type': 'bullish',
                    'high': highs[i],
                    'low': lows[i]
                })
            
            # Bearish fractal (high fractal) - highest high at middle
            is_bearish = True
            for j in range(i - lookback, i + lookback + 1):
                if j != i and highs[i] < highs[j]:
                    is_bearish = False
                    break
            if is_bearish:
                bullish_fractals.append({
                    'index': i,
                    'price': highs[i],
                    'type': 'bearish',
                    'high': highs[i],
                    'low': lows[i]
                })
        
        return bullish_fractals, bearish_fractals


class BOSDetector:
    """
    Detects Break of Structure patterns
    """
    
    def detect_bos(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect BOS (Break of Structure) - when price breaks swing points
        """
        bullish_bos = []
        bearish_bos = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return bullish_bos, bearish_bos
        
        # Detect bullish BOS - breaking higher highs
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                bullish_bos.append({
                    'index': swing_highs[i]['index'],
                    'price': swing_highs[i]['price'],
                    'previous_price': swing_highs[i-1]['price'],
                    'type': 'bullish_bos'
                })
        
        # Detect bearish BOS - breaking lower lows
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                bearish_bos.append({
                    'index': swing_lows[i]['index'],
                    'price': swing_lows[i]['price'],
                    'previous_price': swing_lows[i-1]['price'],
                    'type': 'bearish_bos'
                })
        
        return bullish_bos, bearish_bos


class CHOCHDetector:
    """
    Detects Change of Character patterns
    """
    
    def detect_choch(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect CHOCH (Change of Character) - false break of swing points
        """
        bullish_choch = []
        bearish_choch = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return bullish_choch, bearish_choch
        
        # Detect bearish CHOCH - price breaks below swing low then reverses
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                bearish_choch.append({
                    'index': swing_lows[i]['index'],
                    'price': swing_lows[i]['price'],
                    'previous_price': swing_lows[i-1]['price'],
                    'type': 'bearish_choch'
                })
        
        # Detect bullish CHOCH - price breaks above swing high then reverses
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                bullish_choch.append({
                    'index': swing_highs[i]['index'],
                    'price': swing_highs[i]['price'],
                    'previous_price': swing_highs[i-1]['price'],
                    'type': 'bullish_choch'
                })
        
        return bullish_choch, bearish_choch