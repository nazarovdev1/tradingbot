import yfinance as yf
import pandas as pd
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

def create_model():
    model = Sequential()
    model.add(LSTM(50, input_shape=(20, 1)))
    model.add(Dense(1))  # Regression output
    model.compile(optimizer='adam', loss=tf.keras.losses.MeanSquaredError())
    return model

def main():
    # Check if local CSV exists
    csv_path = 'models/XAU_15m_data.csv'
    if os.path.exists(csv_path):
        print(f"Loading data from {csv_path}...")
        
        # Try reading with header first to check format
        # But based on user feedback, it seems to lack headers or have different format
        # Let's try reading it assuming no header if the first attempt fails or check first line
        
        try:
            # Read first line to check delimiter and header
            with open(csv_path, 'r') as f:
                first_line = f.readline()
            
            if ';' in first_line:
                # Previous format with semi-colon
                df = pd.read_csv(csv_path, sep=';')
            else:
                # New format: Comma separated, likely no header based on file view
                # 2021-09-01 07:30,1812.648,1813.658,1811.378,1812.925,15
                # Columns: Date, Open, High, Low, Close, Volume (maybe)
                df = pd.read_csv(csv_path, header=None, names=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
        
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return

        # Ensure 'Close' column exists
        if 'Close' in df.columns:
            closes = df['Close'].values
            print(f"Loaded {len(closes)} candles from CSV.")
        else:
            print("Error: 'Close' column not found in CSV")
            return
    else:
        print("CSV file not found. Downloading XAU/USD data from Yahoo Finance...")
        data = yf.download("GC=F", start="2019-01-01", end="2025-01-01")  # Using GC=F for Gold futures
        closes = data['Close'].dropna().values

    if len(closes) < 100:
        print("Not enough data")
        return

    closes = closes.astype(np.float32)

    # Scale the closes
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_closes = scaler.fit_transform(closes.reshape(-1, 1)).flatten()

    # Create sequences
    X = []
    y = []

    for i in range(len(scaled_closes) - 21):  # 20 for input, 1 for output
        seq = scaled_closes[i:i+20]
        target = scaled_closes[i+20] - scaled_closes[i+19]  # Change from last in seq to next
        # Normalize target to [-1, 1]
        target = target * 5  # Scale to get reasonable range
        target = np.clip(target, -1, 1)
        X.append(seq.reshape(-1, 1))  # (20, 1)
        y.append(target)

    X = np.array(X)  # (num_samples, 20, 1)
    y = np.array(y)

    print(f"Data shape: X={X.shape}, y={y.shape}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = create_model()
    model.fit(X_train, y_train, epochs=10, batch_size=32, validation_data=(X_test, y_test))

    # Save model
    model.save('models/model.h5')
    print("Model saved to models/model.h5")

if __name__ == "__main__":
    main()
