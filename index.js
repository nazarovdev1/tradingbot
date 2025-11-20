require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

const SYMBOL = 'XAU/USD';
const INTERVAL = '15min';
const CANDLE_COUNT = 320; // enough bars to cover SMC calculations
const MAX_RISK_ALLOWED = 40;
const SWING_LOOKBACK = 10;
const RISK_REWARD = 2;
const AUTO_CHECK_INTERVAL_MS = parseInt(process.env.AUTO_CHECK_INTERVAL_MS || '300000', 10);
const SMC_SERVER_URL = process.env.SMC_SERVER_URL || 'http://127.0.0.1:8000/smc';
const AI_SERVER_URL = process.env.AI_SERVER_URL || 'http://127.0.0.1:8000/predict';
const SMC_TIMEOUT_MS = parseInt(process.env.SMC_TIMEOUT_MS || '10000', 10);
const AI_TIMEOUT_MS = parseInt(process.env.AI_TIMEOUT_MS || '5000', 10);
const AI_CONFIDENCE_THRESHOLD = 0.85; // Only accept signals with >85% confidence

const subscribers = new Set();
let autoMonitorIntervalId = null;
let autoLoopRunning = false;
let lastAutoSignal = null;

const bot = new Telegraf(process.env.BOT_TOKEN);
const express = require('express');

async function fetchTimeSeries(symbol, interval) {
  const response = await axios.get('https://api.twelvedata.com/time_series', {
    params: {
      symbol,
      interval,
      outputsize: CANDLE_COUNT,
      apikey: process.env.TWELVEDATA_KEY
    }
  });

  if (!response.data || response.data.status === 'error') {
    throw new Error(response.data?.message || 'Failed to fetch time series');
  }

  if (!Array.isArray(response.data.values) || response.data.values.length < 50) { // Reduced min for SMC
    throw new Error('Not enough data to compute SMC indicators');
  }

  // TwelveData returns newest first; reverse for chronological calculations
  return response.data.values
    .map((candle) => ({
      time: candle.datetime,
      open: parseFloat(candle.open),
      high: parseFloat(candle.high),
      low: parseFloat(candle.low),
      close: parseFloat(candle.close)
    }))
    .reverse();
}

async function fetchSMCSignal(candles) {
  if (!SMC_SERVER_URL) {
    console.log('SMC server URL missing');
    return {
      validSMCZone: false,
      bias: 'NEUTRAL',
      entry: null,
      sl: null,
      tp: null,
      explanation: 'SMC server not configured',
      smc_analysis: null
    };
  }

  try {
    // Prepare data for SMC analysis - ensure all values are valid floats
    const open = candles.map(candle => parseFloat(candle.open)).filter(v => !isNaN(v) && isFinite(v));
    const high = candles.map(candle => parseFloat(candle.high)).filter(v => !isNaN(v) && isFinite(v));
    const low = candles.map(candle => parseFloat(candle.low)).filter(v => !isNaN(v) && isFinite(v));
    const close = candles.map(candle => parseFloat(candle.close)).filter(v => !isNaN(v) && isFinite(v));

    // Validate that all arrays have the same length
    if (open.length !== high.length || high.length !== low.length || low.length !== close.length) {
      console.error('Data validation failed: arrays have different lengths');
      return {
        validSMCZone: false,
        bias: 'NEUTRAL',
        entry: null,
        sl: null,
        tp: null,
        explanation: 'Invalid data from API',
        smc_analysis: null
      };
    }

    // Ensure we have enough data
    if (close.length < 10) {
      console.error('Not enough valid data points:', close.length);
      return {
        validSMCZone: false,
        bias: 'NEUTRAL',
        entry: null,
        sl: null,
        tp: null,
        explanation: 'Insufficient data',
        smc_analysis: null
      };
    }

    console.log(`Sending ${close.length} candles to SMC server...`);
    console.log(`First few values - Open: ${open.slice(0, 3)}, High: ${high.slice(0, 3)}, Low: ${low.slice(0, 3)}, Close: ${close.slice(0, 3)}`);

    const payload = {
      open: open,
      high: high,
      low: low,
      close: close
    };

    const response = await axios.post(
      SMC_SERVER_URL,
      payload,
      {
        timeout: SMC_TIMEOUT_MS,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    const data = response.data || {};

    // Check if price is in a valid SMC zone (Order Block or FVG)
    const currentPrice = close[close.length - 1];
    let validSMCZone = false;
    let zoneType = '';
    let zoneEntry = null;
    let calculatedSL = null;
    let calculatedTP = null;

    // Check for valid Order Blocks in range
    if (data.orderBlocks && data.orderBlocks.length > 0) {
      for (const ob of data.orderBlocks) {
        if (ob.type.includes('bullish') && currentPrice >= ob.low && currentPrice <= ob.high) {
          validSMCZone = true;
          zoneType = 'BULLISH ORDER BLOCK';
          zoneEntry = ob.high; // Entry at the top of bullish OB
          calculatedSL = ob.low - (Math.abs(ob.high - ob.low) * 0.1); // 10% below OB low
          calculatedTP = ob.high + (Math.abs(ob.high - calculatedSL) * RISK_REWARD); // 1:2 RR
          break;
        } else if (ob.type.includes('bearish') && currentPrice >= ob.low && currentPrice <= ob.high) {
          validSMCZone = true;
          zoneType = 'BEARISH ORDER BLOCK';
          zoneEntry = ob.low; // Entry at the bottom of bearish OB
          calculatedSL = ob.high + (Math.abs(ob.high - ob.low) * 0.1); // 10% above OB high
          calculatedTP = ob.low - (Math.abs(calculatedSL - ob.low) * RISK_REWARD); // 1:2 RR
          break;
        }
      }
    }

    // If no valid OB, check for FVG
    if (!validSMCZone && data.fvgZones && data.fvgZones.length > 0) {
      for (const fvg of data.fvgZones) {
        if (currentPrice >= fvg.low && currentPrice <= fvg.high) {
          validSMCZone = true;
          zoneType = fvg.type === 'bullish_fvg' ? 'BULLISH FVG' : 'BEARISH FVG';
          zoneEntry = fvg.entry;

          // Calculate SL and TP for FVG
          if (fvg.type === 'bullish_fvg') {
            calculatedSL = fvg.low - (Math.abs(fvg.high - fvg.low) * 0.1); // 10% below FVG low
            calculatedTP = fvg.high + (Math.abs(fvg.high - calculatedSL) * RISK_REWARD); // 1:2 RR
          } else {
            calculatedSL = fvg.high + (Math.abs(fvg.high - fvg.low) * 0.1); // 10% above FVG high
            calculatedTP = fvg.low - (Math.abs(calculatedSL - fvg.low) * RISK_REWARD); // 1:2 RR
          }
          break;
        }
      }
    }

    console.log(`SMC Analysis: Valid Zone=${validSMCZone}, Type=${zoneType}`);

    let bias = 'NEUTRAL';
    if (validSMCZone) {
      if (zoneType.includes('BULLISH')) {
        bias = 'BUY';
      } else if (zoneType.includes('BEARISH')) {
        bias = 'SELL';
      }
    }

    return {
      validSMCZone,
      zoneType,
      bias,
      entry: zoneEntry,
      sl: calculatedSL,
      tp: calculatedTP,
      explanation: data.explanation || 'No explanation available',
      smc_analysis: data
    };
  } catch (error) {
    console.error('SMC server request failed:', error.message);
    return {
      validSMCZone: false,
      bias: 'NEUTRAL',
      entry: null,
      sl: null,
      tp: null,
      explanation: 'SMC server error: ' + error.message,
      smc_analysis: null
    };
  }
}

async function fetchAIPrediction(closes) {
  if (!AI_SERVER_URL) {
    console.log('AI server URL missing - returning neutral with 50% confidence');
    return {
      signal: 'NEUTRAL',
      confidence: 0.5,  // Neutral confidence
      error: 'AI server URL missing'
    };
  }

  try {
    // Ensure all closes are valid floats
    const validCloses = closes.map(c => parseFloat(c)).filter(v => !isNaN(v) && isFinite(v));

    if (validCloses.length < 20) {
      console.log('Not enough valid close prices for AI prediction:', validCloses.length);
      return {
        signal: 'NEUTRAL',
        confidence: 0.5,  // Neutral confidence
        error: 'Insufficient data for AI'
      };
    }

    console.log('Asking AI for confirmation...');
    const response = await axios.post(
      AI_SERVER_URL,
      { closes: validCloses },
      { timeout: AI_TIMEOUT_MS }
    );

    const data = response.data || {};
    console.log(`AI Prediction: Signal=${data.signal}, Confidence=${data.confidence}`);

    // Protect against extremely low confidence values
    const confidence = data.confidence || 0;
    const adjustedConfidence = Math.max(0.01, Math.min(1.0, confidence)); // Clamp between 0.01 and 1.0

    return {
      signal: data.signal || 'NEUTRAL',
      confidence: adjustedConfidence
    };
  } catch (error) {
    console.error('AI server request failed:', error.message);
    console.error('Error details:', {
      status: error.response ? error.response.status : 'No response',
      statusText: error.response ? error.response.statusText : 'No response',
      data: error.response ? error.response.data : 'No response data'
    });

    // Return neutral with moderate confidence instead of 0
    return {
      signal: 'NEUTRAL',
      confidence: 0.3,  // Moderate confidence to allow basic functionality
      error: error.message
    };
  }
}

async function analyzeSMCMarket() {
  const candles = await fetchTimeSeries(SYMBOL, INTERVAL);
  const price = candles[candles.length - 1].close;

  // Step 1: SMC Check (The Location)
  const smcResult = await fetchSMCSignal(candles);

  if (!smcResult.validSMCZone) {
    console.log('Price is NOT in a valid SMC zone. No signal generated.');
    return {
      price,
      signal: 'NEUTRAL',
      confidence: 0,
      explanation: 'No valid SMC zone detected at current price level',
      entry: null,
      sl: null,
      tp: null
    };
  }

  console.log(`Price in ${smcResult.zoneType}. Proceeding to Step 2 - AI Confirmation.`);

  // Step 2: AI Confirmation (The Filter)
  const closes = candles.map(candle => candle.close);
  const aiResult = await fetchAIPrediction(closes);

  // Check if AI confidence meets threshold and direction matches SMC
  const aiConfidenceOk = aiResult.confidence >= AI_CONFIDENCE_THRESHOLD;
  const directionMatch = (smcResult.bias === 'BUY' && aiResult.signal === 'BUY') ||
    (smcResult.bias === 'SELL' && aiResult.signal === 'SELL');

  if (!aiConfidenceOk) {
    console.log(`AI rejected signal (Confidence too low: ${aiResult.confidence} < ${AI_CONFIDENCE_THRESHOLD})`);
    return {
      price,
      signal: 'NEUTRAL',
      confidence: aiResult.confidence,
      explanation: `Valid SMC zone detected (${smcResult.zoneType}) but AI confidence too low (${(aiResult.confidence * 100).toFixed(1)}%)`,
      entry: null,
      sl: null,
      tp: null
    };
  }

  if (!directionMatch) {
    console.log(`AI rejected signal (Direction mismatch: SMC=${smcResult.bias} vs AI=${aiResult.signal})`);
    return {
      price,
      signal: 'NEUTRAL',
      confidence: aiResult.confidence,
      explanation: `Valid SMC zone detected (${smcResult.zoneType}) but AI direction doesn't match (SMC: ${smcResult.bias} vs AI: ${aiResult.signal})`,
      entry: null,
      sl: null,
      tp: null
    };
  }

  // Step 3: Execution
  console.log('Confluence confirmed! SMC zone + AI confirmation > 85% confidence');

  return {
    price,
    signal: smcResult.bias,
    confidence: aiResult.confidence,
    explanation: `CONFLUENCE SIGNAL: ${smcResult.zoneType} confirmed with ${aiResult.signal} AI prediction (${(aiResult.confidence * 100).toFixed(1)}% confidence)`,
    entry: smcResult.entry,
    sl: smcResult.sl,
    tp: smcResult.tp
  };
}

function formatSignalMessage(result) {
  const { price, signal, confidence, explanation, entry, sl, tp } = result;
  const signalEmoji = signal === 'BUY' ? '🟢' : signal === 'SELL' ? '🔴' : '⚪️';
  const confidencePercent = (confidence * 100).toFixed(1);

  const lines = [
    `🎯 SMC + AI CONFLUENCE SNIPER SIGNAL 🎯`,
    ` `,
    `💡 Signal: ${signal} ${signalEmoji}`,
    ` `,
    `📈 Symbol: ${SYMBOL} | Timeframe: ${INTERVAL}`,
    `💰 Current Price: ${price.toFixed(4)}`,
    `🤖 AI Confidence: ${confidencePercent}%`,
    ` `,
    `🎯 Entry: ${entry ? entry.toFixed(4) : 'N/A'}`,
    `🛡️ Stop Loss: ${sl ? sl.toFixed(4) : 'N/A'}`,
    `🎯 Take Profit: ${tp ? tp.toFixed(4) : 'N/A'}`,
    ` `,
    `📋 Explanation:`,
    `${explanation}`
  ];

  if (entry !== null && sl !== null && tp !== null) {
    // Calculate risk and reward
    const risk = Math.abs(entry - sl);
    const reward = Math.abs(tp - entry);
    const riskReward = risk > 0 ? (reward / risk).toFixed(2) : 'N/A';

    lines.push(` `,
      `⚖️ Risk/Reward: ${riskReward}:1`,
      ` `,
      `⚠️ ALWAYS use proper risk management!`);
  }

  return lines.join('\n');
}

async function handleSniperSignal(ctx) {
  try {
    await ctx.reply('🔍 Running Sniper Strategy Scan...');
    const result = await analyzeSMCMarket();

    if (result.signal !== 'NEUTRAL') {
      await ctx.reply(formatSignalMessage(result));
    } else {
      await ctx.reply(`⚪️ No confluence signal detected.\n${result.explanation}`);
    }
  } catch (error) {
    console.error('Sniper strategy scan failed:', error.message);
    await ctx.reply(`❌ Sniper strategy scan failed: ${error.message}`);
  }
}

async function runAutoSignalPush() {
  if (autoLoopRunning) return;
  autoLoopRunning = true;
  try {
    if (subscribers.size === 0) {
      lastAutoSignal = null;
      return;
    }

    const result = await analyzeSMCMarket();
    const actionable = result.signal !== 'NEUTRAL';

    if (!actionable) {
      // Only reset last signal if we had a previous actionable signal
      if (lastAutoSignal !== null) {
        console.log('No actionable signal found, clearing last signal');
        lastAutoSignal = null;
      }
      return;
    }

    // Only send signal if it's different from the last one
    if (lastAutoSignal === result.signal) {
      console.log('Same signal as last time, skipping');
      return;
    }

    lastAutoSignal = result.signal;
    console.log(`Sending new confluence signal: ${result.signal}`);

    const autoMessage = formatSignalMessage(result);
    await Promise.allSettled(
      [...subscribers].map(async (chatId) => {
        try {
          await bot.telegram.sendMessage(chatId, autoMessage);
        } catch (error) {
          console.error('Auto signal delivery failed:', error.message);
          if (error?.response?.error_code === 403) {
            subscribers.delete(chatId);
          }
        }
      })
    );
  } catch (error) {
    console.error('Auto Sniper monitoring error:', error.message);
  } finally {
    autoLoopRunning = false;
  }
}

function ensureAutoMonitor() {
  if (autoMonitorIntervalId) return;
  autoMonitorIntervalId = setInterval(() => {
    runAutoSignalPush();
  }, AUTO_CHECK_INTERVAL_MS);
}

// Bot wiring: only the Sniper strategy is exposed
bot.start((ctx) => {
  if (ctx.chat?.id) {
    subscribers.add(ctx.chat.id);
  }
  ctx.reply('🎯 SMC + AI Confluence Sniper Bot is ready!\n\nThe bot scans for high-probability setups using Smart Money Concepts + AI confirmation.\n\nSignals are only sent when:\n• Price is in a valid SMC zone (OB/FVG)\n• AI confirms direction with >85% confidence\n\nUse the button below for manual scan:', {
    reply_markup: {
      inline_keyboard: [
        [{ text: '🔍 Manual Sniper Scan', callback_data: 'sniper_15m' }]
      ]
    }
  });
});

bot.action('sniper_15m', async (ctx) => {
  if (ctx.chat?.id) {
    subscribers.add(ctx.chat.id);
  }
  await handleSniperSignal(ctx);
});

ensureAutoMonitor();

// Check if running on Render or locally
if (process.env.RENDER_EXTERNAL_URL) {
  // Running on Render - use webhook
  const app = express();
  const port = process.env.PORT || 3000;

  // Health check route for Render
  app.get('/', (req, res) => {
    res.send('SMC + AI Confluence Sniper Bot is running!');
  });

  // Set up webhook for Telegram
  app.use(bot.webhookCallback(`/bot${process.env.BOT_TOKEN}`));

  app.listen(port, () => {
    console.log(`SMC + AI Confluence Sniper Bot listening on port ${port}...`);
    // Set webhook URL when deployed on Render
    let renderUrl = process.env.RENDER_EXTERNAL_URL;
    console.log("RENDER_EXTERNAL_URL:", process.env.RENDER_EXTERNAL_URL);

    if (renderUrl) {
      if (renderUrl.startsWith('https://')) {
        renderUrl = renderUrl.substring(8);
      } else if (renderUrl.startsWith('http://')) {
        renderUrl = renderUrl.substring(7);
      }
      renderUrl = `https://${renderUrl}`;
    } else {
      console.error("RENDER_EXTERNAL_URL is not set!");
      return;
    }

    const webhookUrl = `${renderUrl}/bot${process.env.BOT_TOKEN}`;
    console.log("Setting webhook to:", webhookUrl);

    bot.telegram.setWebhook(webhookUrl);
  });
} else {
  // Running locally - use polling
  bot.launch();
  console.log('SMC + AI Confluence Sniper Bot started in polling mode...');
}

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));