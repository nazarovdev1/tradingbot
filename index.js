require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

const SYMBOL = 'XAU/USD';
const INTERVAL = '15min';
const CANDLE_COUNT = 320; // enough bars to cover SMC calculations
const MAX_RISK_ALLOWED = 40;
const SWING_LOOKBACK = 10;
const RISK_REWARD = 2;
const AUTO_CHECK_INTERVAL_MS = parseInt(process.env.AUTO_CHECK_INTERVAL_MS || '60000', 10);
const SMC_SERVER_URL = process.env.SMC_SERVER_URL || 'http://127.0.0.1:8000/final';
const SMC_TIMEOUT_MS = parseInt(process.env.SMC_TIMEOUT_MS || '10000', 10);

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
    return {
      signal: 'NEUTRAL',
      confidence: 0,
      error: 'SMC server URL missing',
      bias: 'NEUTRAL',
      explanation: 'SMC server not configured'
    };
  }

  try {
    // Prepare data for SMC analysis
    const open = candles.map(candle => candle.open);
    const high = candles.map(candle => candle.high);
    const low = candles.map(candle => candle.low);
    const close = candles.map(candle => candle.close);

    const response = await axios.post(
      SMC_SERVER_URL,
      { open, high, low, close },
      { timeout: SMC_TIMEOUT_MS }
    );

    const data = response.data || {};
    return {
      signal: data.signal || 'NEUTRAL',
      confidence: data.confidence || 0,
      bias: data.smc_analysis?.bias || 'NEUTRAL',
      explanation: data.explanation || 'No explanation available',
      entry: data.entry,
      sl: data.sl,
      tp: data.tp,
      trend: data.smc_analysis?.trend,
      smc_analysis: data.smc_analysis
    };
  } catch (error) {
    console.error('SMC server request failed:', error.message);
    return {
      signal: 'NEUTRAL',
      confidence: 0,
      error: error.message,
      bias: 'NEUTRAL',
      explanation: 'SMC server error'
    };
  }
}

async function analyzeSMCMarket() {
  const candles = await fetchTimeSeries(SYMBOL, INTERVAL);
  const price = candles[candles.length - 1].close;

  // Get SMC analysis
  const smcResult = await fetchSMCSignal(candles);

  return {
    price,
    signal: smcResult.signal,
    confidence: smcResult.confidence,
    bias: smcResult.bias,
    explanation: smcResult.explanation,
    entry: smcResult.entry,
    sl: smcResult.sl,
    tp: smcResult.tp,
    trend: smcResult.trend,
    smc_analysis: smcResult.smc_analysis,
    finalSignal: smcResult.signal // In SMC system, the signal is the final signal
  };
}

function formatSignalMessage(result) {
  const { price, signal, confidence, bias, explanation, entry, sl, tp, trend, smc_analysis } = result;
  const signalEmoji = signal === 'BUY' ? '🟢' : signal === 'SELL' ? '🔴' : '⚪️';
  const verdictText = signal !== 'NEUTRAL' ? 'Tavsiya qilinadi' : 'Signal mavjud emas';
  const signalUz = signal === 'BUY' ? 'BUY' : signal === 'SELL' ? 'SELL' : 'NEYTRAL';

  // Create trend text based on SMC trend
  const trendText = trend === 'BULLISH' ? 'Yuksaluvchi trend (BUY mezonlar)' :
                   trend === 'BEARISH' ? 'Pasayuvchi trend (SELL mezonlar)' :
                   'Trend noaniq (RANGE)';

  const lines = [
    `📊 XAU/USD ${INTERVAL} (15 daqiqa) Smart Money Concept Assistant`,
    `🧭 Trend: ${trendText}`,
    `🏁 Signal: ${signalUz} ${signalEmoji}`,
    `🎯 Yakuniy signal: ${signal}`,
    `🤖 Ishonch: ${(confidence * 100).toFixed(1)}%`,
    `💡 Tushuntirish: ${explanation}`,
    `💰 Narx: ${price.toFixed(2)}`
  ];

  // Add SMC-specific details if available
  if (smc_analysis) {
    const bosCount = (smc_analysis.bos?.bullish?.length || 0) + (smc_analysis.bos?.bearish?.length || 0);
    const chochCount = (smc_analysis.choch?.bullish?.length || 0) + (smc_analysis.choch?.bearish?.length || 0);
    const fvgCount = smc_analysis.fvgZones?.length || 0;
    const obCount = smc_analysis.orderBlocks?.length || 0;

    if (bosCount > 0 || chochCount > 0 || fvgCount > 0 || obCount > 0) {
      lines.push(`📈 SMC Elementlar:`);
      if (bosCount > 0) lines.push(`   • BOS: ${bosCount} ta`);
      if (chochCount > 0) lines.push(`   • CHOCH: ${chochCount} ta`);
      if (fvgCount > 0) lines.push(`   • FVG: ${fvgCount} ta`);
      if (obCount > 0) lines.push(`   • Order Block: ${obCount} ta`);
    }
  }

  if (entry !== null && sl !== null && tp !== null) {
    lines.push(`🎯 Entry: ${entry.toFixed(2)}`);
    lines.push(`🛡️ Stop Loss: ${sl.toFixed(2)}`);
    lines.push(`🎯 Take Profit: ${tp.toFixed(2)}`);
    lines.push(`⚖️ Risk/Reward: ${(Math.abs(entry - tp) / Math.abs(entry - sl)).toFixed(1)}:1`);
  } else {
    lines.push('⚠️ Entry/SL/TP: hali aniqlanmadi.');
  }

  return lines.join('\n');
}

async function handleSniperSignal(ctx) {
  try {
    await ctx.reply('🔍 XAU/USD 15m Smart Money Concept tahlili...');
    const result = await analyzeSMCMarket();
    await ctx.reply(formatSignalMessage(result));
  } catch (error) {
    console.error('SMC signali yaratishda xatolik:', error.message);
    await ctx.reply(`SMC tahlili muvaffaqiyatsiz: ${error.message}`);
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
      if (result.signal === 'NEUTRAL') {
        lastAutoSignal = null;
      }
      return;
    }

    // Only send signal if it's different from the last one
    if (lastAutoSignal === result.signal) {
      return;
    }
    lastAutoSignal = result.signal;

    const autoMessage = `${formatSignalMessage(result)}\n⏱️ Avto-signal: SMC 15m monitoring`;
    await Promise.allSettled(
      [...subscribers].map(async (chatId) => {
        try {
          await bot.telegram.sendMessage(chatId, autoMessage);
        } catch (error) {
          console.error('Auto signal yuborishda xato:', error.message);
          if (error?.response?.error_code === 403) {
            subscribers.delete(chatId);
          }
        }
      })
    );
  } catch (error) {
    console.error('Auto SMC monitoring xatosi:', error.message);
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

// Bot wiring: only the 15m SMC strategy is exposed to avoid noisy signals
bot.start((ctx) => {
  if (ctx.chat?.id) {
    subscribers.add(ctx.chat.id);
  }
  ctx.reply('🔍 Oltin Smart Money Concept Assistant tayyor. 15m SMC signallari avtomatik kuzatuvda, qo\'lda so\'rov uchun tugmani bosing.', {
    reply_markup: {
      inline_keyboard: [
        [{ text: '15m SMC Signal (XAU/USD)', callback_data: 'sniper_15m' }]
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
    res.send('Smart Money Concept Assistant bot is running!');
  });

  // Set up webhook for Telegram
  app.use(bot.webhookCallback(`/bot${process.env.BOT_TOKEN}`));

  app.listen(port, () => {
    console.log(`Smart Money Concept Assistant boti ${port}-portda ishga tushirildi...`);
    // Set webhook URL when deployed on Render
    // Check if RENDER_EXTERNAL_URL already includes the protocol
    let renderUrl = process.env.RENDER_EXTERNAL_URL;
    console.log("RENDER_EXTERNAL_URL:", process.env.RENDER_EXTERNAL_URL); // Debug log

    if (renderUrl) {
      // Remove protocol if it's already there to avoid double https://
      if (renderUrl.startsWith('https://')) {
        renderUrl = renderUrl.substring(8); // Remove 'https://'
      } else if (renderUrl.startsWith('http://')) {
        renderUrl = renderUrl.substring(7); // Remove 'http://'
      }

      // Add https:// to make it a proper URL
      renderUrl = `https://${renderUrl}`;
    } else {
      // Fallback in case RENDER_EXTERNAL_URL is not set (shouldn't happen on Render)
      console.error("RENDER_EXTERNAL_URL is not set!");
      return;
    }

    const webhookUrl = `${renderUrl}/bot${process.env.BOT_TOKEN}`;
    console.log("Setting webhook to:", webhookUrl); // Debug log

    bot.telegram.setWebhook(webhookUrl);
  });
} else {
  // Running locally - use polling
  bot.launch();
  console.log('Smart Money Concept Assistant boti polling rejimida ishga tushirildi...');
}

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
