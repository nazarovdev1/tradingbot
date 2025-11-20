import pandas as pd
import backtrader as bt
from datetime import datetime
from typing import Dict, List
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

# Add project root to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategy.hybrid_smc_ai_strategy import HybridSMCAIStrategy


class DataLoader:
    """
    Loads and prepares data for backtesting
    """
    
    def __init__(self, data_path: str, datetime_col: str = 'datetime', 
                 open_col: str = 'open', high_col: str = 'high', 
                 low_col: str = 'low', close_col: str = 'close', 
                 volume_col: str = 'volume'):
        self.data_path = data_path
        self.datetime_col = datetime_col
        self.open_col = open_col
        self.high_col = high_col
        self.low_col = low_col
        self.close_col = close_col
        self.volume_col = volume_col
    
    def load_data(self) -> pd.DataFrame:
        """
        Load data from CSV file and prepare it for backtesting
        """
        # Load the data
        df = pd.read_csv(self.data_path)
        
        # Convert datetime column to datetime type
        df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
        
        # Sort by datetime
        df = df.sort_values(by=self.datetime_col)

        # Ensure minimum high-low range to avoid ATR division by zero
        # Add epsilon to high if range is too small
        diff = df[self.high_col] - df[self.low_col]
        df.loc[diff < 0.01, self.high_col] = df.loc[diff < 0.01, self.low_col] + 0.01
        
        # Ensure required columns exist
        required_cols = [self.datetime_col, self.open_col, self.high_col, 
                        self.low_col, self.close_col, self.volume_col]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in data")
        
        # Rename columns to standard names
        df_renamed = df.rename(columns={
            self.datetime_col: 'datetime',
            self.open_col: 'open',
            self.high_col: 'high',
            self.low_col: 'low',
            self.close_col: 'close',
            self.volume_col: 'volume'
        })
        
        # Ensure no missing values in OHLCV
        df_renamed = df_renamed.dropna(subset=['open', 'high', 'low', 'close', 'volume'])
        
        # Ensure numeric types
        for col in ['open', 'high', 'low', 'close']:
            df_renamed[col] = pd.to_numeric(df_renamed[col], errors='coerce')
        
        df_renamed['volume'] = pd.to_numeric(df_renamed['volume'], errors='coerce')
        
        # Drop any remaining NaN values after conversion
        df_renamed = df_renamed.dropna()

        # Fix for RSI division by zero: ensure some movement in close price
        # If close price is exactly same as previous, add a tiny epsilon
        # This prevents RSI calculation from dividing by zero when avg loss is 0
        close_diff = df_renamed['close'].diff()
        # Find where difference is exactly 0
        zero_diff_mask = (close_diff == 0)
        if zero_diff_mask.any():
            # Add a tiny random noise to these zero-change days
            # 1e-5 is small enough not to affect PnL but big enough for float division
            noise = np.random.uniform(1e-6, 1e-5, size=zero_diff_mask.sum())
            df_renamed.loc[zero_diff_mask, 'close'] += noise
            
            # Also ensure High/Low encompass this new Close
            df_renamed.loc[zero_diff_mask, 'high'] = np.maximum(df_renamed.loc[zero_diff_mask, 'high'], df_renamed.loc[zero_diff_mask, 'close'])
            df_renamed.loc[zero_diff_mask, 'low'] = np.minimum(df_renamed.loc[zero_diff_mask, 'low'], df_renamed.loc[zero_diff_mask, 'close'])
        
        return df_renamed


def execute_backtest(data_path: str, strategy_params: Dict = None,
                initial_cash: float = 10000, commission: float = 0.001) -> Dict:
    """
    Run the complete backtest
    """
    # Initialize Cerebro
    cerebro = bt.Cerebro()

    # Load data
    data_loader = DataLoader(data_path)
    df = data_loader.load_data()

    # Create a PandasData feed
    data_feed = bt.feeds.PandasData(
        dataname=df,
        datetime='datetime',
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1  # -1 means no open interest column
    )

    # Add data to cerebro
    cerebro.adddata(data_feed)

    # Set initial cash
    cerebro.broker.setcash(initial_cash)

    # Set commission
    cerebro.broker.setcommission(commission=commission)

    # Add strategy with parameters
    params = strategy_params or {}
    cerebro.addstrategy(HybridSMCAIStrategy, **params)

    # Add observers for metrics
    cerebro.addobserver(bt.observers.BuySell)
    cerebro.addobserver(bt.observers.Value)
    cerebro.addobserver(bt.observers.Trades)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')

    # Run the backtest
    results = cerebro.run()

    # Get the strategy instance to access trades
    strat = results[0]

    # Collect results
    final_value = cerebro.broker.getvalue()
    initial_value = initial_cash

    # Get analyzers
    sharpe = strat.analyzers.sharpe.get_analysis()
    drawdown = strat.analyzers.drawdown.get_analysis()
    tradeanalyzer = strat.analyzers.tradeanalyzer.get_analysis()
    annual_return = strat.analyzers.annual_return.get_analysis()
    returns = strat.analyzers.returns.get_analysis()

    # Calculate metrics
    total_return = (final_value - initial_value) / initial_value
    sharpe_ratio = sharpe.get('sharperatio', 0)  # Will be None if no trades
    if sharpe_ratio is None:
        sharpe_ratio = 0

    max_drawdown = drawdown.get('max', {}).get('drawdown', 0) / 100 if drawdown else 0

    # Trade statistics
    total_trades = tradeanalyzer.get('total', {}).get('total', 0) if tradeanalyzer else 0
    winning_trades = tradeanalyzer.get('won', {}).get('total', 0) if tradeanalyzer else 0
    losing_trades = tradeanalyzer.get('lost', {}).get('total', 0) if tradeanalyzer else 0
    win_rate = winning_trades / total_trades if total_trades > 0 else 0

    # Profit factor
    total_won = tradeanalyzer.get('won', {}).get('pnl', {}).get('total', 0) if tradeanalyzer else 0
    total_lost = abs(tradeanalyzer.get('lost', {}).get('pnl', {}).get('total', 0)) if tradeanalyzer else 0
    profit_factor = total_won / total_lost if total_lost > 0 else float('inf') if total_won > 0 else 0

    # Prepare the result dictionary
    results_dict = {
        'initial_value': initial_value,
        'final_value': final_value,
        'total_return': total_return,
        'sharpe_ratio': sharpe_ratio,
        'max_drawdown': max_drawdown,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'pnl': final_value - initial_value,
        'trades_list': getattr(strat, 'trades_list', []) if hasattr(strat, 'trades_list') else [],
        'strategy_params': params
    }

    return cerebro, results_dict


def plot_results(cerebro, output_path: str = 'backtest_results.png'):
    """
    Plot the backtest results
    """
    fig = cerebro.plot()[0][0]
    fig.savefig(output_path)
    plt.close(fig)  # Close the figure to free memory
    print(f"Plot saved to {output_path}")


def save_results_to_csv(results_dict: Dict, output_path: str = 'backtest_results.csv'):
    """
    Save backtest results to CSV
    """
    import csv
    
    # Save summary metrics
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['metric', 'value']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerow({'metric': 'Initial Value', 'value': results_dict['initial_value']})
        writer.writerow({'metric': 'Final Value', 'value': results_dict['final_value']})
        writer.writerow({'metric': 'Total Return', 'value': f"{results_dict['total_return']:.4f}"})
        writer.writerow({'metric': 'Sharpe Ratio', 'value': f"{results_dict['sharpe_ratio']:.4f}"})
        writer.writerow({'metric': 'Max Drawdown', 'value': f"{results_dict['max_drawdown']:.4f}"})
        writer.writerow({'metric': 'Total Trades', 'value': results_dict['total_trades']})
        writer.writerow({'metric': 'Winning Trades', 'value': results_dict['winning_trades']})
        writer.writerow({'metric': 'Losing Trades', 'value': results_dict['losing_trades']})
        writer.writerow({'metric': 'Win Rate', 'value': f"{results_dict['win_rate']:.4f}"})
        writer.writerow({'metric': 'Profit Factor', 'value': f"{results_dict['profit_factor']:.4f}"})
        writer.writerow({'metric': 'PNL', 'value': f"{results_dict['pnl']:.2f}"})
    
    print(f"Summary results saved to {output_path}")
    
    # Save individual trades if any
    if results_dict['trades_list']:
        trades_path = output_path.replace('.csv', '_trades.csv')
        trades_df = pd.DataFrame(results_dict['trades_list'])
        trades_df.to_csv(trades_path, index=False)
        print(f"Individual trades saved to {trades_path}")


def save_results_to_json(results_dict: Dict, output_path: str = 'backtest_results.json'):
    """
    Save backtest results to JSON
    """
    import json
    
    # Convert numpy types to Python native types for JSON serialization
    def convert_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [convert_types(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: convert_types(value) for key, value in obj.items()}
        else:
            return obj
    
    serializable_results = convert_types(results_dict)
    
    with open(output_path, 'w') as jsonfile:
        json.dump(serializable_results, jsonfile, indent=2, default=str)
    
    print(f"Results saved to {output_path}")
