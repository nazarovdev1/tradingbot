import numpy as np
from typing import List, Dict, Tuple, Optional
import pandas as pd


class SMCEngine:
    """
    Smart Money Concept Engine that replicates the logic from MT5 SMC indicator
    """
    
    def __init__(self):
        self.lookback = 20  # Default lookback for fractal detection
        
    def detect_swings(self, highs: List[float], lows: List[float], lookback: int = 5) -> Tuple[List[Dict], List[Dict]]:
        """
        Detect swing highs and lows based on fractal pattern
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(lookback, len(highs) - lookback):
            # Check for swing high (highest high in lookback range)
            is_swing_high = True
            for j in range(i - lookback, i + lookback + 1):
                if highs[i] < highs[j]:
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
            for j in range(i - lookback, i + lookback + 1):
                if lows[i] > lows[j]:
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
    
    def detect_fractals(self, highs: List[float], lows: List[float], lookback: int = 2) -> Tuple[List[Dict], List[Dict]]:
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
    
    def detect_bos_choch(self, swing_highs: List[Dict], swing_lows: List[Dict]) -> Dict:
        """
        Detect Break of Structure (BOS) and Change of Character (CHOCH)
        """
        bos_bullish = []
        bos_bearish = []
        choch_bullish = []
        choch_bearish = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {
                'bullish_bos': bos_bullish,
                'bearish_bos': bos_bearish,
                'bullish_choch': choch_bullish,
                'bearish_choch': choch_bearish
            }
        
        # Detect BOS and CHOCH patterns
        # For bullish BOS: higher high broken (new high above previous high)
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                # Check if this creates a BOS - new higher high breaks the previous level
                bos_bullish.append({
                    'index': swing_highs[i]['index'],
                    'price': swing_highs[i]['price'],
                    'previous_price': swing_highs[i-1]['price'],
                    'type': 'bullish_bos'
                })
        
        # For bearish BOS: lower low broken (new low below previous low)
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                # Check if this creates a BOS - new lower low breaks the previous level
                bos_bearish.append({
                    'index': swing_lows[i]['index'],
                    'price': swing_lows[i]['price'],
                    'previous_price': swing_lows[i-1]['price'],
                    'type': 'bearish_bos'
                })
        
        # For CHOCH patterns (Change of Character)
        # Bearish CHOCH: price breaks below previous swing low then back above
        for i in range(1, len(swing_lows)):
            if swing_lows[i]['price'] < swing_lows[i-1]['price']:
                choch_bearish.append({
                    'index': swing_lows[i]['index'],
                    'price': swing_lows[i]['price'],
                    'previous_price': swing_lows[i-1]['price'],
                    'type': 'bearish_choch'
                })
        
        # Bullish CHOCH: price breaks above previous swing high then back below
        for i in range(1, len(swing_highs)):
            if swing_highs[i]['price'] > swing_highs[i-1]['price']:
                choch_bullish.append({
                    'index': swing_highs[i]['index'],
                    'price': swing_highs[i]['price'],
                    'previous_price': swing_highs[i-1]['price'],
                    'type': 'bullish_choch'
                })
        
        return {
            'bullish_bos': bos_bullish,
            'bearish_bos': bos_bearish,
            'bullish_choch': choch_bullish,
            'bearish_choch': choch_bearish
        }
    
    def detect_fvg(self, opens: List[float], highs: List[float], lows: List[float], closes: List[float]) -> List[Dict]:
        """
        Detect Fair Value Gaps (FVG)
        FVG is a gap between candles that gets filled
        """
        fvg_zones = []
        
        for i in range(2, len(highs) - 1):
            # Bullish FVG: gap between previous candle and next candle that isn't filled by middle candle
            prev_high = highs[i-2]
            prev_low = lows[i-2]
            middle_high = highs[i-1]
            middle_low = lows[i-1]
            next_high = highs[i]
            next_low = lows[i]
            
            # Check for bullish FVG
            if next_low > prev_high and middle_high <= next_low and middle_low >= prev_high:
                fvg_zones.append({
                    'index': i-1,
                    'type': 'bullish_fvg',
                    'high': next_low,  # Upper bound of gap
                    'low': prev_high,  # Lower bound of gap
                    'entry': (next_low + prev_high) / 2
                })
            
            # Check for bearish FVG
            if next_high < prev_low and middle_high <= prev_low and middle_low >= next_high:
                fvg_zones.append({
                    'index': i-1,
                    'type': 'bearish_fvg',
                    'high': prev_low,  # Upper bound of gap
                    'low': next_high,  # Lower bound of gap
                    'entry': (prev_low + next_high) / 2
                })
        
        return fvg_zones
    
    def detect_order_blocks(self, highs: List[float], lows: List[float], swing_highs: List[Dict], swing_lows: List[Dict]) -> List[Dict]:
        """
        Detect order blocks based on swing points
        """
        order_blocks = []
        
        # Look for order blocks after swing highs/lows that held as support/resistance
        for i in range(len(swing_highs)):
            if i > 0:
                # Potential bearish order block after a swing high that held support
                swing_high = swing_highs[i]
                prev_swing_high = swing_highs[i-1]
                
                # Check if price moved away from the swing high and then returned
                # indicating liquidity grab and order block formation
                order_blocks.append({
                    'index': swing_high['index'],
                    'type': 'bearish_order_block',
                    'high': swing_high['high'],
                    'low': swing_high['low'],
                    'price': swing_high['price']
                })
        
        for i in range(len(swing_lows)):
            if i > 0:
                # Potential bullish order block after a swing low that held resistance
                swing_low = swing_lows[i]
                prev_swing_low = swing_lows[i-1]
                
                # Check if price moved away from the swing low and then returned
                order_blocks.append({
                    'index': swing_low['index'],
                    'type': 'bullish_order_block',
                    'high': swing_low['high'],
                    'low': swing_low['low'],
                    'price': swing_low['price']
                })
        
        return order_blocks
    
    def detect_liquidity_sweeps(self, highs: List[float], lows: List[float], swing_highs: List[Dict], swing_lows: List[Dict]) -> List[Dict]:
        """
        Detect liquidity sweeps (wicks that touch swing points)
        """
        liquidity_sweeps = []
        
        # Check for liquidity sweeps at swing points
        for swing in swing_highs:
            # Check if there's a candle that touched or went above the swing high (liquidity sweep up)
            for i in range(swing['index'] - 5, swing['index'] + 5):  # Look around the swing point
                if 0 <= i < len(highs):
                    if highs[i] >= swing['price'] and lows[i] < swing['price']:
                        liquidity_sweeps.append({
                            'index': i,
                            'type': 'liquidity_sweep_high',
                            'price': swing['price'],
                            'candle_index': i
                        })
        
        for swing in swing_lows:
            # Check if there's a candle that touched or went below the swing low (liquidity sweep down)
            for i in range(swing['index'] - 5, swing['index'] + 5):  # Look around the swing point
                if 0 <= i < len(lows):
                    if lows[i] <= swing['price'] and highs[i] > swing['price']:
                        liquidity_sweeps.append({
                            'index': i,
                            'type': 'liquidity_sweep_low',
                            'price': swing['price'],
                            'candle_index': i
                        })
        
        return liquidity_sweeps
    
    def calculate_fibonacci_levels(self, start_price: float, end_price: float) -> Dict[float, float]:
        """
        Calculate fibonacci retracement levels
        """
        diff = abs(end_price - start_price)
        levels = {}
        
        # Common fibonacci levels
        fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
        
        if start_price <= end_price:  # Uptrend
            for level in fib_levels:
                levels[level] = start_price + (diff * level)
        else:  # Downtrend
            for level in fib_levels:
                levels[level] = start_price - (diff * level)
        
        return levels
    
    def detect_trend(self, closes: List[float], ma_period: int = 20) -> str:
        """
        Detect market trend based on moving average
        """
        if len(closes) < ma_period:
            return "RANGE"
        
        ma = sum(closes[-ma_period:]) / ma_period
        current_price = closes[-1]
        
        if current_price > ma:
            return "BULLISH"
        elif current_price < ma:
            return "BEARISH"
        else:
            return "RANGE"
    
    def analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        """
        Main analysis function that combines all SMC elements
        """
        highs = df['high'].tolist()
        lows = df['low'].tolist()
        closes = df['close'].tolist()
        opens = df['open'].tolist()
        
        # Detect swings
        swing_highs, swing_lows = self.detect_swings(highs, lows)
        
        # Detect fractals
        bullish_fractals, bearish_fractals = self.detect_fractals(highs, lows)
        
        # Detect BOS/CHOCH
        bos_choch = self.detect_bos_choch(swing_highs, swing_lows)
        
        # Detect FVGs
        fvg_zones = self.detect_fvg(opens, highs, lows, closes)
        
        # Detect order blocks
        order_blocks = self.detect_order_blocks(highs, lows, swing_highs, swing_lows)
        
        # Detect liquidity sweeps
        liquidity_sweeps = self.detect_liquidity_sweeps(highs, lows, swing_highs, swing_lows)
        
        # Determine trend
        trend = self.detect_trend(closes)
        
        # Calculate fibonacci levels based on recent swing points
        fib_levels = {}
        if len(swing_highs) > 0 and len(swing_lows) > 0:
            # Use the most recent swing high and low for fibonacci calculation
            recent_swing_high = max(swing_highs, key=lambda x: x['index'])['price']
            recent_swing_low = max(swing_lows, key=lambda x: x['index'])['price']
            fib_levels = self.calculate_fibonacci_levels(recent_swing_low, recent_swing_high)
        
        # Determine signal bias
        bias = "NEUTRAL"
        entry = None
        sl = None
        tp = None
        
        # Determine bias based on recent BOS/CHOCH
        if len(bos_choch['bullish_bos']) > 0:
            recent_bos = bos_choch['bullish_bos'][-1]
            if recent_bos['price'] <= closes[-1]:  # Current price is above BOS level
                bias = "BUY"
                # Set entry, stop loss, and take profit
                entry = recent_bos['price']
                # Find the most recent swing low for stop loss
                if len(swing_lows) > 0:
                    recent_swing_low = max(swing_lows, key=lambda x: x['index'])
                    sl = recent_swing_low['price'] - (abs(recent_bos['price'] - recent_swing_low['price']) * 0.2)  # 20% below for safety
                # Take profit at next fibonacci level or 2:1 risk reward
                if 0.618 in fib_levels:
                    tp = fib_levels[0.618]
                else:
                    tp = entry + 2 * abs(entry - sl) if sl else entry + (recent_bos['price'] - closes[-1]) * 2
        
        if len(bos_choch['bearish_bos']) > 0:
            recent_bos = bos_choch['bearish_bos'][-1]
            if recent_bos['price'] >= closes[-1]:  # Current price is below BOS level
                bias = "SELL"
                # Set entry, stop loss, and take profit
                entry = recent_bos['price']
                # Find the most recent swing high for stop loss
                if len(swing_highs) > 0:
                    recent_swing_high = max(swing_highs, key=lambda x: x['index'])
                    sl = recent_swing_high['price'] + (abs(recent_swing_high['price'] - recent_bos['price']) * 0.2)  # 20% above for safety
                # Take profit at next fibonacci level or 2:1 risk reward
                if 0.382 in fib_levels:
                    tp = fib_levels[0.382]
                else:
                    tp = entry - 2 * abs(entry - sl) if sl else entry - (closes[-1] - recent_bos['price']) * 2
        
        # Check for CHOCH signals as well
        if bias == "NEUTRAL":
            if len(bos_choch['bullish_choch']) > 0:
                recent_choch = bos_choch['bullish_choch'][-1]
                if recent_choch['price'] <= closes[-1] and recent_choch['price'] > closes[-5]:  # Recent move up
                    bias = "BUY"
                    entry = recent_choch['price']
            
            if len(bos_choch['bearish_choch']) > 0:
                recent_choch = bos_choch['bearish_choch'][-1]
                if recent_choch['price'] >= closes[-1] and recent_choch['price'] < closes[-5]:  # Recent move down
                    bias = "SELL"
                    entry = recent_choch['price']
        
        # Check for FVG signals
        if bias == "NEUTRAL" and len(fvg_zones) > 0:
            # Look for most recent FVG
            recent_fvg = fvg_zones[-1]
            if recent_fvg['type'] == 'bullish_fvg' and closes[-1] > recent_fvg['low']:
                bias = "BUY"
                entry = recent_fvg['entry']
            elif recent_fvg['type'] == 'bearish_fvg' and closes[-1] < recent_fvg['high']:
                bias = "SELL"
                entry = recent_fvg['entry']
        
        # Check for order block signals
        if bias == "NEUTRAL" and len(order_blocks) > 0:
            # Look for most recently formed order block
            recent_ob = order_blocks[-1]
            if recent_ob['type'] == 'bullish_order_block' and closes[-1] > recent_ob['price']:
                bias = "BUY"
                entry = recent_ob['price']
            elif recent_ob['type'] == 'bearish_order_block' and closes[-1] < recent_ob['price']:
                bias = "SELL"
                entry = recent_ob['price']
        
        # Determine liquidity sweep status
        liquidity_swept = len(liquidity_sweeps) > 0
        
        # Create explanation
        explanation_parts = []
        if len(bos_choch['bullish_bos']) > 0:
            explanation_parts.append("Bullish BOS detected")
        if len(bos_choch['bearish_bos']) > 0:
            explanation_parts.append("Bearish BOS detected")
        if len(fvg_zones) > 0:
            explanation_parts.append("FVG zones identified")
        if len(order_blocks) > 0:
            explanation_parts.append("Order blocks detected")
        if liquidity_swept:
            explanation_parts.append("Recent liquidity sweep")
        
        explanation = "; ".join(explanation_parts) if explanation_parts else "No clear SMC patterns detected"
        
        return {
            "trend": trend,
            "bos": {
                "bullish": bos_choch['bullish_bos'],
                "bearish": bos_choch['bearish_bos']
            },
            "choch": {
                "bullish": bos_choch['bullish_choch'],
                "bearish": bos_choch['bearish_choch']
            },
            "fvgZones": fvg_zones,
            "orderBlocks": order_blocks,
            "liquiditySwept": liquidity_swept,
            "liquiditySweeps": liquidity_sweeps,
            "fractals": {
                "bullish": bearish_fractals,
                "bearish": bullish_fractals
            },
            "swingPoints": {
                "highs": swing_highs,
                "lows": swing_lows
            },
            "fibonacciLevels": fib_levels,
            "bias": bias,
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "current_price": closes[-1],
            "explanation": explanation
        }


# For testing purposes
def test_smc_engine():
    # Create sample data
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(100) * 0.1)
    highs = prices + np.random.rand(100) * 0.5
    lows = prices - np.random.rand(100) * 0.5
    opens = prices - np.random.rand(100) * 0.25
    closes = prices + np.random.rand(100) * 0.25
    
    df = pd.DataFrame({
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes
    })
    
    engine = SMCEngine()
    result = engine.analyze_market_structure(df)
    
    print("SMC Analysis Result:")
    print(f"Trend: {result['trend']}")
    print(f"Bias: {result['bias']}")
    print(f"Entry: {result['entry']}")
    print(f"Stop Loss: {result['sl']}")
    print(f"Take Profit: {result['tp']}")
    print(f"Explanation: {result['explanation']}")
    
    return result


if __name__ == "__main__":
    test_smc_engine()