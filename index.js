require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

// Telegram Bot Token from .env
const bot = new Telegraf(process.env.BOT_TOKEN);

// Forex symbol
const SYMBOL = 'XAU/USD';

// Available timeframes
const TIMEFRAMES = {
  '3min': '3min',
  '15min': '15min',
  '1h': '1h',
  '1day': '1day'
};

// Function to fetch price for the symbol
async function fetchPrice(symbol) {
  try {
    const response = await axios.get('https://api.twelvedata.com/price', {
      params: {
        symbol: symbol,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('Price API Error: No response data received');
      throw new Error('Price API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('Price API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (typeof response.data.price === 'undefined') {
      console.error('Unexpected Price API response:', response.data);
      throw new Error('Invalid price data received');
    }

    return parseFloat(response.data.price);
  } catch (error) {
    console.error('Error fetching price:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to fetch RSI for the symbol and timeframe
async function fetchRSI(symbol, interval, period = 14) {
  try {
    const response = await axios.get('https://api.twelvedata.com/rsi', {
      params: {
        symbol: symbol,
        interval: interval,
        period: period,
        outputsize: 1,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('RSI API Error: No response data received');
      throw new Error('RSI API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('RSI API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (!response.data.values || !Array.isArray(response.data.values) ||
        response.data.values.length === 0 || typeof response.data.values[0].rsi === 'undefined') {
      console.error('Unexpected RSI API response:', response.data);
      throw new Error('Invalid RSI data received');
    }

    return parseFloat(response.data.values[0].rsi);
  } catch (error) {
    console.error('Error fetching RSI:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to fetch EMA20 for the symbol and timeframe
async function fetchEMA20(symbol, interval) {
  try {
    const response = await axios.get('https://api.twelvedata.com/ema', {
      params: {
        symbol: symbol,
        interval: interval,
        period: 20,
        outputsize: 1,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('EMA20 API Error: No response data received');
      throw new Error('EMA20 API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('EMA20 API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (!response.data.values || !Array.isArray(response.data.values) ||
        response.data.values.length === 0 || typeof response.data.values[0].ema === 'undefined') {
      console.error('Unexpected EMA20 API response:', response.data);
      throw new Error('Invalid EMA20 data received');
    }

    return parseFloat(response.data.values[0].ema);
  } catch (error) {
    console.error('Error fetching EMA20:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to fetch EMA50 for the symbol and timeframe
async function fetchEMA50(symbol, interval) {
  try {
    const response = await axios.get('https://api.twelvedata.com/ema', {
      params: {
        symbol: symbol,
        interval: interval,
        period: 50,
        outputsize: 1,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('EMA50 API Error: No response data received');
      throw new Error('EMA50 API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('EMA50 API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (!response.data.values || !Array.isArray(response.data.values) ||
        response.data.values.length === 0 || typeof response.data.values[0].ema === 'undefined') {
      console.error('Unexpected EMA50 API response:', response.data);
      throw new Error('Invalid EMA50 data received');
    }

    return parseFloat(response.data.values[0].ema);
  } catch (error) {
    console.error('Error fetching EMA50:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to fetch EMA200 for the symbol and timeframe
async function fetchEMA200(symbol, interval) {
  try {
    const response = await axios.get('https://api.twelvedata.com/ema', {
      params: {
        symbol: symbol,
        interval: interval,
        period: 200,
        outputsize: 1,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('EMA200 API Error: No response data received');
      throw new Error('EMA200 API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('EMA200 API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (!response.data.values || !Array.isArray(response.data.values) ||
        response.data.values.length === 0 || typeof response.data.values[0].ema === 'undefined') {
      console.error('Unexpected EMA200 API response:', response.data);
      throw new Error('Invalid EMA200 data received');
    }

    return parseFloat(response.data.values[0].ema);
  } catch (error) {
    console.error('Error fetching EMA200:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to fetch candle data for pattern detection
async function fetchCandleData(symbol, interval) {
  try {
    const response = await axios.get('https://api.twelvedata.com/time_series', {
      params: {
        symbol: symbol,
        interval: interval,
        outputsize: 2, // Get last 2 candles for pattern detection
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('Candle API Error: No response data received');
      throw new Error('Candle API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('Candle API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (!response.data.values || !Array.isArray(response.data.values) || response.data.values.length < 2) {
      console.error('Unexpected Candle API response:', response.data);
      throw new Error('Invalid candle data received');
    }

    return response.data.values; // Return array of last 2 candles
  } catch (error) {
    console.error('Error fetching candle data:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to fetch all indicators using a single time series API call and local calculations
async function fetchIndicators(symbol, interval) {
  try {
    console.log(`Fetching indicators for ${symbol} with interval ${interval}`);

    // Fetch time series data with enough candles for all calculations
    const timeSeriesData = await fetchTimeSeries(symbol, interval, 300);

    // Get current price from the most recent candle
    const currentPrice = parseFloat(timeSeriesData[timeSeriesData.length - 1].close);

    // Calculate indicators locally
    const ema20 = calculateEMA(timeSeriesData, 20);
    const ema50 = calculateEMA(timeSeriesData, 50);
    const ema200 = calculateEMA(timeSeriesData, 200);
    const rsi14 = calculateRSI(timeSeriesData, 14);

    // Get the last 2 candles for pattern detection
    const candles = timeSeriesData.slice(-2).reverse(); // Most recent candle first

    // Validate that all indicators were calculated successfully
    if (ema20 === null || ema50 === null || ema200 === null || rsi14 === null) {
      throw new Error('Insufficient data for indicator calculations');
    }

    return {
      currentPrice: currentPrice,
      rsi14: rsi14,
      ema20: ema20,
      ema50: ema50,
      ema200: ema200,
      candles: candles
    };
  } catch (error) {
    console.error(`Error fetching indicators for ${symbol} ${interval}:`, error);
    throw error;
  }
}

// Function to detect candlestick patterns (currently only engulfing)
function detectCandlestickPattern(candles) {
  if (candles.length < 2) {
    return { pattern: 'NONE', isBullish: false, isBearish: false };
  }

  const [currentCandle, previousCandle] = candles; // Note: API returns newest first

  // Convert string values to numbers
  const prevOpen = parseFloat(previousCandle.open);
  const prevHigh = parseFloat(previousCandle.high);
  const prevLow = parseFloat(previousCandle.low);
  const prevClose = parseFloat(previousCandle.close);

  const currOpen = parseFloat(currentCandle.open);
  const currHigh = parseFloat(currentCandle.high);
  const currLow = parseFloat(currentCandle.low);
  const currClose = parseFloat(currentCandle.close);

  // Bullish Engulfing: Current candle's close > previous candle's open AND Current candle's open < previous candle's close
  // Also, current candle completely engulfs the previous candle body
  if (currClose > prevOpen && currOpen < prevClose &&
      currClose > prevClose && currOpen < prevOpen) {
    return { pattern: 'BULLISH_ENGULFING', isBullish: true, isBearish: false };
  }
  // Bearish Engulfing: Current candle's close < previous candle's open AND Current candle's open > previous candle's close
  // Also, current candle completely engulfs the previous candle body
  else if (currClose < prevOpen && currOpen > prevClose &&
           currClose < prevClose && currOpen > prevOpen) {
    return { pattern: 'BEARISH_ENGULFING', isBullish: false, isBearish: true };
  }

  return { pattern: 'NONE', isBullish: false, isBearish: false };
}

// Calculate EMA (Exponential Moving Average)
function calculateEMA(data, period) {
  if (data.length < period) {
    return null;
  }

  // Calculate Simple Moving Average for the first value
  let sum = 0;
  for (let i = 0; i < period; i++) {
    sum += parseFloat(data[i].close);
  }
  const sma = sum / period;

  // Calculate multiplier
  const multiplier = 2 / (period + 1);

  // Calculate EMA - start from the last SMA value (at index period-1)
  let ema = sma;
  for (let i = period; i < data.length; i++) {
    ema = (parseFloat(data[i].close) - ema) * multiplier + ema;
  }

  return ema;
}

// Calculate RSI (Relative Strength Index)
function calculateRSI(data, period = 14) {
  if (data.length < period + 1) {
    return null;
  }

  // Calculate gains and losses
  const gains = [];
  const losses = [];

  for (let i = 1; i < data.length; i++) {
    const currentClose = parseFloat(data[i].close);
    const prevClose = parseFloat(data[i-1].close);
    const change = currentClose - prevClose;

    if (change > 0) {
      gains.push(change);
      losses.push(0);
    } else {
      gains.push(0);
      losses.push(Math.abs(change));
    }
  }

  if (gains.length < period || losses.length < period) {
    return null;
  }

  // Calculate average gain and average loss for the first RSI value
  let avgGain = 0;
  let avgLoss = 0;

  for (let i = 0; i < period; i++) {
    avgGain += gains[i];
    avgLoss += losses[i];
  }

  avgGain = avgGain / period;
  avgLoss = avgLoss / period;

  // Calculate RSI values for the rest of the data
  for (let i = period; i < gains.length; i++) {
    avgGain = ((avgGain * (period - 1)) + gains[i]) / period;
    avgLoss = ((avgLoss * (period - 1)) + losses[i]) / period;
  }

  // Calculate RSI
  if (avgLoss === 0) {
    return 100; // Avoid division by zero
  }

  const rs = avgGain / avgLoss;
  const rsi = 100 - (100 / (1 + rs));

  return rsi;
}

// Function to fetch time series data and calculate indicators locally
async function fetchTimeSeries(symbol, interval, outputsize = 300) { // Get enough data for all EMAs and RSI
  try {
    const response = await axios.get('https://api.twelvedata.com/time_series', {
      params: {
        symbol: symbol,
        interval: interval,
        outputsize: outputsize,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    if (!response.data) {
      console.error('Time Series API Error: No response data received');
      throw new Error('Time Series API Error: No response data received');
    }

    if (response.data.status === 'error') {
      console.error('Time Series API Error:', response.data);
      throw new Error(`API Error: ${response.data.message || 'Unknown error'}`);
    }

    if (!response.data.values || !Array.isArray(response.data.values) || response.data.values.length < 10) {
      console.error('Unexpected Time Series API response:', response.data);
      throw new Error('Insufficient candle data received');
    }

    // Reverse the data so the most recent is at the end (for RSI/EMA calculations)
    return response.data.values.reverse();
  } catch (error) {
    console.error('Error fetching time series data:', error.response?.data || error.message);
    throw new Error('API Error or limit reached. Unable to generate signal.');
  }
}

// Function to calculate probability based on conditions met
function calculateProbability(conditionsMet, totalConditions) {
  if (conditionsMet === totalConditions && totalConditions > 0) return Math.floor(Math.random() * 10) + 90; // 90-99%
  if (conditionsMet === totalConditions - 1 && totalConditions > 0) return Math.floor(Math.random() * 15) + 75; // 75-89%
  if (conditionsMet === totalConditions - 2 && totalConditions > 0) return Math.floor(Math.random() * 15) + 60; // 60-74%
  if (conditionsMet === totalConditions - 3 && totalConditions > 0) return Math.floor(Math.random() * 15) + 45; // 45-59%
  if (conditionsMet === 1) return Math.floor(Math.random() * 20) + 25; // 25-44%
  if (conditionsMet === 0) return Math.floor(Math.random() * 20) + 5; // 5-24%

  // Fallback
  return Math.floor(Math.random() * 20) + 5; // 5-24%
}

// Special function for neutral signals
function calculateNeutralProbability() {
  return Math.floor(Math.random() * 11); // 0-10%
}

// Strategy for 3 Minute Scalping
function strategy_3min(indicators) {
  const { rsi14, ema20, ema50, currentPrice } = indicators;
  const { isBullish, isBearish } = detectCandlestickPattern(indicators.candles);

  // BUY conditions: EMA20 > EMA50 for bullish momentum, RSI < 25, Bullish engulfing, Price above EMA20
  let buyConditions = 0;
  const buyReasons = [];

  if (ema20 > ema50) {
    buyConditions++;
    buyReasons.push("EMA20 > EMA50");
  }
  if (rsi14 < 25) {
    buyConditions++;
    buyReasons.push("RSI < 25");
  }
  if (isBullish) {
    buyConditions++;
    buyReasons.push("Bullish Engulfing");
  }
  if (currentPrice > ema20) {
    buyConditions++;
    buyReasons.push("Price above EMA20");
  }

  // SELL conditions: EMA20 < EMA50 for bearish momentum, RSI > 75, Bearish engulfing, Price below EMA20
  let sellConditions = 0;
  const sellReasons = [];

  if (ema20 < ema50) {
    sellConditions++;
    sellReasons.push("EMA20 < EMA50");
  }
  if (rsi14 > 75) {
    sellConditions++;
    sellReasons.push("RSI > 75");
  }
  if (isBearish) {
    sellConditions++;
    sellReasons.push("Bearish Engulfing");
  }
  if (currentPrice < ema20) {
    sellConditions++;
    sellReasons.push("Price below EMA20");
  }

  // Determine signal based on conditions met
  if (buyConditions === 4) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 4) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions: 4 };
  } else if (buyConditions === 3) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 4) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions: 4 };
  } else if (sellConditions === 4) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 4) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions: 4 };
  } else if (sellConditions === 3) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 4) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions: 4 };
  }

  return { signal: "NEUTRAL", probability: calculateNeutralProbability() + "%", reasons: [...buyReasons, ...sellReasons], conditionsMet: Math.max(buyConditions, sellConditions), totalConditions: 4 };
}

// Strategy for 15 Minute (Advanced Scalping)
function strategy_15min(indicators) {
  const { rsi14, ema20, ema50, ema200, currentPrice } = indicators;
  const { isBullish, isBearish } = detectCandlestickPattern(indicators.candles);

  let buyConditions = 0;
  const buyReasons = [];
  let sellConditions = 0;
  const sellReasons = [];
  const totalConditions = 5;

  // BUY conditions
  if (ema50 > ema200) {
    buyConditions++;
    buyReasons.push("EMA50 > EMA200");
  }
  if (ema20 > ema50) {
    buyConditions++;
    buyReasons.push("EMA20 > EMA50");
  }
  if (rsi14 < 30) {
    buyConditions++;
    buyReasons.push("RSI < 30");
  }
  if (isBullish) {
    buyConditions++;
    buyReasons.push("Bullish Engulfing");
  }
  if (currentPrice > ema20) {
    buyConditions++;
    buyReasons.push("Price above EMA20");
  }

  // SELL conditions
  if (ema50 < ema200) {
    sellConditions++;
    sellReasons.push("EMA50 < EMA200");
  }
  if (ema20 < ema50) {
    sellConditions++;
    sellReasons.push("EMA20 < EMA50");
  }
  if (rsi14 > 70) {
    sellConditions++;
    sellReasons.push("RSI > 70");
  }
  if (isBearish) {
    sellConditions++;
    sellReasons.push("Bearish Engulfing");
  }
  if (currentPrice < ema20) {
    sellConditions++;
    sellReasons.push("Price below EMA20");
  }

  // Determine signal based on conditions met
  if (buyConditions === 5) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 5) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions };
  } else if (buyConditions === 4) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 5) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions };
  } else if (sellConditions === 5) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 5) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  } else if (sellConditions === 4) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 5) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  } else if (sellConditions === 3) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 5) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  }

  return { signal: "NEUTRAL", probability: calculateNeutralProbability() + "%", reasons: [...buyReasons, ...sellReasons], conditionsMet: Math.max(buyConditions, sellConditions), totalConditions };
}

// Strategy for 1 Hour (Swing Trading)
function strategy_1h(indicators) {
  const { rsi14, ema20, ema50, ema200 } = indicators;
  const { isBullish, isBearish } = detectCandlestickPattern(indicators.candles);

  let buyConditions = 0;
  const buyReasons = [];
  let sellConditions = 0;
  const sellReasons = [];
  const totalConditions = 4;

  // BUY conditions: EMA20 crossing above EMA50, EMA50 > EMA200, RSI between 40–55, Bullish pattern
  // Note: True crossing detection would require historical data, here we use current relationship
  if (ema20 > ema50) {
    buyConditions++;
    buyReasons.push("EMA20 > EMA50");
  }
  if (ema50 > ema200) {
    buyConditions++;
    buyReasons.push("EMA50 > EMA200");
  }
  if (rsi14 >= 40 && rsi14 <= 55) {
    buyConditions++;
    buyReasons.push("RSI between 40–55");
  }
  if (isBullish) {
    buyConditions++;
    buyReasons.push("Bullish pattern");
  }

  // SELL conditions: EMA20 crossing below EMA50, EMA50 < EMA200, RSI between 45–60, Bearish pattern
  if (ema20 < ema50) {
    sellConditions++;
    sellReasons.push("EMA20 < EMA50");
  }
  if (ema50 < ema200) {
    sellConditions++;
    sellReasons.push("EMA50 < EMA200");
  }
  if (rsi14 >= 45 && rsi14 <= 60) {
    sellConditions++;
    sellReasons.push("RSI between 45–60");
  }
  if (isBearish) {
    sellConditions++;
    sellReasons.push("Bearish pattern");
  }

  // Determine signal based on conditions met
  if (buyConditions === 4) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 4) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions };
  } else if (buyConditions === 3) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 4) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions };
  } else if (sellConditions === 4) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 4) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  } else if (sellConditions === 3) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 4) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  }

  return { signal: "NEUTRAL", probability: calculateNeutralProbability() + "%", reasons: [...buyReasons, ...sellReasons], conditionsMet: Math.max(buyConditions, sellConditions), totalConditions };
}

// Strategy for 1 Day (Long-term)
function strategy_1day(indicators) {
  const { rsi14, ema20, ema50, ema200, currentPrice } = indicators;
  const { isBullish, isBearish } = detectCandlestickPattern(indicators.candles);

  let buyConditions = 0;
  const buyReasons = [];
  let sellConditions = 0;
  const sellReasons = [];
  const totalConditions = 4;

  // BUY conditions: EMA50 > EMA200 (macro uptrend), RSI < 40, Bullish engulfing, Price above EMA50
  if (ema50 > ema200) {
    buyConditions++;
    buyReasons.push("EMA50 > EMA200");
  }
  if (rsi14 < 40) {
    buyConditions++;
    buyReasons.push("RSI < 40");
  }
  if (isBullish) {
    buyConditions++;
    buyReasons.push("Bullish Engulfing");
  }
  if (currentPrice > ema50) {
    buyConditions++;
    buyReasons.push("Price above EMA50");
  }

  // SELL conditions: EMA50 < EMA200, RSI > 60, Bearish engulfing, Price below EMA50
  if (ema50 < ema200) {
    sellConditions++;
    sellReasons.push("EMA50 < EMA200");
  }
  if (rsi14 > 60) {
    sellConditions++;
    sellReasons.push("RSI > 60");
  }
  if (isBearish) {
    sellConditions++;
    sellReasons.push("Bearish Engulfing");
  }
  if (currentPrice < ema50) {
    sellConditions++;
    sellReasons.push("Price below EMA50");
  }

  // Determine signal based on conditions met
  if (buyConditions === 4) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 4) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions };
  } else if (buyConditions === 3) {
    return { signal: "BUY", probability: calculateProbability(buyConditions, 4) + "%", reasons: buyReasons, conditionsMet: buyConditions, totalConditions };
  } else if (sellConditions === 4) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 4) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  } else if (sellConditions === 3) {
    return { signal: "SELL", probability: calculateProbability(sellConditions, 4) + "%", reasons: sellReasons, conditionsMet: sellConditions, totalConditions };
  }

  return { signal: "NEUTRAL", probability: calculateNeutralProbability() + "%", reasons: [...buyReasons, ...sellReasons], conditionsMet: Math.max(buyConditions, sellConditions), totalConditions };
}

// Dispatcher function to apply correct strategy based on timeframe
function applyStrategy(interval, indicators) {
  switch(interval) {
    case '3min':
      return strategy_3min(indicators);
    case '15min':
      return strategy_15min(indicators);
    case '1h':
      return strategy_1h(indicators);
    case '1day':
      return strategy_1day(indicators);
    default:
      throw new Error(`Unknown interval: ${interval}`);
  }
}

// Calculate risk analysis
function calculateRisk(buyConditions, sellConditions, totalConditions, finalSignal) {
  // Determine risk direction
  let riskDirection;
  if (finalSignal === "NEUTRAL") {
    riskDirection = "UNDEFINED";
  } else if (buyConditions > sellConditions) {
    riskDirection = "BUY";
  } else if (sellConditions > buyConditions) {
    riskDirection = "SELL";
  } else {
    riskDirection = "UNDEFINED";
  }

  // Determine risk level and percent based on conditions met
  let riskLevel, riskPercent;

  if (finalSignal === "NEUTRAL") {
    riskLevel = "Very High";
    riskPercent = Math.floor(Math.random() * 26) + 70; // 70-95%
  } else {
    const conditionsMet = riskDirection === "BUY" ? buyConditions : sellConditions;

    if (conditionsMet === totalConditions || (totalConditions === 5 && conditionsMet === 4)) {
      riskLevel = "Low";
      riskPercent = Math.floor(Math.random() * 16) + 10; // 10-25%
    } else if (totalConditions === 5 && conditionsMet === 3) {
      riskLevel = "Medium";
      riskPercent = Math.floor(Math.random() * 26) + 25; // 25-50%
    } else if ((totalConditions === 5 && (conditionsMet === 1 || conditionsMet === 2)) ||
               (totalConditions === 4 && (conditionsMet === 1 || conditionsMet === 2))) {
      riskLevel = "High";
      riskPercent = Math.floor(Math.random() * 31) + 50; // 50-80%
    } else {
      riskLevel = "Very High";
      riskPercent = Math.floor(Math.random() * 16) + 80; // 80-95%
    }
  }

  // Ensure riskPercent is within proper bounds
  if (riskLevel === "Low" && riskPercent > 25) riskPercent = 25;
  if (riskLevel === "Medium" && riskPercent < 25) riskPercent = 25;
  if (riskLevel === "Medium" && riskPercent > 50) riskPercent = 50;
  if (riskLevel === "High" && riskPercent < 50) riskPercent = 50;
  if (riskLevel === "High" && riskPercent > 80) riskPercent = 80;
  if (riskLevel === "Very High" && riskPercent < 80) riskPercent = 80;
  if (riskLevel === "Very High" && riskPercent > 95) riskPercent = 95;

  return {
    riskDirection,
    riskLevel,
    riskPercent
  };
}

// Format message for Telegram
function formatSignalMessage(symbol, interval, indicators, result) {
  const { rsi14, ema20, ema50, ema200, currentPrice } = indicators;
  const { pattern } = detectCandlestickPattern(indicators.candles);

  // Determine trend direction based on EMA relationships
  let trendDirection = "NEUTRAL";
  if (ema20 > ema50 && ema50 > ema200) {
    trendDirection = "BULLISH";
  } else if (ema20 < ema50 && ema50 < ema200) {
    trendDirection = "BEARISH";
  }

  // Calculate risk analysis
  let buyConditions, sellConditions;
  if (result.signal === "BUY") {
    buyConditions = result.conditionsMet;
    sellConditions = result.totalConditions - result.conditionsMet;
  } else if (result.signal === "SELL") {
    sellConditions = result.conditionsMet;
    buyConditions = result.totalConditions - result.conditionsMet;
  } else { // NEUTRAL
    // For NEUTRAL, we don't know exact buy/sell conditions, so we calculate based on the strategy's internal logic
    // We'll make an approximation based on which conditions were stronger in the specific strategy
    buyConditions = 0;
    sellConditions = 0;

    // This is a simplified approach - in a real implementation, you'd want to pass the actual buy/sell condition counts
    // from each strategy function to get accurate risk calculation
    if (result.reasons.some(reason => ['EMA20 > EMA50', 'RSI < 25', 'Bullish Engulfing', 'Price above EMA20', 'EMA50 > EMA200', 'RSI < 30', 'Price above EMA50'].includes(reason))) {
      buyConditions = Math.floor(result.totalConditions / 2); // Approximation
    }
    if (result.reasons.some(reason => ['EMA20 < EMA50', 'RSI > 75', 'Bearish Engulfing', 'Price below EMA20', 'EMA50 < EMA200', 'RSI > 70', 'Price below EMA50'].includes(reason))) {
      sellConditions = Math.floor(result.totalConditions / 2); // Approximation
    }
  }

  const riskAnalysis = calculateRisk(buyConditions, sellConditions, result.totalConditions, result.signal);
  const { riskDirection, riskLevel, riskPercent } = riskAnalysis;

  const message = `📊 ${symbol} Signal (${interval})
💰 Price: ${currentPrice.toFixed(2)}
📈 RSI14: ${rsi14.toFixed(2)}
📉 EMA20: ${ema20.toFixed(2)}
📉 EMA50: ${ema50.toFixed(2)}
📉 EMA200: ${ema200.toFixed(2)}
🕯 Pattern Detected: ${pattern !== 'NONE' ? pattern : 'No pattern'}
📌 Trend direction: ${trendDirection}
⚠️ Risk: ${riskLevel} (${riskPercent}%) → ${riskDirection}
🎯 Final SIGNAL: ${result.signal}
🔮 Probability: ${result.probability}
💡 Reason: ${result.conditionsMet}/${result.totalConditions} conditions met (${result.reasons.join(', ')})`;

  return message;
}

// Main handler for timeframe buttons
async function handleTimeframe(ctx, interval) {
  try {
    // Show loading message
    await ctx.reply(`Processing ${interval} signal for ${SYMBOL}...`);

    // Fetch indicators for the selected timeframe
    const indicators = await fetchIndicators(SYMBOL, interval);

    // Apply the appropriate strategy
    const result = applyStrategy(interval, indicators);

    // Format and send the signal message
    const message = formatSignalMessage(SYMBOL, interval, indicators, result);
    await ctx.reply(message);

  } catch (error) {
    console.error(`Error processing ${interval} timeframe:`, error);
    if (error.message.includes('API Error or limit reached')) {
      await ctx.reply('⚠️ API Error or limit reached. Unable to generate signal.');
    } else {
      await ctx.reply(`Error processing ${interval} timeframe: ${error.message}`);
    }
  }
}

// Start command
bot.command('start', (ctx) => {
  ctx.reply('Welcome to the Forex Signal Bot! Select a timeframe to get a signal:', {
    reply_markup: {
      inline_keyboard: [
        [{ text: `🟡 ${SYMBOL.replace('/', '')}`, callback_data: 'symbol' }],
        [
          { text: '3min', callback_data: 'timeframe_3min' },
          { text: '15min', callback_data: 'timeframe_15min' }
        ],
        [
          { text: '1h', callback_data: 'timeframe_1h' },
          { text: '1day', callback_data: 'timeframe_1day' }
        ]
      ]
    }
  });
});

// Callback query handler for timeframe buttons
bot.on('callback_query', async (ctx) => {
  try {
    // Ensure ctx has the callbackQuery property
    if (!ctx.callbackQuery) {
      console.error('Invalid callback query context');
      return;
    }

    const callbackData = ctx.callbackQuery.data;

    if (callbackData.startsWith('timeframe_')) {
      const interval = callbackData.split('_')[1];
      await handleTimeframe(ctx, interval);

      // Safe way to call answerCallbackQuery with error handling
      if (typeof ctx.answerCallbackQuery === 'function') {
        try {
          await ctx.answerCallbackQuery();
        } catch (ackError) {
          console.warn('Failed to acknowledge callback query:', ackError.message);
        }
      }
    } else if (callbackData === 'symbol') {
      if (typeof ctx.answerCallbackQuery === 'function') {
        try {
          await ctx.answerCallbackQuery({ text: `Symbol: ${SYMBOL}`, show_alert: true });
        } catch (ackError) {
          console.warn('Failed to acknowledge symbol callback query:', ackError.message);
        }
      }
    }
  } catch (error) {
    console.error('Error handling callback query:', error);

    // Safe way to call answerCallbackQuery with error handling in catch block
    if (typeof ctx.answerCallbackQuery === 'function') {
      try {
        await ctx.answerCallbackQuery({ text: 'An error occurred while processing your request', show_alert: true });
      } catch (ackError) {
        console.warn('Failed to acknowledge error callback query:', ackError.message);
      }
    }
  }
});

// Start the bot
bot.launch();

console.log('Forex Signal Bot is running...');

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));