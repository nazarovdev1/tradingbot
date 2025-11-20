from setuptools import setup, find_packages

setup(
    name="smc-ai-backtester",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "backtrader",
        "pandas",
        "numpy",
        "matplotlib",
        "tensorflow",
        "scikit-learn",
        "yfinance",
        "tqdm",
    ],
    author="Quant Developer",
    description="SMC + AI Backtesting System",
    python_requires=">=3.7",
)