#!/usr/bin/env python3
"""
Main runner for the SMC + AI Backtesting System
"""
import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backtest.data_loader import execute_backtest
from backtest.plot import plot_equity_curve, plot_trade_analysis
from backtest.metrics import generate_backtest_report, calculate_metrics
from backtest.data_loader import DataLoader, save_results_to_csv, save_results_to_json


def main():
    parser = argparse.ArgumentParser(description='SMC + AI Backtesting System')
    parser.add_argument('--data', type=str, required=True, help='Path to CSV data file')
    parser.add_argument('--output-dir', type=str, default='./backtest_results', help='Output directory for results')
    parser.add_argument('--initial-cash', type=float, default=10000.0, help='Initial cash for backtest')
    parser.add_argument('--commission', type=float, default=0.001, help='Commission rate')
    parser.add_argument('--printlog', action='store_true', help='Print log during backtest')
    
    # Strategy parameters
    parser.add_argument('--risk-per-trade', type=float, default=0.02, help='Risk per trade (default: 0.02 = 2%)')
    parser.add_argument('--max-risk', type=int, default=40, help='Max risk allowed (default: 40)')
    parser.add_argument('--atr-period', type=int, default=14, help='ATR period (default: 14)')
    parser.add_argument('--ema200-period', type=int, default=200, help='EMA200 period (default: 200)')
    parser.add_argument('--ema50-period', type=int, default=50, help='EMA50 period (default: 50)')
    parser.add_argument('--rsi-period', type=int, default=14, help='RSI period (default: 14)')
    parser.add_argument('--risk-reward', type=float, default=2.0, help='Risk/reward ratio (default: 2.0)')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("Starting SMC + AI Backtesting System...")
    print(f"Data file: {args.data}")
    print(f"Initial cash: ${args.initial_cash:,.2f}")
    print(f"Commission: {args.commission:.4f}")
    print("-" * 50)
    
    # Prepare strategy parameters
    strategy_params = {
        'printlog': args.printlog,
        'risk_per_trade': args.risk_per_trade,
        'max_risk_allowed': args.max_risk,
        'atr_period': args.atr_period,
        'ema200_period': args.ema200_period,
        'ema50_period': args.ema50_period,
        'rsi_period': args.rsi_period,
        'risk_reward': args.risk_reward
    }
    
    # Run the backtest
    try:
        cerebro, results_dict = execute_backtest(
            data_path=args.data,
            strategy_params=strategy_params,
            initial_cash=args.initial_cash,
            commission=args.commission
        )
        
        print(f"Backtest completed!")
        print(f"Initial Value: ${results_dict['initial_value']:,.2f}")
        print(f"Final Value: ${results_dict['final_value']:,.2f}")
        print(f"Total Return: {results_dict['total_return']*100:.2f}%")
        print(f"Total Trades: {results_dict['total_trades']}")
        print(f"Win Rate: {results_dict['win_rate']*100:.2f}%")
        print(f"Profit Factor: {results_dict['profit_factor']:.4f}")
        print(f"Sharpe Ratio: {results_dict['sharpe_ratio']:.4f}")
        print(f"Max Drawdown: {results_dict['max_drawdown']*100:.2f}%")
        
        # Generate and print detailed report
        report = generate_backtest_report(results_dict)
        print("\n" + report)
        
        # Save results
        csv_path = output_dir / f"backtest_results_{Path(args.data).stem}.csv"
        json_path = output_dir / f"backtest_results_{Path(args.data).stem}.json"
        
        save_results_to_csv(results_dict, str(csv_path))
        save_results_to_json(results_dict, str(json_path))
        
        # Generate plots
        equity_plot_path = output_dir / f"equity_curve_{Path(args.data).stem}.png"
        analysis_plot_path = output_dir / f"trade_analysis_{Path(args.data).stem}.png"
        
        plot_equity_curve(cerebro, str(equity_plot_path))
        plot_trade_analysis(results_dict, str(analysis_plot_path))
        
        print(f"\nResults saved to:")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")
        print(f"  Equity Curve: {equity_plot_path}")
        print(f"  Trade Analysis: {analysis_plot_path}")
        
    except Exception as e:
        print(f"Error during backtesting: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()