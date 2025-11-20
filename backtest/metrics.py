import backtrader as bt
import pandas as pd
import numpy as np
from typing import Dict, Any
import sys
import os

# Add project root to path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from strategy.hybrid_smc_ai_strategy import HybridSMCAIStrategy


def calculate_metrics(results_dict: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate additional metrics from the backtest results
    """
    metrics = {}
    
    # Basic metrics that should already be in results
    metrics['total_return'] = results_dict.get('total_return', 0)
    metrics['sharpe_ratio'] = results_dict.get('sharpe_ratio', 0)
    metrics['max_drawdown'] = results_dict.get('max_drawdown', 0)
    metrics['win_rate'] = results_dict.get('win_rate', 0)
    metrics['profit_factor'] = results_dict.get('profit_factor', 0)
    
    # Calculate additional metrics if trades list is available
    trades_list = results_dict.get('trades_list', [])
    
    if trades_list:
        trades_df = pd.DataFrame(trades_list)
        
        # Average win/loss
        wins = trades_df[trades_df['pnl'] > 0]['pnl']
        losses = trades_df[trades_df['pnl'] < 0]['pnl']
        
        metrics['average_win'] = wins.mean() if not wins.empty else 0
        metrics['average_loss'] = losses.mean() if not losses.empty else 0
        metrics['win_loss_ratio'] = abs(metrics['average_win'] / metrics['average_loss']) if metrics['average_loss'] != 0 else float('inf')
        
        # Profit/loss metrics
        metrics['total_profit'] = wins.sum() if not wins.empty else 0
        metrics['total_loss'] = losses.sum() if not losses.empty else 0
        
        # Expectancy
        avg_win = metrics['average_win']
        avg_loss = abs(metrics['average_loss'])
        win_rate = metrics['win_rate']
        loss_rate = 1 - win_rate
        
        metrics['expectancy'] = (avg_win * win_rate) - (avg_loss * loss_rate) if avg_loss != 0 else 0
        
        # Max consecutive wins/losses
        pnl_series = trades_df['pnl']
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for pnl in pnl_series:
            if pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        
        metrics['max_consecutive_wins'] = max_consecutive_wins
        metrics['max_consecutive_losses'] = max_consecutive_losses
    
    return metrics


def analyze_trade_performance(trades_list: list) -> Dict[str, Any]:
    """
    Analyze the performance of individual trades
    """
    if not trades_list:
        return {}
    
    trades_df = pd.DataFrame(trades_list)
    
    performance = {
        'total_trades': len(trades_df),
        'winning_trades': len(trades_df[trades_df['pnl'] > 0]),
        'losing_trades': len(trades_df[trades_df['pnl'] < 0]),
        'breakeven_trades': len(trades_df[trades_df['pnl'] == 0]),
    }
    
    performance['win_rate'] = performance['winning_trades'] / performance['total_trades'] if performance['total_trades'] > 0 else 0
    
    if not trades_df.empty:
        performance['avg_pnl'] = trades_df['pnl'].mean()
        performance['total_pnl'] = trades_df['pnl'].sum()
        performance['pnl_std'] = trades_df['pnl'].std()
        performance['max_win'] = trades_df['pnl'].max()
        performance['max_loss'] = trades_df['pnl'].min()
        performance['profit_factor'] = (
            trades_df[trades_df['pnl'] > 0]['pnl'].sum() / 
            abs(trades_df[trades_df['pnl'] < 0]['pnl'].sum())
            if trades_df[trades_df['pnl'] < 0]['pnl'].sum() != 0 else float('inf')
        )
    
    return performance


def generate_backtest_report(results_dict: Dict[str, Any]) -> str:
    """
    Generate a comprehensive backtest report
    """
    # Calculate additional metrics
    metrics = calculate_metrics(results_dict)
    trade_performance = analyze_trade_performance(results_dict.get('trades_list', []))
    
    report = []
    report.append("="*60)
    report.append("BACKTEST RESULTS REPORT")
    report.append("="*60)
    report.append(f"Strategy: Hybrid SMC + AI Strategy")
    report.append(f"Initial Capital: ${results_dict['initial_value']:,.2f}")
    report.append(f"Final Capital: ${results_dict['final_value']:,.2f}")
    report.append(f"Total PnL: ${results_dict['pnl']:,.2f}")
    report.append(f"Total Return: {results_dict['total_return']*100:.2f}%")
    report.append("")
    
    report.append("KEY METRICS:")
    report.append(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
    report.append(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")
    report.append(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
    report.append(f"  Profit Factor: {metrics['profit_factor']:.4f}")
    report.append(f"  Expectancy: {metrics.get('expectancy', 0):.4f}")
    report.append("")
    
    report.append("TRADE PERFORMANCE:")
    report.append(f"  Total Trades: {trade_performance.get('total_trades', 0)}")
    report.append(f"  Winning Trades: {trade_performance.get('winning_trades', 0)}")
    report.append(f"  Losing Trades: {trade_performance.get('losing_trades', 0)}")
    report.append(f"  Breakeven Trades: {trade_performance.get('breakeven_trades', 0)}")
    report.append(f"  Avg Win: ${trade_performance.get('max_win', 0):.2f}")
    report.append(f"  Avg Loss: ${trade_performance.get('max_loss', 0):.2f}")
    report.append(f"  Total Profit: ${trade_performance.get('total_pnl', 0):.2f}")
    report.append("")
    
    report.append("RISK METRICS:")
    report.append(f"  Max Consecutive Wins: {metrics.get('max_consecutive_wins', 0)}")
    report.append(f"  Max Consecutive Losses: {metrics.get('max_consecutive_losses', 0)}")
    report.append(f"  Win/Loss Ratio: {metrics.get('win_loss_ratio', 0):.4f}")
    report.append("")
    
    report.append("STRATEGY PARAMETERS:")
    for param, value in results_dict.get('strategy_params', {}).items():
        report.append(f"  {param}: {value}")
    
    report.append("="*60)
    
    return "\n".join(report)