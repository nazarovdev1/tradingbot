require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

const SYMBOL = 'XAU/USD';
const INTERVAL = '15min';
const CANDLE_COUNT = 320; // enough bars to cover EMA200/ATR calculations
const MAX_RISK_ALLOWED = 40;
const ATR_PERIOD = 14;
const ATR_BASELINE_LOOKBACK = 10;
const SWING_LOOKBACK = 10;
const RISK_REWARD = 2;
const RSI_PERIOD = 14;

const bot = new Telegraf(process.env.BOT_TOKEN);

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

  if (!Array.isArray(response.data.values) || response.data.values.length < 210) {
    throw new Error('Not enough data to compute indicators');
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

function computeEMA(values, period) {
  if (values.length < period) throw new Error(`Need at least ${period} values for EMA`);
  const multiplier = 2 / (period + 1);
  let ema = values.slice(0, period).reduce((sum, v) => sum + v, 0) / period;
  for (let i = period; i < values.length; i++) {
    ema = (values[i] - ema) * multiplier + ema;
  }
  return ema;
}

function computeRSI(values, period = RSI_PERIOD) {
  if (values.length <= period) throw new Error('Not enough values for RSI');
  let gains = 0;
  let losses = 0;
  for (let i = 1; i <= period; i++) {
    const change = values[i] - values[i - 1];
    if (change >= 0) gains += change; else losses -= change;
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;
  for (let i = period + 1; i < values.length; i++) {
    const change = values[i] - values[i - 1];
    const gain = Math.max(change, 0);
    const loss = Math.max(-change, 0);
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
  }
  if (avgLoss === 0) return 100;
  const rs = avgGain / avgLoss;
  return 100 - 100 / (1 + rs);
}

function computeATRSeries(candles, period = ATR_PERIOD) {
  if (candles.length <= period) throw new Error('Not enough candles for ATR');
  const trs = [];
  for (let i = 1; i < candles.length; i++) {
    const current = candles[i];
    const prev = candles[i - 1];
    const tr = Math.max(
      current.high - current.low,
      Math.abs(current.high - prev.close),
      Math.abs(current.low - prev.close)
    );
    trs.push(tr);
  }

  const atrValues = [];
  let atr = trs.slice(0, period).reduce((sum, v) => sum + v, 0) / period;
  atrValues.push(atr);

  for (let i = period; i < trs.length; i++) {
    atr = (atr * (period - 1) + trs[i]) / period; // Wilder smoothing
    atrValues.push(atr);
  }

  return atrValues;
}

function calculateSwingLevels(candles, lookback = SWING_LOOKBACK) {
  if (candles.length < lookback) {
    return { swingLow: null, swingHigh: null };
  }

  const recent = candles.slice(-lookback);
  const swingLow = recent.reduce((min, candle) => Math.min(min, candle.low), Number.POSITIVE_INFINITY);
  const swingHigh = recent.reduce((max, candle) => Math.max(max, candle.high), Number.NEGATIVE_INFINITY);

  return {
    swingLow: swingLow === Number.POSITIVE_INFINITY ? null : swingLow,
    swingHigh: swingHigh === Number.NEGATIVE_INFINITY ? null : swingHigh
  };
}

async function analyzeMarketRisk() {
  const candles = await fetchTimeSeries(SYMBOL, INTERVAL);
  const closes = candles.map((c) => c.close);
  const price = closes[closes.length - 1];
  const ema200 = computeEMA(closes, 200);
  const rsi14 = computeRSI(closes, RSI_PERIOD);
  const atrSeries = computeATRSeries(candles, ATR_PERIOD);
  const atrCurrent = atrSeries[atrSeries.length - 1];
  const atrWindow = atrSeries.slice(-ATR_BASELINE_LOOKBACK);
  const atrBaseline = atrWindow.reduce((sum, value) => sum + value, 0) / atrWindow.length;
  const signal = price > ema200 ? 'BUY' : price < ema200 ? 'SELL' : 'NEUTRAL';

  const rsiDistance = rsi14 > 70 ? rsi14 - 70 : rsi14 < 30 ? 30 - rsi14 : 0;
  const rsiScore = Math.min(rsiDistance / 30, 1) * 40;

  const atrRatio = atrBaseline > 0 ? atrCurrent / atrBaseline : 1;
  const atrScore = Math.min(Math.max(atrRatio - 1, 0) / 1.5, 1) * 35;

  const deviation = ema200 ? Math.abs(price - ema200) / ema200 : 0;
  const trendScore = Math.min(deviation / 0.03, 1) * 25;

  const rawRisk = rsiScore + atrScore + trendScore;
  const riskScore = Math.min(parseFloat(rawRisk.toFixed(1)), 100);
  const safeTrade = riskScore <= MAX_RISK_ALLOWED;
  const { swingLow, swingHigh } = calculateSwingLevels(candles, SWING_LOOKBACK);

  let sl = null;
  let tp = null;

  if (safeTrade && signal === 'BUY' && swingLow !== null) {
    const riskDistance = price - swingLow;
    if (riskDistance > 0) {
      sl = swingLow;
      tp = price + riskDistance * RISK_REWARD;
    }
  } else if (safeTrade && signal === 'SELL' && swingHigh !== null) {
    const riskDistance = swingHigh - price;
    if (riskDistance > 0) {
      sl = swingHigh;
      tp = price - riskDistance * RISK_REWARD;
    }
  }

  return {
    price,
    ema200,
    rsi14,
    atrCurrent,
    atrBaseline,
    deviationPercent: deviation * 100,
    signal,
    riskScore,
    safeTrade,
    sl,
    tp
  };
}

function formatSignalMessage(result) {
  const { price, ema200, rsi14, atrCurrent, atrBaseline, deviationPercent, signal, riskScore, safeTrade, sl, tp } = result;
  const riskEmoji = safeTrade ? '✅' : '⛔';
  const signalEmoji = signal === 'BUY' ? '🟢' : signal === 'SELL' ? '🔴' : '⚪';
  const verdictText = safeTrade ? 'Tavsiya qilinadi' : 'Yuqori xavf - Qatnashmang';
  const signalUz = signal === 'BUY' ? 'BUY' : signal === 'SELL' ? 'SELL' : 'NEYTRAL';
  const lines = [
    `📊 XAU/USD ${INTERVAL} Smart Risk Assistant`,
    `🏁 Signal: ${signalUz} ${signalEmoji}`,
    `⚖️ Xavf darajasi: ${riskScore.toFixed(1)}% ${riskEmoji} (maks ${MAX_RISK_ALLOWED}%)`,
    `🧭 Xulosa: ${safeTrade ? 'XAVFSIZ / TAVSIYA QILINGAN' : 'YUQORI XAVF / QATNASHMANG'} - ${verdictText}`,
    `💰 Narx: ${price.toFixed(2)}`,
    `📈 EMA200: ${ema200.toFixed(2)} (farq ${deviationPercent.toFixed(2)}%)`,
    `📊 RSI14: ${rsi14.toFixed(2)}`,
    `🌪️ ATR(${ATR_PERIOD}): ${atrCurrent.toFixed(2)} | O'rtacha ${ATR_BASELINE_LOOKBACK}: ${atrBaseline.toFixed(2)}`
  ];

  if (safeTrade && sl !== null && tp !== null) {
    lines.push(`🛡️ Stop Loss: ${sl.toFixed(2)} (swing ${SWING_LOOKBACK})`);
    lines.push(`🎯 Take Profit: ${tp.toFixed(2)} (1:${RISK_REWARD} RR)`);
  } else {
    lines.push("⚠️ SL/TP: yuqori xavf yoki strukturaviy muammolar tufayi berilmagan.");
  }

  return lines.join('\n');
}

async function handleSniperSignal(ctx) {
  try {
    await ctx.reply('🔍 XAU/USD 15m Smart Risk baholanmoqda...');
    const result = await analyzeMarketRisk();
    await ctx.reply(formatSignalMessage(result));
  } catch (error) {
    console.error('Smart Risk signali yaratishda xatolik:', error.message);
    await ctx.reply(`Smart Risk baholash muvaffaqiyatsiz: ${error.message}`);
  }
}

// Bot wiring: only the 15m sniper strategy is exposed to avoid noisy signals from other timeframes
bot.start((ctx) => {
  ctx.reply('🥇 Oltin Smart Risk Assistant tayyor. XAU/USD uchun 15m bahoni olish uchun tugmani bosing.', {
    reply_markup: {
      inline_keyboard: [
        [{ text: '15m Smart Risk (XAU/USD)', callback_data: 'sniper_15m' }]
      ]
    }
  });
});

bot.action('sniper_15m', handleSniperSignal);

bot.launch();
console.log('Smart Risk Assistant boti XAU/USD 15m uchun ishga tushirildi...');

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
