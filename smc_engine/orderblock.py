import numpy as np
from typing import List, Dict


class OrderBlockDetector:
    """
    Detects Order Blocks in price action
    """
    
    def detect_order_blocks(self, highs: np.ndarray, lows: np.ndarray, swing_highs: List[Dict], swing_lows: List[Dict]) -> List[Dict]:
        """
        Detect potential order blocks based on swing points
        """
        order_blocks = []
        
        # Look for order blocks after swing highs/lows that held as support/resistance
        for i, swing in enumerate(swing_highs):
            if i > 0:
                # Potential bearish order block after a swing high that acted as resistance
                prev_swing = swing_highs[i-1]
                
                # Calculate the block as the range around the swing high
                block_high = max(swing['high'], prev_swing['high'])
                block_low = min(swing['high'], prev_swing['high']) - (max(swing['high'], prev_swing['high']) - min(swing['high'], prev_swing['high'])) * 0.3
                block_low = max(block_low, min(swing['low'], prev_swing['low']))  # Ensure block doesn't go below the lows
                
                order_blocks.append({
                    'index': swing['index'],
                    'type': 'bearish_order_block',
                    'high': block_high,
                    'low': block_low,
                    'mid_price': (block_high + block_low) / 2,
                    'strength': self._calculate_ob_strength(highs, lows, swing['index'])
                })
        
        for i, swing in enumerate(swing_lows):
            if i > 0:
                # Potential bullish order block after a swing low that acted as support
                prev_swing = swing_lows[i-1]
                
                # Calculate the block as the range around the swing low
                block_low = min(swing['low'], prev_swing['low'])
                block_high = max(swing['low'], prev_swing['low']) + (min(swing['low'], prev_swing['low']) - max(swing['low'], prev_swing['low'])) * 0.3
                block_high = min(block_high, max(swing['high'], prev_swing['high']))  # Ensure block doesn't go above the highs
                
                order_blocks.append({
                    'index': swing['index'],
                    'type': 'bullish_order_block',
                    'high': block_high,
                    'low': block_low,
                    'mid_price': (block_high + block_low) / 2,
                    'strength': self._calculate_ob_strength(highs, lows, swing['index'])
                })
        
        return order_blocks
    
    def _calculate_ob_strength(self, highs: np.ndarray, lows: np.ndarray, swing_index: int, lookback: int = 10) -> float:
        """
        Calculate the strength of an order block based on how many times it has been tested
        """
        if swing_index < lookback:
            return 0.0
        
        # Count how many times price tested the level in the recent past
        test_count = 0
        for i in range(max(0, swing_index-lookback), swing_index):
            if highs[i] > lows[swing_index] and lows[i] < highs[swing_index]:
                test_count += 1
        
        return min(1.0, test_count / 5.0)  # Normalize to 0-1 scale


class InsideBarDetector:
    """
    Detects inside bars which can indicate consolidation
    """
    
    def detect_inside_bars(self, highs: np.ndarray, lows: np.ndarray) -> List[Dict]:
        """
        Detect inside bars (bars completely within the range of previous bar)
        """
        inside_bars = []
        
        for i in range(1, len(highs)):
            if highs[i] <= highs[i-1] and lows[i] >= lows[i-1]:
                inside_bars.append({
                    'index': i,
                    'high': highs[i],
                    'low': lows[i],
                    'type': 'inside_bar'
                })
        
        return inside_bars


class MotherBarDetector:
    """
    Detects mother bars which can indicate significant market moves
    """
    
    def detect_mother_bars(self, highs: np.ndarray, lows: np.ndarray, min_ratio: float = 1.5) -> List[Dict]:
        """
        Detect mother bars (significantly larger bars that may contain inside bars)
        """
        mother_bars = []
        
        for i in range(1, len(highs)):
            current_range = highs[i] - lows[i]
            prev_range = highs[i-1] - lows[i-1]
            
            if prev_range > 0 and (current_range / prev_range) >= min_ratio:
                mother_bars.append({
                    'index': i-1,  # Previous bar is the mother bar
                    'high': highs[i-1],
                    'low': lows[i-1],
                    'type': 'mother_bar',
                    'range_ratio': current_range / prev_range
                })
        
        return mother_bars