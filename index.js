require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Define constants for price validation
const MIN_PRICE = 1000;
const MAX_PRICE = 7000;
const MAX_RISK_ALLOWED = 40; // Maximum allowed risk percentage
const USERS_FILE = path.join(__dirname, 'users.json');

// Load subscribed users
let subscribedUsers = new Set();
if (fs.existsSync(USERS_FILE)) {
    try {
        const data = fs.readFileSync(USERS_FILE, 'utf8');
        subscribedUsers = new Set(JSON.parse(data));
        console.log(`Loaded ${subscribedUsers.size} subscribed users.`);
    } catch (e) {
        console.error('Error loading users:', e);
    }
}

function saveUsers() {
    try {
        fs.writeFileSync(USERS_FILE, JSON.stringify([...subscribedUsers]));
    } catch (e) {
        console.error('Error saving users:', e);
    }
}

// Function to fetch OHLCV data from TwelveData
async function fetchOHLCV(symbol = 'XAU/USD', timeframe = '15min', limit = 100) {
    try {
        if (!process.env.TWELVEDATA_KEY) {
            throw new Error('TWELVEDATA_KEY environment variable is not set');
        }

        const response = await axios.get('https://api.twelvedata.com/time_series', {
            params: {
                symbol: symbol,
                interval: timeframe,
                outputsize: limit,
                apikey: process.env.TWELVEDATA_KEY
            }
        });

        if (!response.data || response.data.status === 'error') {
            throw new Error(response.data?.message || 'TwelveData API returned an error');
        }

        const values = Array.isArray(response.data.values) ? response.data.values.slice().reverse() : [];
        if (values.length === 0) {
            throw new Error('TwelveData API returned no data values');
        }

        console.log('Using TwelveData API for XAU/USD');
        return {
            open: values.map(item => parseFloat(item.open)),
            high: values.map(item => parseFloat(item.high)),
            low: values.map(item => parseFloat(item.low)),
            close: values.map(item => parseFloat(item.close)),
            volume: values.map(item => parseFloat(item.volume || 0)),
            timestamps: values.map(item => new Date(item.datetime).getTime())
        };
    } catch (error) {
        console.error('Error fetching OHLCV data from TwelveData:', error.message);
        throw error;
    }
}

const bot = new Telegraf(process.env.BOT_TOKEN);
const STRATEGY_SERVER_URL = process.env.STRATEGY_SERVER_URL || 'http://localhost:5000/analyze';
const ALERT_COOLDOWN = 300000; // 5 minutes

let lastCandleTime = 0;
let lastAlert = 0;

// Function to calculate EMA (Exponential Moving Average)
function calculateEMA(values, period) {
    if (values.length < period) throw new Error(`Need at least ${period} closes for EMA`);
    const k = 2 / (period + 1);
    let ema = values.slice(0, period).reduce((sum, value) => sum + value, 0) / period;
    for (let i = period; i < values.length; i++) {
        ema = values[i] * k + ema * (1 - k);
    }
    return ema;
}

// Function to calculate RSI (Relative Strength Index)
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

// Function to calculate ATR (Average True Range)
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

// Function to calculate swing levels (highs and lows)
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

// Function to build a snapshot of risk parameters
// Updated buildRiskSnapshot to handle higher price ranges for XAU/USD
function buildRiskSnapshot(data, approvedPrices = []) {
    const closes = data.close;
    const highs = data.high;
    const lows = data.low;
    if (closes.length < 210) throw new Error('Not enough data for risk snapshot');

    const price = closes[closes.length - 1];

    // Expanded realistic price range for XAU/USD
    if (!approvedPrices.includes(price) && (price < MIN_PRICE || price > MAX_PRICE)) {
        throw new Error(`PRICE_OUT_OF_RANGE: Current price ${price} is outside the valid range (${MIN_PRICE}-${MAX_PRICE}) for XAU/USD`);
    }

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

// Function to determine the final trading signal
function determineFinalSignal(strategySignal) {
    const strat = (strategySignal || 'NEUTRAL').toUpperCase();
    console.log(`Final Signal: ${strat}`);
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
// Updated analyzeMarket to handle insufficient data gracefully
async function analyzeMarket() {
    try {
        console.log(`Starting market analysis for XAU/USD...`);

        // Fetch latest OHLCV data for XAU/USD
        const data = await fetchOHLCV('XAU/USD', '15min', 320); // 15-minute timeframe

        // Validate that we have sufficient data before proceeding
        if (!data || data.close.length < 210) {
            console.warn('Not enough data for risk snapshot. Skipping analysis for this cycle.');
            return;
        }

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
        strategyResult.signal = (strategyResult.signal || 'NEUTRAL').toUpperCase();
        console.log('Strategy Analysis:', strategyResult);

        const normalizedSignal = strategyResult.signal;

        // Send alerts ONLY for valid signals (BUY/SELL)
        if (normalizedSignal !== 'NEUTRAL') {
            // Check if enough time has passed since last alert
            if (Date.now() - lastAlert > ALERT_COOLDOWN) {
                // Send alert to all users
                const message = formatSignalMessage({
                    symbol: 'XAU/USD',
                    timeframe: '15min',
                    strategyResult,
                    snapshot
                });

                console.log('Sending alert to', subscribedUsers.size, 'users');
                console.log('Message:', message);

                // Broadcast to all subscribed users
                for (const chatId of subscribedUsers) {
                    try {
                        await bot.telegram.sendMessage(chatId, message);
                        console.log(`Sent alert to ${chatId}`);
                    } catch (error) {
                        console.error(`Failed to send to ${chatId}:`, error.message);
                    }
                }

                lastAlert = Date.now();
            } else {
                console.log('Alert cooldown active, skipping...');
            }
        } else {
            console.log('No valid signal generated (NEUTRAL)');
        }
    } catch (error) {
        console.error('Error in analyzeMarket:', error.message);
    }
}

// Function to format signal message
function formatSignalMessage({ symbol, timeframe, strategyResult, snapshot }) {
    const strategySignal = (strategyResult.signal || 'NEUTRAL').toUpperCase();
    const finalSignal = determineFinalSignal(strategySignal);
    const riskEmoji = snapshot.safeTrade ? '✅' : '⚠️';

    const entry = strategyResult.entry ?? snapshot.price;
    let sl = strategyResult.sl;
    let tp = strategyResult.tp;

    // Fallback SL/TP if not provided by strategy
    if (!sl) {
        sl = finalSignal === 'BUY' ? snapshot.swingLow : snapshot.swingHigh;
    }
    if (!tp && typeof sl === 'number' && typeof entry === 'number') {
        const riskDistance = Math.abs(entry - sl);
        tp = finalSignal === 'BUY' ? entry + riskDistance * 2 : entry - riskDistance * 2;
    }

    const formatPrice = (value) => (typeof value === 'number' ? value.toFixed(2) : 'N/A');

    // Extract SMC details if available
    const smc = strategyResult.smc_details || {};
    let aiDisplay = 'N/A';

    if (strategyResult.aiSignal === 'NEUTRAL') {
        aiDisplay = `NEUTRAL (${(strategyResult.aiConfidence * 100).toFixed(0)}% - Ishonchsiz)`;
    } else {
        aiDisplay = `${strategyResult.aiSignal} (${(strategyResult.aiConfidence * 100).toFixed(0)}%)`;
    }

    return `🚀 ${symbol} ${timeframe} SMC + AI Signal
    
🏁 Signal: ${finalSignal} ${finalSignal === 'BUY' ? '🟢' : finalSignal === 'SELL' ? '🔴' : '⚪️'}
💡 Sabab: ${strategyResult.reason || 'N/A'}
🤖 AI Tasdiqi: ${aiDisplay}

💰 Kirish (Entry): ${formatPrice(entry)}
🛡️ Stop Loss: ${formatPrice(sl)}
🎯 Take Profit: ${formatPrice(tp)}

📊 SMC Tahlili:
• Trend: ${smc.trend || 'N/A'}
• Bias: ${smc.bias || 'N/A'}
• BOS: ${smc.bos?.bullish?.length ? 'Bullish ✅' : ''} ${smc.bos?.bearish?.length ? 'Bearish 🔻' : ''}
• FVG: ${smc.fvgZones?.length || 0} ta zona
• Order Block: ${smc.orderBlocks?.length || 0} ta blok

⚖️ Risk Menejment:
• Xavf darajasi: ${snapshot.riskScore.toFixed(1)}% ${riskEmoji}
• RSI: ${snapshot.rsi14.toFixed(2)}
• ATR: ${formatPrice(snapshot.atrCurrent)}

⏱️ Vaqt: ${new Date().toLocaleString()}`;
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
    // Save user to subscribed list
    if (!subscribedUsers.has(ctx.chat.id)) {
        subscribedUsers.add(ctx.chat.id);
        saveUsers();
        console.log(`New user subscribed: ${ctx.chat.id}`);
    }

    ctx.reply(`🎯 SMC+AI XAU/USD Trading Bot is active!

✅ Siz muvaffaqiyatli obuna bo'ldingiz.
Endi bot sizga avtomatik ravishda signallarni yuboradi.

This bot monitors XAU/USD for trading signals based on:
• Smart Money Concepts (SMC)
• AI Prediction (LSTM)
• Risk Management

Commands available:
/analyze - Force immediate analysis of XAU/USD
/status - Show current market status
/start - Subscribe to auto-alerts

Signals include Entry, Stop Loss, and Take Profit levels.`);
});

bot.command('analyze', async (ctx) => {
    try {
        await ctx.reply("🔄 XAU/USD uchun qo'lda tahlil boshlanmoqda...");
        const data = await fetchOHLCV('XAU/USD', '15min', 320);

        // Validate that we have realistic data before proceeding for analyze command too
        const latestClose = data.close[data.close.length - 1];
        if (latestClose < 1200 || latestClose > 5000) {
            await ctx.reply(`⚠️ XAU/USD narxi realistik bo'lmagan qiymat: ${latestClose}. Iltimos, tarif reytingingizni tekshiring.`);
            return;
        }

        // Continue with analysis using the validated data
        const snapshot = buildRiskSnapshot(data);
        const strategyResult = await analyzeWithStrategyServer(data, 'XAU/USD');

        const message = formatSignalMessage({
            symbol: 'XAU/USD',
            timeframe: '15min',
            strategyResult,
            snapshot
        });

        await ctx.reply(message);
        console.log('Manual Analysis:', strategyResult);
    } catch (error) {
        console.error('Error in manual analysis:', error.message);
        if (error.message.includes('This symbol is available starting with Grow')) {
            await ctx.reply("⚠️ XAU/USD ma\'lumotlarini olish uchun TwelveData Grow yoki undan yuqori tarif kerak.");
        } else {
            await ctx.reply('❌ Tahlilda xatolik yuz berdi: ' + error.message);
        }
    }
});

bot.command('status', async (ctx) => {
    try {
        const data = await fetchOHLCV('XAU/USD', '15min', 320);

        // Validate that we have realistic data before proceeding for status command too
        const latestClose = data.close[data.close.length - 1];
        if (latestClose < 1200 || latestClose > 5000) {
            await ctx.reply(`⚠️ XAU/USD narxi realistik bo'lmagan qiymat: ${latestClose}.`);
            return;
        }

        const snapshot = buildRiskSnapshot(data);
        const strategyResult = await analyzeWithStrategyServer(data, 'XAU/USD');
        const message = formatSignalMessage({
            symbol: 'XAU/USD',
            timeframe: '15min',
            strategyResult,
            snapshot
        });

        await ctx.reply(message);
    } catch (error) {
        console.error('Error in status command:', error.message);
        await ctx.reply('❌ XAU/USD holatini olishda xatolik yuz berdi: ' + error.message);
    }
});

// Start the bot
bot.launch();

// Start the market analysis loop
startMarketAnalysis();

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

console.log(`XAU/USD Trading Bot is running on 15min data...`);
