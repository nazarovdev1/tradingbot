import pandas as pd
import numpy as np
from scipy.special import expit  # sigmoid function
import json
from datetime import datetime
import matplotlib.pyplot as plt


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_atr(high, low, close, period=14):
    """Calculate Average True Range"""
    high_low = high - low
    high_close = np.abs(high - close.shift())
    low_close = np.abs(low - close.shift())
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    return atr


def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices, period):
    """Calculate Exponential Moving Average"""
    return prices.ewm(span=period, adjust=False).mean()


def sigmoid(x):
    """Sigmoid activation function"""
    return expit(x)


# Load the dataset
df = pd.read_csv('sample_data_extended.csv')

# Convert datetime column to datetime type
df['datetime'] = pd.to_datetime(df['datetime'])

# Calculate indicators
df['EMA50'] = calculate_ema(df['close'], 50)
df['EMA200'] = calculate_ema(df['close'], 200)
df['RSI14'] = calculate_rsi(df['close'], 14)
df['ATR14'] = calculate_atr(df['high'], df['low'], df['close'], 14)
df['HL2'] = (df['high'] + df['low']) / 2
df['SMA20'] = calculate_sma(df['close'], 20)
df['Volatility'] = df['close'].rolling(window=20).std()

# Generate AI features
df['price_change_pct'] = df['close'].pct_change()
df['candle_body_size'] = abs(df['close'] - df['open']) / df['close']
df['upper_wick_size'] = (df['high'] - np.maximum(df['open'], df['close'])) / df['close']
df['lower_wick_size'] = (np.minimum(df['open'], df['close']) - df['low']) / df['close']
df['rolling_volume_mean'] = df['volume'].rolling(window=20).mean()
df['normalized_volume'] = df['volume'] / df['rolling_volume_mean']
df['rolling_close_mean'] = df['close'].rolling(window=20).mean()
df['rolling_high_low_range'] = (df['high'] - df['low']).rolling(window=20).mean()
df['momentum'] = df['close'] - df['close'].shift(10)

# Fill NaN values
df.fillna(method='bfill', inplace=True)
df.fillna(method='ffill', inplace=True)

# Generate AI signal probabilities
ema_ratio = (df['EMA50'] - df['EMA200']) / df['EMA200'] * 10
rsi_scaled = df['RSI14'] / 10
combo_signal = ema_ratio + rsi_scaled

df['ai_buy_prob'] = sigmoid(combo_signal)
df['ai_sell_prob'] = 1 - df['ai_buy_prob']

# Generate signals based on probabilities and conditions
buy_condition = (df['ai_buy_prob'] > 0.55) & (df['EMA50'] > df['EMA200'])
sell_condition = (df['ai_sell_prob'] > 0.55) & (df['EMA50'] < df['EMA200'])

df['signal'] = 'NONE'
df.loc[buy_condition, 'signal'] = 'BUY'
df.loc[sell_condition, 'signal'] = 'SELL'

# Save the enhanced dataset
df.to_csv('dataset_with_indicators.csv', index=False)


# Run optimized backtest
def run_backtest(df, risk_per_trade=0.02, tp_multiplier=2, sl_multiplier=1):
    # Initialize variables
    balance = 10000.0  # Starting balance
    position = None
    entry_price = None
    trade_count = 0
    wins = 0
    losses = 0
    pnl_list = []
    balance_history = [balance]
    
    tp_pct = df['ATR14'] / df['close'] * tp_multiplier
    sl_pct = df['ATR14'] / df['close'] * sl_multiplier
    
    for i in range(1, len(df)):
        current_signal = df.iloc[i]['signal']
        current_price = df.iloc[i]['close']
        
        # Check if we have an open position
        if position is not None:
            # Calculate exit conditions
            if position == 'BUY':
                take_profit = entry_price * (1 + tp_pct.iloc[i])
                stop_loss = entry_price * (1 - sl_pct.iloc[i])
                
                if current_price >= take_profit or current_price <= stop_loss:
                    # Exit position
                    pnl = balance * risk_per_trade * (1 if current_price >= take_profit else -1)
                    balance += pnl
                    pnl_list.append(pnl)
                    
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                        
                    position = None
                    entry_price = None
                    trade_count += 1
            elif position == 'SELL':
                take_profit = entry_price * (1 - tp_pct.iloc[i])
                stop_loss = entry_price * (1 + sl_pct.iloc[i])
                
                if current_price <= take_profit or current_price >= stop_loss:
                    # Exit position
                    pnl = balance * risk_per_trade * (1 if current_price <= take_profit else -1)
                    balance += pnl
                    pnl_list.append(pnl)
                    
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                        
                    position = None
                    entry_price = None
                    trade_count += 1
        
        # Check if we should enter a new position
        if position is None:
            if current_signal == 'BUY':
                position = 'BUY'
                entry_price = current_price
            elif current_signal == 'SELL':
                position = 'SELL'
                entry_price = current_price
        
        # Record balance for equity curve
        balance_history.append(balance)
    
    # Calculate performance metrics
    total_return = (balance - 10000.0) / 10000.0
    win_rate = wins / trade_count if trade_count > 0 else 0
    profit_factor = sum(p for p in pnl_list if p > 0) / abs(sum(p for p in pnl_list if p < 0)) if sum(p for p in pnl_list if p < 0) != 0 else float('inf')
    
    # Calculate Sharpe ratio (simplified, using daily returns)
    if len(pnl_list) > 1:
        daily_returns = np.diff(balance_history) / np.array(balance_history[:-1])
        excess_returns = daily_returns - 0.0002  # Subtract risk-free rate (simplified)
        if np.std(excess_returns) != 0:
            sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
    else:
        sharpe_ratio = 0
    
    # Calculate max drawdown
    cumulative = np.array(balance_history)
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
    
    # Create results dictionary
    results = {
        'total_trades': trade_count,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'total_return': total_return,
        'final_balance': balance,
        'initial_balance': 10000.0,
        'pnl': sum(pnl_list)
    }
    
    return results, balance_history


# Run the backtest
backtest_results, balance_history = run_backtest(df)

# Save backtest results to JSON
with open('optimized_backtest_results.json', 'w') as f:
    json.dump(backtest_results, f, indent=2)

# Create equity curve plot
plt.figure(figsize=(14, 8))
plt.plot(balance_history)
plt.title('Equity Curve - Optimized Backtest')
plt.xlabel('Time Period')
plt.ylabel('Balance ($)')
plt.grid(True)
plt.savefig('equity_curve_optimized.png')
plt.close()

print("Dataset with indicators saved to 'dataset_with_indicators.csv'")
print("Backtest results saved to 'optimized_backtest_results.json'")
print("Equity curve saved to 'equity_curve_optimized.png'")
print("Backtest Summary:")
print(f"Total Trades: {backtest_results['total_trades']}")
print(f"Wins: {backtest_results['wins']}, Losses: {backtest_results['losses']}")
print(f"Win Rate: {backtest_results['win_rate']:.2%}")
print(f"Profit Factor: {backtest_results['profit_factor']:.2f}")
print(f"Sharpe Ratio: {backtest_results['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {backtest_results['max_drawdown']:.2%}")
print(f"Total Return: {backtest_results['total_return']:.2%}")
print(f"Final Balance: ${backtest_results['final_balance']:.2f}")