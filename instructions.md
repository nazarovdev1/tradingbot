# Smart Money Concept (SMC) + AI Trading Signal System

This system combines Smart Money Concept indicators with AI predictions to generate fact-based trading signals that can be consumed by a Telegram bot.

## Architecture Overview

- **SMC Engine**: Python module that detects BOS, CHOCH, FVGs, Order Blocks, Liquidity Sweeps, and other SMC concepts
- **FastAPI Server**: HTTP server providing API endpoints for SMC analysis and AI predictions
- **Node.js Telegram Bot**: Consumes signals from the Python backend and sends them to subscribers

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train the AI Model (Optional)

If you want to use the AI prediction component:

```bash
python train_model.py
```

This will download XAU/USD data and train an LSTM model, saving it to `models/model.h5`.

### 3. Start the SMC Server

```bash
uvicorn smc_server:app --host 0.0.0.0 --port 8000
```

The server will start with the following endpoints:
- `POST /smc` - Get pure SMC analysis
- `POST /predict` - Get AI prediction only  
- `POST /final` - Get combined SMC + AI signal
- `GET /health` - Health check

### 4. Configure the Telegram Bot

Create a `.env` file with the following variables:

```env
BOT_TOKEN=your_telegram_bot_token
TWELVEDATA_KEY=your_twelvedata_api_key
AI_MODEL_PATH=./models/model.h5
AI_SERVER_PORT=8000
SMC_SERVER_URL=http://127.0.0.1:8000/final
SMC_TIMEOUT_MS=10000
AUTO_CHECK_INTERVAL_MS=60000
```

### 5. Start the Telegram Bot

```bash
node index.js
```

## API Endpoints

### SMC Analysis (`POST /smc`)
Input:
```json
{
  "open": [100.1, 100.2, 100.3, ...],
  "high": [100.5, 100.6, 100.7, ...],
  "low": [99.8, 99.9, 100.0, ...],
  "close": [100.3, 100.4, 100.5, ...]
}
```

Output:
```json
{
  "trend": "BULLISH/BEARISH/RANGE",
  "bos": { "bullish": [...], "bearish": [...] },
  "choch": { "bullish": [...], "bearish": [...] },
  "fvgZones": [...],
  "orderBlocks": [...],
  "liquiditySwept": true/false,
  "bias": "BUY/SELL/NEUTRAL",
  "entry": number,
  "sl": number,
  "tp": number,
  "explanation": "detailed explanation"
}
```

### Final Signal (`POST /final`)
Combines SMC analysis with AI prediction to produce a final trading signal.

## Signal Logic

### BUY Signal Generated When:
- BOS up or CHOCH up detected
- Price enters discount zone (Fibonacci 62%-50%)
- Last Order Block is bullish and not invalidated
- No fresh liquidity above entry
- No bearish FVG above entry
- Trend is bullish AND volatility normal

### SELL Signal Generated When:
- BOS down or CHOCH down detected
- Price enters premium zone (Fibonacci 62%-50%)
- Last Order Block is bearish and not invalidated
- No fresh liquidity below entry
- No bullish FVG below entry
- Trend is bearish

The system prioritizes SMC signals over AI predictions when there's a conflict.

## Environment Variables

- `TWELVEDATA_KEY`: API key for fetching market data (get from twelvedata.com)
- `BOT_TOKEN`: Telegram bot token from @BotFather
- `AI_MODEL_PATH`: Path to the trained model file
- `AI_SERVER_PORT`: Port for the FastAPI server
- `SMC_SERVER_URL`: URL to the SMC server final endpoint
- `SMC_TIMEOUT_MS`: Timeout for SMC server requests
- `AUTO_CHECK_INTERVAL_MS`: Interval for automatic signal checks

## Testing

To test the SMC engine independently:

```bash
python smc_engine.py
```

## Troubleshooting

- If you receive "No model file found" messages, the system will work with fallback random predictions
- Ensure your TwelveData API key has sufficient requests quota
- Check that the server is running and accessible from the bot
- Verify that all environment variables are properly set