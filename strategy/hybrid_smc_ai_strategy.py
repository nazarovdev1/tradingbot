import backtrader as bt
import numpy as np
import pandas as pd
from typing import Dict, List

# Import our SMC and AI modules
from smc_engine.smc import SMCAnalyzer
from ai_engine.predict import PredictionEngine


class HybridSMCAIStrategy(bt.Strategy):
    """
    Hybrid SMC + AI Strategy with Risk Management
    """
    
    params = (
        ('printlog', True),
        ('risk_per_trade', 0.02),  # 2% risk per trade
        ('max_risk_allowed', 40),  # Maximum risk score allowed
        ('atr_period', 14),
        ('ema200_period', 200),
        ('ema50_period', 50),
        ('rsi_period', 14),
        ('atr_baseline_lookback', 10),
        ('risk_reward', 2.0),  # 1:2 risk/reward ratio
        ('lookback_period', 20),
    )
    
    def __init__(self):
        # Initialize indicators
        self.atr = bt.indicators.ATR(self.data, period=self.params.atr_period)
        self.ema200 = bt.indicators.EMA(self.data, period=self.params.ema200_period)
        self.ema50 = bt.indicators.EMA(self.data, period=self.params.ema50_period)
        self.rsi = bt.indicators.RSI(self.data, period=self.params.rsi_period, safediv=True)
        
        # Initialize SMC and AI engines
        self.smc_analyzer = SMCAnalyzer(lookback_period=self.params.lookback_period)
        self.ai_engine = PredictionEngine()
        
        # Track position state
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
        # Track trade history
        self.trades_list = []
        
        # Data history for analysis
        self.data_history = {'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
    
    def log(self, txt, dt=None, force=False):
        """Logging function"""
        if self.params.printlog or force:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} - {txt}')
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            # Order submitted/accepted - nothing to do
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.log(f'BUY EXECUTED: Price: {order.executed.price:.4f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            
            elif order.issell():
                self.log(f'SELL EXECUTED: Price: {order.executed.price:.4f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            
            # Reset order
            self.order = None
        
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            self.order = None
    
    def notify_trade(self, trade):
        """Handle trade notifications"""
        if trade.isclosed:
            trade_info = {
                'pnl': trade.pnl,
                'pnl_percentage': trade.pnlcomm,
                'entry_price': trade.price,
                'exit_price': trade.value / trade.size if trade.size != 0 else 0,  # Calculate exit price
                'size': abs(trade.size),
                'entry_datetime': self.data.datetime.datetime(),
                'exit_datetime': self.data.datetime.datetime(),
                'trade_id': len(getattr(self, 'trades_list', [])) + 1
            }

            if not hasattr(self, 'trades_list'):
                self.trades_list = []

            self.trades_list.append(trade_info)
            self.log(f'OPERATION PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}')
    
    def next(self):
        """Main strategy logic"""
        # Update data history
        self.data_history['open'].append(self.data.open[0])
        self.data_history['high'].append(self.data.high[0])
        self.data_history['low'].append(self.data.low[0])
        self.data_history['close'].append(self.data.close[0])
        self.data_history['volume'].append(self.data.volume[0] if len(self.data) > 0 and self.data.volume[0] >= 0 else 0)

        # Keep history at appropriate length
        max_len = max(200, self.params.lookback_period * 5)  # Keep enough data for SMC analysis
        for key in self.data_history:
            if len(self.data_history[key]) > max_len:
                self.data_history[key] = self.data_history[key][-max_len:]

        # Skip if not enough data
        if len(self.data_history['close']) < 50:  # Increased minimum for more reliable signals
            return

        # Check if an order is pending
        if self.order:
            return

        # Check if in position
        if self.position:
            return

        # Generate signal
        signal = self.generate_signal()

        # Execute trades based on signal
        if signal == 'BUY' and not self.position:
            # Calculate position size based on risk management
            risk_amount = self.broker.getvalue() * self.params.risk_per_trade
            sl_price = self.calculate_stop_loss('BUY')

            if sl_price and risk_amount > 0:
                # Calculate position size based on ATR for better risk management
                atr_val = self.atr[0]
                if atr_val > 0:
                    risk_distance = abs(self.data.close[0] - sl_price)
                    if risk_distance > 0:
                        size = risk_amount / risk_distance
                    else:
                        # If we can't calculate risk distance, use a default based on ATR
                        size = risk_amount / (atr_val * 1.5)
                else:
                    size = risk_amount / 0.001  # Default fallback

                self.order = self.buy(size=size)

                # Place stop loss order
                if sl_price:
                    self.sell(exectype=bt.Order.Stop, price=sl_price, size=size, trailamount=None)

                # Place take profit order
                tp_price = self.calculate_take_profit('BUY', self.data.close[0], sl_price)
                if tp_price:
                    self.sell(exectype=bt.Order.Limit, price=tp_price, size=size)

        elif signal == 'SELL' and not self.position:
            # Calculate position size based on risk management
            risk_amount = self.broker.getvalue() * self.params.risk_per_trade
            sl_price = self.calculate_stop_loss('SELL')

            if sl_price and risk_amount > 0:
                # Calculate position size based on ATR for better risk management
                atr_val = self.atr[0]
                if atr_val > 0:
                    risk_distance = abs(self.data.close[0] - sl_price)
                    if risk_distance > 0:
                        size = risk_amount / risk_distance
                    else:
                        # If we can't calculate risk distance, use a default based on ATR
                        size = risk_amount / (atr_val * 1.5)
                else:
                    size = risk_amount / 0.001  # Default fallback

                self.order = self.sell(size=size)

                # Place stop loss order
                if sl_price:
                    self.buy(exectype=bt.Order.Stop, price=sl_price, size=size, trailamount=None)

                # Place take profit order
                tp_price = self.calculate_take_profit('SELL', self.data.close[0], sl_price)
                if tp_price:
                    self.buy(exectype=bt.Order.Limit, price=tp_price, size=size)
    
    def generate_signal(self) -> str:
        """
        Generate trading signal based on SMC + AI + Risk analysis
        """
        # Get SMC analysis
        smc_signal = self.apply_smc_filters()
        
        # Get AI prediction
        ai_signal = self.apply_ai_filters()
        
        # Get risk assessment
        risk_ok = self.apply_risk_filters()
        
        # Only proceed if risk is acceptable
        if not risk_ok:
            return 'NEUTRAL'
        
        # Combine signals according to priority
        if smc_signal == 'NEUTRAL' and ai_signal == 'NEUTRAL':
            return 'NEUTRAL'
        elif smc_signal != 'NEUTRAL' and ai_signal != 'NEUTRAL':
            # Both signals agree
            if smc_signal == ai_signal:
                return smc_signal
            else:
                # Conflict: SMC > AI
                return smc_signal
        elif smc_signal != 'NEUTRAL':
            # Only SMC has a signal: use SMC
            return smc_signal
        elif ai_signal != 'NEUTRAL':
            # Only AI has a signal: use AI
            return ai_signal
        else:
            return 'NEUTRAL'
    
    def apply_smc_filters(self) -> str:
        """
        Apply SMC-based filters to generate signal
        """
        try:
            # Create DataFrame for SMC analysis
            df = pd.DataFrame({
                'open': self.data_history['open'],
                'high': self.data_history['high'],
                'low': self.data_history['low'],
                'close': self.data_history['close']
            })
            
            # Run SMC analysis
            smc_result = self.smc_analyzer.analyze(df)
            
            # Determine bias from SMC elements
            bias = smc_result.get('bias', 'NEUTRAL')
            
            return bias
        except Exception as e:
            self.log(f"Error in SMC analysis: {e}")
            return 'NEUTRAL'
    
    def apply_ai_filters(self) -> str:
        """
        Apply AI-based filters to generate signal
        """
        try:
            # Get AI prediction
            closes = self.data_history['close']
            prediction = self.ai_engine.get_prediction(closes)
            
            return prediction['signal']
        except Exception as e:
            self.log(f"Error in AI prediction: {e}")
            return 'NEUTRAL'
    
    def apply_risk_filters(self) -> bool:
        """
        Apply risk management filters
        """
        current_price = self.data.close[0]

        # Check if we have enough indicator data
        if len(self.data_history['close']) < 200 or len(self) < 200:
            return False

        # Calculate deviation from EMA200
        ema200_val = self.ema200[0] if len(self.ema200) > 0 else self.data.close[-200]
        ema50_val = self.ema50[0] if len(self.ema50) > 0 else self.data.close[-50]
        rsi_val = self.rsi[0] if len(self.rsi) > 0 else 50
        atr_val = self.atr[0] if len(self.atr) > 0 else 0.001

        deviation = abs(current_price - ema200_val) / ema200_val if ema200_val != 0 else 0

        # Calculate ATR-based risk (get the baseline from historical ATR values)
        atr_values = []
        for i in range(1, min(self.params.atr_baseline_lookback + 1, len(self.atr))):
            if len(self.atr) >= i and not np.isnan(self.atr[-i]):
                atr_values.append(self.atr[-i])

        if atr_values:
            atr_baseline = np.mean(atr_values)
            atr_ratio = atr_val / atr_baseline if atr_baseline > 0 else 1
        else:
            atr_ratio = 1  # Default to 1 if we don't have historical ATR data

        # Risk scoring logic
        deviation_threshold = 0.005  # 0.5% pullback zone
        breakout_threshold = 0.012  # 1.2% extension
        atr_min_ratio = 0.8
        atr_max_ratio = 1.8
        rsi_buy_ready = 42 <= rsi_val <= 65 and rsi_val < 70
        rsi_sell_ready = 35 <= rsi_val <= 58 and rsi_val > 30

        # Calculate risk score components
        deviation_range = max(breakout_threshold - deviation_threshold, 0.0001)
        deviation_penalty = max(0, deviation - deviation_threshold)
        deviation_score = min(deviation_penalty / deviation_range, 1) * 40

        rsi_mid_distance = max(0, abs(rsi_val - 50) - 10)  # outside 40-60 zone adds risk
        rsi_score = min(rsi_mid_distance / 40, 1) * 35

        atr_score = 0
        if atr_ratio < atr_min_ratio:
            atr_score = min((atr_min_ratio - atr_ratio) / atr_min_ratio, 1) * 25
        elif atr_ratio > atr_max_ratio:
            atr_score = min((atr_ratio - atr_max_ratio) / atr_max_ratio, 1) * 25

        raw_risk = deviation_score + rsi_score + atr_score
        risk_score = min(float(raw_risk), 100)

        # Additional structure checks
        up_trend = current_price > ema200_val
        down_trend = current_price < ema200_val
        atr_healthy = atr_ratio >= 0.7 and atr_ratio <= 2.2
        short_trend_up = current_price > ema50_val and ema50_val > ema200_val
        short_trend_down = current_price < ema50_val and ema50_val < ema200_val

        # Additional checks for setup quality
        momentum_extension_cap = 0.018
        within_momentum_extension = deviation <= momentum_extension_cap

        buy_structure_ready = (deviation <= deviation_threshold or
                              (deviation <= breakout_threshold and atr_ratio >= 1) or
                              (short_trend_up and within_momentum_extension))

        sell_structure_ready = (deviation <= deviation_threshold or
                               (deviation <= breakout_threshold and atr_ratio >= 1) or
                               (short_trend_down and within_momentum_extension))

        setup_clean = atr_healthy

        # Final risk assessment
        risk_ok = risk_score <= self.params.max_risk_allowed
        trend_aligned = (up_trend and rsi_buy_ready and buy_structure_ready) or \
                       (down_trend and rsi_sell_ready and sell_structure_ready)

        return risk_ok and setup_clean and trend_aligned
    
    def calculate_stop_loss(self, direction: str) -> float:
        """
        Calculate stop loss based on SMC levels (swing highs/lows)
        """
        try:
            # Create DataFrame for SMC analysis
            df = pd.DataFrame({
                'open': self.data_history['open'][-50:],  # Look at recent 50 candles
                'high': self.data_history['high'][-50:],
                'low': self.data_history['low'][-50:],
                'close': self.data_history['close'][-50:]
            })
            
            # Run SMC analysis on recent data to find swing points
            smc_result = self.smc_analyzer.analyze(df)
            
            current_price = self.data.close[0]
            
            if direction == 'BUY':
                # For BUY, SL should be below recent swing low
                if smc_result['swing_lows']:
                    # Get the most recent swing low
                    recent_swing_low = max(smc_result['swing_lows'], key=lambda x: x['index'])
                    # Set SL slightly below the swing low
                    sl_distance = abs(current_price - recent_swing_low['price']) * 0.1  # 10% of move
                    return recent_swing_low['price'] - sl_distance
                else:
                    # If no swing low found, use ATR-based SL
                    atr_val = self.atr[0]
                    return current_price - (atr_val * 1.5)
            
            elif direction == 'SELL':
                # For SELL, SL should be above recent swing high
                if smc_result['swing_highs']:
                    # Get the most recent swing high
                    recent_swing_high = max(smc_result['swing_highs'], key=lambda x: x['index'])
                    # Set SL slightly above the swing high
                    sl_distance = abs(recent_swing_high['price'] - current_price) * 0.1  # 10% of move
                    return recent_swing_high['price'] + sl_distance
                else:
                    # If no swing high found, use ATR-based SL
                    atr_val = self.atr[0]
                    return current_price + (atr_val * 1.5)
            
            return None
        except Exception as e:
            self.log(f"Error calculating stop loss: {e}")
            return None
    
    def calculate_take_profit(self, direction: str, entry_price: float, sl_price: float) -> float:
        """
        Calculate take profit based on risk-reward ratio
        """
        if not sl_price:
            # If no SL price, use default based on ATR
            atr_val = self.atr[0]
            if direction == 'BUY':
                return entry_price + (atr_val * self.params.risk_reward * 1.5)
            else:
                return entry_price - (atr_val * self.params.risk_reward * 1.5)
        
        risk = abs(entry_price - sl_price)
        reward = risk * self.params.risk_reward
        
        if direction == 'BUY':
            return entry_price + reward
        else:
            return entry_price - reward
    
    def stop(self):
        """
        Called when backtesting is stopped
        """
        self.log(f'Final Portfolio Value: {self.broker.getvalue():.2f}')