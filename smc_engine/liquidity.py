import numpy as np
from typing import List, Dict


class LiquidityDetector:
    """
    Detects liquidity sweeps in price action
    """
    
    def detect_liquidity_sweeps(self, highs: np.ndarray, lows: np.ndarray, swing_highs: List[Dict], swing_lows: List[Dict]) -> List[Dict]:
        """
        Detect liquidity sweeps at swing points
        Liquidity sweeps happen when price moves to grab stop losses at key levels
        """
        liquidity_sweeps = []
        
        # Check for liquidity sweeps at swing highs (bullish sweeps)
        for swing in swing_highs:
            # Look for wicks extending above the swing high (potential liquidity grab)
            for i in range(max(0, swing['index'] - 5), min(len(highs), swing['index'] + 5)):
                if highs[i] > swing['price'] and lows[i] < swing['price']:
                    # This candle formed a wick above the swing high, possibly sweeping liquidity
                    liquidity_sweeps.append({
                        'index': i,
                        'type': 'bullish_liquidity_sweep',
                        'level': swing['price'],
                        'candle_index': i,
                        'wick_size': highs[i] - swing['price']
                    })
        
        # Check for liquidity sweeps at swing lows (bearish sweeps)
        for swing in swing_lows:
            # Look for wicks extending below the swing low (potential liquidity grab)
            for i in range(max(0, swing['index'] - 5), min(len(lows), swing['index'] + 5)):
                if lows[i] < swing['price'] and highs[i] > swing['price']:
                    # This candle formed a wick below the swing low, possibly sweeping liquidity
                    liquidity_sweeps.append({
                        'index': i,
                        'type': 'bearish_liquidity_sweep',
                        'level': swing['price'],
                        'candle_index': i,
                        'wick_size': swing['price'] - lows[i]
                    })
        
        return liquidity_sweeps
    
    def detect_liquidity_zones(self, highs: np.ndarray, lows: np.ndarray, lookback: int = 20) -> List[Dict]:
        """
        Detect potential liquidity zones based on large wicks/levels that attracted orders
        """
        liquidity_zones = []
        
        for i in range(lookback, len(highs)):
            # Look for candles with large wicks (potential liquidity areas)
            body_size = abs(highs[i] - lows[i])
            upper_wick = highs[i] - max(highs[i], lows[i])
            lower_wick = min(highs[i], lows[i]) - lows[i]
            
            # If wick is significantly larger than body, it may have attracted liquidity
            if body_size > 0 and (upper_wick / body_size) > 2:
                liquidity_zones.append({
                    'index': i,
                    'type': 'upper_liquidity_zone',
                    'level': highs[i],
                    'strength': upper_wick / body_size
                })
            elif body_size > 0 and (lower_wick / body_size) > 2:
                liquidity_zones.append({
                    'index': i,
                    'type': 'lower_liquidity_zone',
                    'level': lows[i],
                    'strength': lower_wick / body_size
                })
        
        return liquidity_zones


class UnusualVolumeDetector:
    """
    Detects unusual volume patterns that may indicate institutional activity
    """
    
    def detect_unusual_volume(self, volumes: np.ndarray, lookback: int = 20, threshold: float = 1.5) -> List[Dict]:
        """
        Detect unusually high volume bars that may indicate institutional interest
        """
        unusual_volume = []
        
        if len(volumes) < lookback:
            return unusual_volume
        
        for i in range(lookback, len(volumes)):
            avg_volume = np.mean(volumes[i-lookback:i])
            
            if avg_volume > 0 and (volumes[i] / avg_volume) > threshold:
                unusual_volume.append({
                    'index': i,
                    'volume': volumes[i],
                    'avg_volume': avg_volume,
                    'ratio': volumes[i] / avg_volume,
                    'type': 'unusual_volume'
                })
        
        return unusual_volume