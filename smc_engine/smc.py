import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

from .structure import SwingDetector
from .fvg import FVGDetector
from .orderblock import OrderBlockDetector
from .liquidity import LiquidityDetector


class SMCAnalyzer:
    """
    Smart Money Concept Analyzer that combines all SMC elements
    """
    
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
        self.swing_detector = SwingDetector(lookback_period)
        self.fvg_detector = FVGDetector()
        self.ob_detector = OrderBlockDetector()
        self.liquidity_detector = LiquidityDetector()
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Main analysis function that combines all SMC elements
        """
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        opens = df['open'].values
        
        # Detect swings
        swing_highs, swing_lows = self.swing_detector.detect_swings(highs, lows)
        
        # Detect fractals
        bullish_fractals, bearish_fractals = self.swing_detector.detect_fractals(highs, lows)
        
        # Detect BOS and CHOCH
        bos_bullish, bos_bearish, choch_bullish, choch_bearish = self.detect_bos_choch(swing_highs, swing_lows)
        
        # Detect FVGs
        fvg_zones = self.fvg_detector.detect_fvg(opens, highs, lows, closes)
        
        # Detect Order Blocks
        order_blocks = self.ob_detector.detect_order_blocks(highs, lows, swing_highs, swing_lows)
        
        # Detect Liquidity Sweeps
        liquidity_sweeps = self.liquidity_detector.detect_liquidity_sweeps(highs, lows, swing_highs, swing_lows)
        
        # Determine market phase
        market_phase = self.determine_market_phase(closes)
        
        # Determine trend based on swing structure
        trend = self.determine_trend(swing_highs, swing_lows)
        
        result = {
            'trend': trend,
            'market_phase': market_phase,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'bullish_fractals': bullish_fractals,
            'bearish_fractals': bearish_fractals,
            'bullish_bos': bos_bullish,
            'bearish_bos': bos_bearish,
            'bullish_choch': choch_bullish,
            'bearish_choch': choch_bearish,
            'fvg_zones': fvg_zones,
            'order_blocks': order_blocks,
            'liquidity_sweeps': liquidity_sweeps,
            'fibonacci_levels': self.calculate_fibonacci_levels(df),
            'bias': self.calculate_bias(bos_bullish, bos_bearish, choch_bullish, choch_bearish, fvg_zones, order_blocks),
            'current_price': closes[-1] if len(closes) > 0 else None
        }
        
        return result

    def analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """
        Wrapper method for backward compatibility with the server interface
        """
        result = self.analyze(df)

        return {
            'trend': result['trend'],
            'bos': {
                'bullish': len(result.get('bullish_bos', [])) > 0,
                'bearish': len(result.get('bearish_bos', [])) > 0
            },
            'choch': {
                'bullish': len(result.get('bullish_choch', [])) > 0,
                'bearish': len(result.get('bearish_choch', [])) > 0
            },
            'fvgZones': result.get('fvg_zones', []),
            'orderBlocks': result.get('order_blocks', []),
            'liquiditySwept': len(result.get('liquidity_sweeps', [])) > 0,
            'bias': result.get('bias', 'NEUTRAL'),
            'entry': None,
            'sl': None,
            'tp': None,
            'explanation': f"Trend: {result.get('trend', 'NONE')}, Bias: {result.get('bias', 'NONE')}"
        }
    
    def detect_bos_choch(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> Tuple[List, List, List, List]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHOCH)
        """
        bos_bullish = []
        bos_bearish = []
        choch_bullish = []
        choch_bearish = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return bos_bullish, bos_bearish, choch_bullish, choch_bearish
        
        # Detect BOS patterns
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                bos_bullish.append({
                    'index': swing_highs[i]['index'],
                    'price': swing_highs[i]['price'],
                    'previous_price': swing_highs[i-1]['price'],
                    'type': 'bullish_bos'
                })
        
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                bos_bearish.append({
                    'index': swing_lows[i]['index'],
                    'price': swing_lows[i]['price'],
                    'previous_price': swing_lows[i-1]['price'],
                    'type': 'bearish_bos'
                })
        
        # Detect CHOCH patterns
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                choch_bearish.append({
                    'index': swing_lows[i]['index'],
                    'price': swing_lows[i]['price'],
                    'previous_price': swing_lows[i-1]['price'],
                    'type': 'bearish_choch'
                })
        
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                choch_bullish.append({
                    'index': swing_highs[i]['index'],
                    'price': swing_highs[i]['price'],
                    'previous_price': swing_highs[i-1]['price'],
                    'type': 'bullish_choch'
                })
        
        return bos_bullish, bos_bearish, choch_bullish, choch_bearish
    
    def determine_market_phase(self, closes: np.ndarray) -> str:
        """
        Determine market phase based on price action
        """
        if len(closes) < 50:
            return "INSUFFICIENT_DATA"
        
        # Calculate volatility relative to moving average
        ma_20 = np.mean(closes[-20:])
        volatility = np.std(closes[-20:])
        relative_volatility = volatility / ma_20 if ma_20 != 0 else 0
        
        # Determine if trending or ranging based on price movement
        recent_range = max(closes[-20:]) - min(closes[-20:])
        avg_range = np.mean([max(closes[i-5:i]) - min(closes[i-5:i]) for i in range(5, len(closes)) if i < len(closes)])
        
        if relative_volatility > 0.02:  # High volatility
            return "DISTRIBUTION" if closes[-1] > closes[-20] else "ACCUMULATION"
        elif recent_range > avg_range * 1.5:  # Expanding range
            return "TRENDING"
        else:  # Low volatility and stable range
            return "RANGING"
    
    def determine_trend(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> str:
        """
        Determine the current trend based on swing structure
        """
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return "NEUTRAL"
        
        last_2_highs = swing_highs[-2:]
        last_2_lows = swing_lows[-2:]
        
        higher_highs = last_2_highs[1]['price'] > last_2_highs[0]['price']
        higher_lows = last_2_lows[1]['price'] > last_2_lows[0]['price']
        lower_highs = last_2_highs[1]['price'] < last_2_highs[0]['price']
        lower_lows = last_2_lows[1]['price'] < last_2_lows[0]['price']
        
        if higher_highs and higher_lows:
            return "BULLISH"
        elif lower_highs and lower_lows:
            return "BEARISH"
        else:
            return "RANGE"
    
    def calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict[float, float]:
        """
        Calculate fibonacci retracement levels based on recent swing points
        """
        if len(df) < 20:
            return {}
        
        highs = df['high'].values
        lows = df['low'].values
        
        # Find the highest high and lowest low in the lookback period
        recent_high = max(highs[-20:])
        recent_low = min(lows[-20:])
        
        diff = recent_high - recent_low
        
        levels = {}
        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
        
        for ratio in fib_ratios:
            levels[ratio] = recent_low + (diff * ratio)
        
        return levels
    
    def calculate_bias(self, bos_bullish: List, bos_bearish: List, choch_bullish: List, choch_bearish: List, 
                      fvg_zones: List, order_blocks: List) -> str:
        """
        Calculate the overall SMC bias based on detected elements
        """
        bullish_signals = len(bos_bullish) + len(choch_bullish)
        bearish_signals = len(bos_bearish) + len(choch_bearish)
        
        # Check for bullish FVGs and order blocks
        bullish_fvg = sum(1 for fvg in fvg_zones if fvg.get('type') == 'bullish_fvg')
        bullish_ob = sum(1 for ob in order_blocks if ob.get('type') == 'bullish_order_block')
        
        # Check for bearish FVGs and order blocks
        bearish_fvg = sum(1 for fvg in fvg_zones if fvg.get('type') == 'bearish_fvg')
        bearish_ob = sum(1 for ob in order_blocks if ob.get('type') == 'bearish_order_block')
        
        bullish_signals += bullish_fvg + bullish_ob
        bearish_signals += bearish_fvg + bearish_ob
        
        if bullish_signals > bearish_signals:
            return "BULLISH"
        elif bearish_signals > bullish_signals:
            return "BEARISH"
        else:
            return "NEUTRAL"
