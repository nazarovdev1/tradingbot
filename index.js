require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

const bot = new Telegraf(process.env.BOT_TOKEN);
const STRATEGY_SERVER_URL = 'http://localhost:5000/analyze';
const TIMEFRAME = '15min';
const TIMEFRAME_LABEL = '15min (15 daqiqa)';
const MAX_RISK_ALLOWED = 40;
const ALERT_COOLDOWN = 300000; // 5 minutes

let lastCandleTime = 0;
let lastAlert = 0;

// Function to fetch OHLC data from TwelveData (supports XAU/USD)
async function fetchOHLCV(symbol = 'XAU/USD', timeframe = TIMEFRAME, limit = 100) {
    try {
        const response = await axios.get('https://api.twelvedata.com/time_series', {
            params: {
                symbol,
                interval: timeframe,
                outputsize: limit,
                apikey: process.env.TWELVEDATA_KEY
            }
        });

        if (!response.data || response.data.status === 'error') {
            throw new Error(response.data?.message || 'Failed to fetch data from TwelveData');
        }

        const values = Array.isArray(response.data.values) ? response.data.values.slice().reverse() : [];
        if (values.length === 0) {
            throw new Error('Empty response from TwelveData');
        }

        return {
            open: values.map(item => parseFloat(item.open)),
            high: values.map(item => parseFloat(item.high)),
            low: values.map(item => parseFloat(item.low)),
            close: values.map(item => parseFloat(item.close)),
            volume: values.map(item => parseFloat(item.volume || 0)),
            timestamps: values.map(item => new Date(item.datetime).getTime())
        };
    } catch (error) {
        console.error('Error fetching OHLCV data:', error.message);
        throw error;
    }
}

function calculateEMA(values, period) {
    if (values.length < period) throw new Error(`Need at least ${period} closes for EMA`);
    const k = 2 / (period + 1);
    let ema = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    for (let i = period; i < values.length; i++) {
        ema = values[i] * k + ema * (1 - k);
    }
    return ema;
}

function calculateRSI(values, period = 14) {
    if (values.length <= period) throw new Error('Not enough closes for RSI');
    let gains = 0;
    let losses = 0;
    for (let i = 1; i <= period; i++) {
        const diff = values[i] - values[i - 1];
        if (diff >= 0) gains += diff; else losses -= diff;
    }
    let avgGain = gains / period;
    let avgLoss = losses / period;
    for (let i = period + 1; i < values.length; i++) {
        const diff = values[i] - values[i - 1];
        const gain = diff > 0 ? diff : 0;
        const loss = diff < 0 ? -diff : 0;
        avgGain = ((avgGain * (period - 1)) + gain) / period;
        avgLoss = ((avgLoss * (period - 1)) + loss) / period;
    }
    if (avgLoss === 0) return 100;
    const rs = avgGain / avgLoss;
    return 100 - 100 / (1 + rs);
}

function calculateATR(highs, lows, closes, period = 14) {
    if (highs.length <= period || lows.length <= period || closes.length <= period) {
        throw new Error('Not enough candles for ATR');
    }
    const trs = [];
    for (let i = 1; i < highs.length; i++) {
        const high = highs[i];
        const low = lows[i];
        const prevClose = closes[i - 1];
        const tr = Math.max(
            high - low,
            Math.abs(high - prevClose),
            Math.abs(low - prevClose)
        );
        trs.push(tr);
    }
    let atr = trs.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    const atrSeries = [atr];
    for (let i = period; i < trs.length; i++) {
        atr = ((atr * (period - 1)) + trs[i]) / period;
        atrSeries.push(atr);
    }
    return atrSeries;
}

function calculateSwingLevels(lows, highs, lookback = 10) {
    if (lows.length < lookback || highs.length < lookback) return { swingLow: null, swingHigh: null };
    const recentLows = lows.slice(-lookback);
    const recentHighs = highs.slice(-lookback);
    const swingLow = recentLows.reduce((min, value) => Math.min(min, value), Number.POSITIVE_INFINITY);
    const swingHigh = recentHighs.reduce((max, value) => Math.max(max, value), Number.NEGATIVE_INFINITY);
    return {
        swingLow: swingLow === Number.POSITIVE_INFINITY ? null : swingLow,
        swingHigh: swingHigh === Number.NEGATIVE_INFINITY ? null : swingHigh
    };
}

function buildRiskSnapshot(data) {
    const closes = data.close;
    const highs = data.high;
    const lows = data.low;
    if (closes.length < 210) throw new Error('Not enough data for risk snapshot');

    const price = closes[closes.length - 1];
    const ema200 = calculateEMA(closes, 200);
    const ema50 = calculateEMA(closes, 50);
    const rsi14 = calculateRSI(closes, 14);
    const atrSeries = calculateATR(highs, lows, closes, 14);
    const atrCurrent = atrSeries[atrSeries.length - 1];
    const atrBaseline = atrSeries.slice(-10).reduce((sum, value) => sum + value, 0) / Math.min(10, atrSeries.length);
    const deviation = ema200 ? Math.abs(price - ema200) / ema200 : 0;
    const deviationPercent = deviation * 100;
    const nearEma = deviation <= 0.005;
    const inBreakoutZone = deviation <= 0.012;
    const atrRatio = atrBaseline > 0 ? atrCurrent / atrBaseline : 1;

    const rsiMidDistance = Math.max(0, Math.abs(rsi14 - 50) - 10);
    const rsiScore = Math.min(rsiMidDistance / 40, 1) * 35;
    const deviationPenalty = Math.max(0, deviation - 0.005);
    const deviationRange = Math.max(0.012 - 0.005, 0.0001);
    const deviationScore = Math.min(deviationPenalty / deviationRange, 1) * 40;
    let atrScore = 0;
    if (atrRatio < 0.8) {
        atrScore = Math.min((0.8 - atrRatio) / 0.8, 1) * 25;
    } else if (atrRatio > 1.8) {
        atrScore = Math.min((atrRatio - 1.8) / 1.8, 1) * 25;
    }
    const riskScore = Math.min(Number((deviationScore + rsiScore + atrScore).toFixed(1)), 100);
    const safeTrade = riskScore <= MAX_RISK_ALLOWED;

    const trendBias = price > ema200 ? 'BULLISH' : price < ema200 ? 'BEARISH' : 'FLAT';
    const shortTrendBias = price > ema50 ? 'BULLISH' : price < ema50 ? 'BEARISH' : 'FLAT';
    const atrState = atrRatio < 0.8 ? 'past' : atrRatio > 1.8 ? 'juda yuqori' : 'barqaror';
    const pullbackText = nearEma
        ? '✅ EMA200 yaqinida, pullback tasdiqlandi'
        : inBreakoutZone
            ? `⚡️ Momentum break-out (EMA200 dan ${deviationPercent.toFixed(2)}% uzoqda)`
            : `⚠️ Narx EMA200 dan ${deviationPercent.toFixed(2)}% uzoqda`;

    const { swingLow, swingHigh } = calculateSwingLevels(lows, highs, 10);

    return {
        price,
        ema200,
        ema50,
        rsi14,
        atrCurrent,
        atrBaseline,
        atrRatio,
        deviationPercent,
        nearEma,
        inBreakoutZone,
        trendBias,
        shortTrendBias,
        atrState,
        pullbackText,
        riskScore,
        safeTrade,
        swingLow,
        swingHigh
    };
}

function determineFinalSignal(strategySignal, aiSignal) {
    const strat = (strategySignal || 'NEUTRAL').toUpperCase();
    const ai = (aiSignal || 'NEUTRAL').toUpperCase();
    if (ai === 'NEUTRAL' || strat === ai) return strat;
    return strat;
}

// Function to analyze market with the new strategy server
async function analyzeWithStrategyServer(data, symbol = 'XAU/USD') {
    try {
        const payload = {
            symbol: symbol,
            open: data.open,
            high: data.high,
            low: data.low,
            close: data.close,
            volume: data.volume
        };

        const response = await axios.post(STRATEGY_SERVER_URL, payload, {
            timeout: 15000 // 15 seconds timeout for more complex analysis
        });

        return response.data;
    } catch (error) {
        console.error('Error from strategy server:', error.message);
        console.error('Make sure strategy server is running on http://localhost:5000/analyze');

        // Return a neutral result instead of throwing error
        return {
            signal: 'NEUTRAL',
            entry: null,
            sl: null,
            tp: null,
            reason: 'SERVER_ERROR',
            confidence: 0.0
        };
    }
}

// Main analysis loop
async function analyzeMarket() {
    try {
        console.log(`Starting market analysis for XAU/USD (${TIMEFRAME_LABEL})...`);

        // Fetch latest OHLCV data for XAU/USD
        const data = await fetchOHLCV('XAU/USD', TIMEFRAME, 320); // 15-minute timeframe
        const snapshot = buildRiskSnapshot(data);

        // Get the latest candle time
        const latestCandleTime = data.timestamps[data.timestamps.length - 1];

        // Only process if it's a new candle (not already processed)
        if (latestCandleTime <= lastCandleTime) {
            console.log('Candle already processed, skipping...');
            return;
        }

        console.log(`Processing new candle at ${new Date(latestCandleTime).toISOString()}`);
        lastCandleTime = latestCandleTime;

        // Analyze with the new strategy server
        const strategyResult = await analyzeWithStrategyServer(data, 'XAU/USD');
        console.log('Strategy Analysis:', strategyResult);

        const normalizedSignal = (strategyResult.signal || 'NEUTRAL').toUpperCase();

        if (strategyResult && normalizedSignal !== 'NEUTRAL') {
            // Check if signal confidence is high enough
            if (strategyResult.confidence >= 0.6) { // At least 60% confidence
                // Check if enough time has passed since last alert
                if (Date.now() - lastAlert > ALERT_COOLDOWN) {
                    // Send alert to all users
                    const message = formatSignalMessage({
                        symbol: 'XAU/USD',
                        timeframe: TIMEFRAME_LABEL,
                        strategyResult,
                        snapshot
                    });

                    // Broadcast to all users (we'll send to users who have started the bot)
                    // In a real implementation, you'd have a list of subscribed chat IDs
                    console.log('Sending alert:', message);

                    // For now, we'll just log it - in real implementation, broadcast to all users
                    // await bot.telegram.sendMessage(chatId, message);

                    lastAlert = Date.now();
                } else {
                    console.log('Alert cooldown active, skipping...');
                }
            } else {
                console.log(`Signal confidence too low: ${(strategyResult.confidence * 100).toFixed(1)}%. Required: >=60%.`);
            }
        } else {
            console.log('No valid signal generated from strategy server');
        }
    } catch (error) {
        console.error('Error in analyzeMarket:', error.message);
    }
}

// Function to format signal message
function formatSignalMessage({ symbol, timeframe, strategyResult, snapshot }) {
    const strategySignal = (strategyResult.signal || 'NEUTRAL').toUpperCase();
    const aiSignalRaw = strategyResult.aiSignal || 'NEUTRAL';
    const aiSignal = aiSignalRaw.toUpperCase();
    const aiConfidence = strategyResult.aiConfidence ?? 0;
    const finalSignal = determineFinalSignal(strategySignal, aiSignal);
    const riskEmoji = snapshot.safeTrade ? '✅' : '⚠️';
    const trendText = snapshot.trendBias === 'BULLISH'
        ? 'Yuksaluvchi trend (narx EMA200 dan yuqori)'
        : snapshot.trendBias === 'BEARISH'
            ? 'Pasayuvchi trend (narx EMA200 dan past)'
            : 'Trend noaniq (narx EMA200 atrofida)';
    const trend50Text = snapshot.shortTrendBias === 'BULLISH'
        ? 'EMA50 ham yuqoriga qaratilgan (momentum BUY bilan)'
        : snapshot.shortTrendBias === 'BEARISH'
            ? 'EMA50 pastga og\'di (momentum SELL bilan)'
            : 'EMA50 neytral, momentum yetarli emas';

    const entry = strategyResult.entry ?? snapshot.price;
    let sl = strategyResult.sl;
    let tp = strategyResult.tp;
    if (!sl) {
        sl = finalSignal === 'BUY' ? snapshot.swingLow : snapshot.swingHigh;
    }
    if (!tp && typeof sl === 'number' && typeof entry === 'number') {
        const riskDistance = Math.abs(entry - sl);
        tp = finalSignal === 'BUY' ? entry + riskDistance * 2 : entry - riskDistance * 2;
    }

    const formatPrice = (value) => (typeof value === 'number' ? value.toFixed(2) : 'N/A');

    return `📊 ${symbol} ${timeframe} Smart Risk Assistant
🧭 Trend200: ${trendText}
📉 Trend50: ${trend50Text}
↩️ Pullback/Momentum: ${snapshot.pullbackText}
🏁 Signal: ${finalSignal} ${finalSignal === 'BUY' ? '🟢' : finalSignal === 'SELL' ? '🔴' : '⚪️'}
🤖 AI Signal: ${aiSignal} (ishonch ${aiConfidence.toFixed(2)})
🎯 Yakuniy signal: ${finalSignal}
⚖️ Xavf darajasi: ${snapshot.riskScore.toFixed(1)}% ${riskEmoji} (maks ${MAX_RISK_ALLOWED}%)
🧭 Xulosa: ${snapshot.safeTrade ? 'XAVFSIZ / TAVSIYA QILINGAN' : 'YUQORI XAVF / QATNASHMANG'} - ${snapshot.safeTrade ? 'Tavsiya qilinadi' : 'Qatnashmang'}
💰 Narx: ${formatPrice(snapshot.price)}
📈 EMA200: ${formatPrice(snapshot.ema200)} | EMA50: ${formatPrice(snapshot.ema50)} (farq ${snapshot.deviationPercent.toFixed(2)}%)
📊 RSI14: ${snapshot.rsi14.toFixed(2)} (prefer 40-60 koridor)
🌪️ ATR(14): ${formatPrice(snapshot.atrCurrent)} | O'rtacha 10: ${formatPrice(snapshot.atrBaseline)} (holat: ${snapshot.atrState})
🛡️ Stop Loss: ${formatPrice(sl)}
🎯 Take Profit: ${formatPrice(tp)}
⏱️ Avto-signal: Sniper ${TIMEFRAME_LABEL} monitoring`;
}



// Set up the analysis interval
function startMarketAnalysis() {
    // Run analysis immediately
    analyzeMarket();

    // Run analysis every 15 minutes for XAU/USD
    setInterval(analyzeMarket, 15 * 60 * 1000);

    console.log('Market analysis loop started for XAU/USD (15m)...');
}

// Telegram command handlers
bot.start((ctx) => {
    ctx.reply(`🎯 SMC+AI XAU/USD Trading Bot is active!

This bot monitors XAU/USD for trading signals based on:
• Smart Money Concepts (SMC)
• AI Predictions
• Risk Management

Commands available:
/analyze - Force immediate analysis of XAU/USD
/status - Show current market status

Signals include Entry, Stop Loss, and Take Profit levels.`);
});

bot.command('analyze', async (ctx) => {
    try {
        await ctx.reply('🔄 Running manual market analysis for XAU/USD...');
        await analyzeMarket();
        await ctx.reply('✅ Analysis completed. Check console for results.');
    } catch (error) {
        console.error('Error in manual analysis:', error.message);
        await ctx.reply('❌ Error during analysis. Check logs.');
    }
});

bot.command('status', async (ctx) => {
    try {
        const data = await fetchOHLCV('XAU/USD', TIMEFRAME, 320);
        const snapshot = buildRiskSnapshot(data);
        const strategyResult = await analyzeWithStrategyServer(data, 'XAU/USD');
        const message = formatSignalMessage({
            symbol: 'XAU/USD',
            timeframe: TIMEFRAME_LABEL,
            strategyResult,
            snapshot
        });

        await ctx.reply(message);
    } catch (error) {
        console.error('Error in status command:', error.message);
        await ctx.reply('? Error retrieving market status.');
    }
});

// Start the bot
bot.launch();

// Start the market analysis loop
startMarketAnalysis();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

console.log(`XAU/USD Trading Bot is running on ${TIMEFRAME_LABEL} data...`);


