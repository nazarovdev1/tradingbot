import backtrader as bt
import matplotlib.pyplot as plt
import pandas as pd
from typing import Dict, Any
import sys
import os

# Add project root to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def plot_equity_curve(cerebro: bt.Cerebro, output_path: str = 'equity_curve.png') -> None:
    """
    Plot the equity curve from backtest results
    """
    # Run the strategy to get data for plotting
    fig = cerebro.plot(figsize=(14, 8))[0][0]
    
    # Customize the plot
    fig.suptitle('Backtest Equity Curve - Hybrid SMC + AI Strategy', fontsize=16)
    
    # Save the plot
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)  # Close the figure to free memory
    
    print(f"Equity curve saved to {output_path}")


def plot_trade_analysis(results_dict: Dict[str, Any], output_path: str = 'trade_analysis.png') -> None:
    """
    Plot trade analysis (PnL distribution, etc.)
    """
    trades_list = results_dict.get('trades_list', [])
    
    if not trades_list:
        print("No trades to plot.")
        return
    
    trades_df = pd.DataFrame(trades_list)
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Trade Analysis - Hybrid SMC + AI Strategy', fontsize=16)
    
    # Plot 1: PnL distribution histogram
    axes[0, 0].hist(trades_df['pnl'], bins=20, edgecolor='black')
    axes[0, 0].set_title('Distribution of Trade PnL')
    axes[0, 0].set_xlabel('PnL')
    axes[0, 0].set_ylabel('Frequency')
    
    # Plot 2: Cumulative PnL over time
    if 'entry_datetime' in trades_df.columns:
        # Convert datetime if needed and sort
        trades_df['entry_datetime'] = pd.to_datetime(trades_df['entry_datetime'])
        trades_df = trades_df.sort_values('entry_datetime')
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        axes[0, 1].plot(trades_df['entry_datetime'], trades_df['cumulative_pnl'])
        axes[0, 1].set_title('Cumulative PnL Over Time')
        axes[0, 1].set_xlabel('Date')
        axes[0, 1].set_ylabel('Cumulative PnL')
        axes[0, 1].tick_params(axis='x', rotation=45)
    else:
        # If no datetime available, plot cumulative PnL by trade number
        trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
        axes[0, 1].plot(range(len(trades_df)), trades_df['cumulative_pnl'])
        axes[0, 1].set_title('Cumulative PnL Over Time')
        axes[0, 1].set_xlabel('Trade Number')
        axes[0, 1].set_ylabel('Cumulative PnL')
    
    # Plot 3: Win vs Loss comparison
    wins = trades_df[trades_df['pnl'] > 0]['pnl']
    losses = trades_df[trades_df['pnl'] < 0]['pnl']
    
    axes[1, 0].bar(['Wins', 'Losses'], [len(wins), len(losses)], color=['green', 'red'])
    axes[1, 0].set_title('Number of Wins vs Losses')
    axes[1, 0].set_ylabel('Count')
    
    # Add value labels on bars
    for i, v in enumerate([len(wins), len(losses)]):
        axes[1, 0].text(i, v + 0.5, str(v), ha='center', va='bottom')
    
    # Plot 4: Average win vs average loss
    avg_win = wins.mean() if len(wins) > 0 else 0
    avg_loss = losses.mean() if len(losses) > 0 else 0
    
    axes[1, 1].bar(['Average Win', 'Average Loss'], [abs(avg_win), abs(avg_loss)], 
                   color=['green', 'red'])
    axes[1, 1].set_title('Average Win vs Average Loss')
    axes[1, 1].set_ylabel('PnL Amount')
    
    # Add value labels on bars
    for i, v in enumerate([abs(avg_win), abs(avg_loss)]):
        axes[1, 1].text(i, v + max(abs(avg_win), abs(avg_loss)) * 0.01, f'${v:.2f}', 
                        ha='center', va='bottom')
    
    plt.tight_layout()
    fig.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Trade analysis chart saved to {output_path}")


def plot_strategy_comparison(cerebro: bt.Cerebro, output_path: str = 'strategy_comparison.png') -> None:
    """
    Plot strategy performance compared to buy & hold
    """
    # This would require running an additional backtest with a buy & hold strategy
    # For now, we'll just plot the equity curve as implemented above
    plot_equity_curve(cerebro, output_path)