require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');
const express = require('express');

// Initialize bot with token
const bot = new Telegraf(process.env.BOT_TOKEN);

// Express server for uptime monitoring
const app = express();
app.get('/health', (req, res) => res.send('OK'));
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server listening on port ${PORT}`));

// Joriy narxni olish funksiyasi
async function fetchPrice(symbol) {
  try {
    const response = await axios.get('https://api.twelvedata.com/price', {
      params: {
        symbol: symbol,
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    console.log('Narx API Javobi:', JSON.stringify(response.data, null, 2)); // Debug log

    // Javob kutilgan strukturaga ega ekanligini tekshirish
    if (!response.data || typeof response.data.price === 'undefined') {
      // Javobda xatolik borligini tekshirish
      if (response.data && response.data.status === 'error') {
        console.error('Narx API Xatosi:', response.data);
        throw new Error(`API Xatosi: ${response.data.message || 'Noma\'lum xato'}`);
      }
      console.error('Kutilmagan Narx API javobi:', response.data);
      throw new Error('Noto\'g\'ri narx ma\'lumotlari qabul qilindi');
    }

    return parseFloat(response.data.price);
  } catch (error) {
    console.error('Narxni olishda xato:', error.response?.data || error.message);
    throw new Error('Narxni olishda xato');
  }
}

// RSI olish funksiyasi
async function fetchRSI(symbol, period = 14) {
  try {
    const response = await axios.get('https://api.twelvedata.com/rsi', {
      params: {
        symbol: symbol,
        interval: '1day',
        period: period,
        outputsize: 1, // Faqat so\'nggi qiymatni olish
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    console.log('RSI API Javobi:', JSON.stringify(response.data, null, 2)); // Debug log

    // Javob kutilgan strukturaga ega ekanligini tekshirish
    if (!response.data || !response.data.values || !Array.isArray(response.data.values) || response.data.values.length === 0 || typeof response.data.values[0].rsi === 'undefined') {
      // Javobda xatolik borligini tekshirish
      if (response.data.status === 'error') {
        console.error('RSI API Xatosi:', response.data);
        throw new Error(`API Xatosi: ${response.data.message || 'Noma\'lum xato'}`);
      }
      console.error('Kutilmagan RSI API javobi:', response.data);
      throw new Error('Noto\'g\'ri RSI ma\'lumotlari qabul qilindi');
    }

    return parseFloat(response.data.values[0].rsi);
  } catch (error) {
    console.error('RSI olishda xato:', error.response?.data || error.message);
    throw new Error('RSI olishda xato');
  }
}

// EMA 50 olish funksiyasi
async function fetchEMA50(symbol) {
  try {
    const response = await axios.get('https://api.twelvedata.com/ema', {
      params: {
        symbol: symbol,
        interval: '1day',
        period: 50,
        outputsize: 1, // Faqat so\'nggi qiymatni olish
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    console.log('EMA50 API Javobi:', JSON.stringify(response.data, null, 2)); // Debug log

    // Javob kutilgan strukturaga ega ekanligini tekshirish
    if (!response.data || !response.data.values || !Array.isArray(response.data.values) || response.data.values.length === 0 || typeof response.data.values[0].ema === 'undefined') {
      // Javobda xatolik borligini tekshirish
      if (response.data.status === 'error') {
        console.error('EMA50 API Xatosi:', response.data);
        throw new Error(`API Xatosi: ${response.data.message || 'Noma\'lum xato'}`);
      }
      console.error('Kutilmagan EMA50 API javobi:', response.data);
      throw new Error('Noto\'g\'ri EMA50 ma\'lumotlari qabul qilindi');
    }

    return parseFloat(response.data.values[0].ema);
  } catch (error) {
    console.error('EMA50 olishda xato:', error.response?.data || error.message);
    throw new Error('EMA50 olishda xato');
  }
}

// EMA 200 olish funksiyasi
async function fetchEMA200(symbol) {
  try {
    const response = await axios.get('https://api.twelvedata.com/ema', {
      params: {
        symbol: symbol,
        interval: '1day',
        period: 200,
        outputsize: 1, // Faqat so\'nggi qiymatni olish
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    console.log('EMA200 API Javobi:', JSON.stringify(response.data, null, 2)); // Debug log

    // Javob kutilgan strukturaga ega ekanligini tekshirish
    if (!response.data || !response.data.values || !Array.isArray(response.data.values) || response.data.values.length === 0 || typeof response.data.values[0].ema === 'undefined') {
      // Javobda xatolik borligini tekshirish
      if (response.data.status === 'error') {
        console.error('EMA200 API Xatosi:', response.data);
        throw new Error(`API Xatosi: ${response.data.message || 'Noma\'lum xato'}`);
      }
      console.error('Kutilmagan EMA200 API javobi:', response.data);
      throw new Error('Noto\'g\'ri EMA200 ma\'lumotlari qabul qilindi');
    }

    return parseFloat(response.data.values[0].ema);
  } catch (error) {
    console.error('EMA200 olishda xato:', error.response?.data || error.message);
    throw new Error('EMA200 olishda xato');
  }
}

// Sham ma'lumotlarini olish funksiyasi
async function fetchCandleData(symbol) {
  try {
    const response = await axios.get('https://api.twelvedata.com/time_series', {
      params: {
        symbol: symbol,
        interval: '1day',
        outputsize: 2, // Oxirgi 2 shamlarni olish
        apikey: process.env.TWELVEDATA_KEY
      }
    });

    console.log('Sham API Javobi:', JSON.stringify(response.data, null, 2)); // Debug log

    // Javob kutilgan strukturaga ega ekanligini tekshirish
    if (!response.data || !response.data.values || !Array.isArray(response.data.values) || response.data.values.length < 2) {
      // Javobda xatolik borligini tekshirish
      if (response.data && response.data.status === 'error') {
        console.error('Sham API Xatosi:', response.data);
        throw new Error(`API Xatosi: ${response.data.message || 'Noma\'lum xato'}`);
      }
      console.error('Kutilmagan Sham API javobi:', response.data);
      throw new Error('Noto\'g\'ri sham ma\'lumotlari qabul qilindi');
    }

    return response.data.values; // Oxirgi 2 shamlar massivini qaytaradi
  } catch (error) {
    console.error('Sham ma\'lumotlarini olishda xato:', error.response?.data || error.message);
    throw new Error('Sham ma\'lumotlarini olishda xato');
  }
}

// Sham patternlarini aniqlash funksiyasi (Shovqinli/To'qimli Qamrov)
function detectCandlePattern(candles) {
  if (candles.length < 2) {
    return { pattern: 'YOK', description: 'Patternni aniqlash uchun yetarli ma\'lumot yo\'q' };
  }

  // Oxirgi 2 shamlarni olish
  const prevCandle = candles[1]; // Oldingi sham
  const currentCandle = candles[0]; // Joriy sham

  // Sham tanasining o'lchamlarini hisoblash (ochilish va yopilish orasidagi mutlaq farq)
  const prevBody = Math.abs(parseFloat(prevCandle.open) - parseFloat(prevCandle.close));
  const currentBody = Math.abs(parseFloat(currentCandle.open) - parseFloat(currentCandle.close));

  // Sham ranglarini aniqlash (Qizil = To'qimli, Yashil = Shovqinli)
  const isPrevRed = parseFloat(prevCandle.open) > parseFloat(prevCandle.close);
  const isPrevGreen = parseFloat(prevCandle.open) < parseFloat(prevCandle.close);
  const isCurrentRed = parseFloat(currentCandle.open) > parseFloat(currentCandle.close);
  const isCurrentGreen = parseFloat(currentCandle.open) < parseFloat(currentCandle.close);

  // Shovqinli Qamrov: Oldingi qizil sham, joriy yashil sham, joriy tanasi oldingisini to'liq qamrab oladi
  if (isPrevRed && isCurrentGreen && currentBody > prevBody) {
    // Joriy sham oldingi shamni to'liq qamrab olganligini tekshirish
    if (parseFloat(currentCandle.close) > parseFloat(prevCandle.open) &&
        parseFloat(currentCandle.open) < parseFloat(prevCandle.close)) {
      return {
        pattern: 'SHOVQINLI_QAMROV',
        description: 'Shovqinli Qamrov Patterni Aniqlandi'
      };
    }
  }

  // To'qimli Qamrov: Oldingi yashil sham, joriy qizil sham, joriy tanasi oldingisini to'liq qamrab oladi
  if (isPrevGreen && isCurrentRed && currentBody > prevBody) {
    // Joriy sham oldingi shamni to'liq qamrab olganligini tekshirish
    if (parseFloat(currentCandle.open) > parseFloat(prevCandle.close) &&
        parseFloat(currentCandle.close) < parseFloat(prevCandle.open)) {
      return {
        pattern: 'TO\'QIMLI_QAMROV',
        description: 'To\'qimli Qamrov Patterni Aniqlandi'
      };
    }
  }

  return { pattern: 'YOK', description: 'Hech Qanday Qamrov Patterni Aniqlanmadi' };
}

// 3X tasdiqlash bilan signalni tahlil qilish funksiyasi
function analyzeSignal(price, rsi, ema50, ema200, candlePattern) {
  // Barcha ma'lumotlar mavjudligini tekshirish
  if (typeof rsi !== 'number' || typeof ema50 !== 'number' || typeof ema200 !== 'number' || typeof price !== 'number' ||
      isNaN(rsi) || isNaN(ema50) || isNaN(ema200) || isNaN(price) || !candlePattern) {
    return {
      signal: 'XATO',
      probability: 0,
      reason: 'Noto\'g\'ri ko\'rsatkich qiymatlari qabul qilindi',
      conditionsMet: 0
    };
  }

  // Shart sanagichlarini ishga tushirish
  let buyConditionsMet = 0;
  let sellConditionsMet = 0;
  const conditions = {
    trendUp: ema50 > ema200,
    trendDown: ema50 < ema200,
    rsiOversold: rsi < 35,
    rsiOverbought: rsi > 65,
    bullishPattern: candlePattern.pattern === 'SHOVQINLI_QAMROV',
    bearishPattern: candlePattern.pattern === 'TO\'QIMLI_QAMROV',
    priceAboveEMA50: price > ema50,
    priceBelowEMA50: price < ema50
  };

  // SOTIB OLISH shartlarini tekshirish
  if (conditions.trendUp && conditions.rsiOversold && conditions.bullishPattern && conditions.priceAboveEMA50) {
    buyConditionsMet = 4;
    return {
      signal: 'SOTIB_OLISH',
      probability: calculateProbability(buyConditionsMet, 'SOTIB_OLISH'),
      trend: conditions.trendUp ? 'O\'suvchi Trend' : 'Tushuvchi Trend',
      pattern: candlePattern.pattern,
      reason: `4/4 shart bajarildi: ${conditions.trendUp ? 'Trend Yuqoriga (EMA50 > EMA200), ' : ''}RSI Sotuvga Qiyson, Shovqinli Qamrov Patterni, EMA50 Dan Yuqori Narx`,
      conditionsMet: buyConditionsMet
    };
  }

  // SOTISH shartlarini tekshirish
  if (conditions.trendDown && conditions.rsiOverbought && conditions.bearishPattern && conditions.priceBelowEMA50) {
    sellConditionsMet = 4;
    return {
      signal: 'SOTISH',
      probability: calculateProbability(sellConditionsMet, 'SOTISH'),
      trend: conditions.trendDown ? 'Tushuvchi Trend' : 'O\'suvchi Trend',
      pattern: candlePattern.pattern,
      reason: `4/4 shart bajarildi: ${conditions.trendDown ? 'Trend Pastga (EMA50 < EMA200), ' : ''}RSI Sotuvga Qiyson, To'qimli Qamrov Patterni, EMA50 Dan Past Narx`,
      conditionsMet: sellConditionsMet
    };
  }

  // Ehtimoliy signallar uchun qisman shartlarni tekshirish
  // Qancha SOTIB OLISH shartlari bajarilganini sanash
  if (conditions.trendUp) buyConditionsMet++;
  if (conditions.rsiOversold) buyConditionsMet++;
  if (conditions.bullishPattern) buyConditionsMet++;
  if (conditions.priceAboveEMA50) buyConditionsMet++;

  // Qancha SOTISH shartlari bajarilganini sanash
  if (conditions.trendDown) sellConditionsMet++;
  if (conditions.rsiOverbought) sellConditionsMet++;
  if (conditions.bearishPattern) sellConditionsMet++;
  if (conditions.priceBelowEMA50) sellConditionsMet++;

  // Eng ko'p bajarilgan shartlar asosida signalni aniqlash
  if (buyConditionsMet >= sellConditionsMet && buyConditionsMet > 0) {
    return {
      signal: buyConditionsMet >= 3 ? 'SOTIB_OLISH' : 'NEYTRAL',
      probability: calculateProbability(buyConditionsMet, 'SOTIB_OLISH'),
      trend: conditions.trendUp ? 'O\'suvchi Trend' : 'Tushuvchi Trend',
      pattern: candlePattern.pattern,
      reason: `${buyConditionsMet}/4 SOTIB OLISH shartlari bajarildi`,
      conditionsMet: buyConditionsMet
    };
  } else if (sellConditionsMet > 0) {
    return {
      signal: sellConditionsMet >= 3 ? 'SOTISH' : 'NEYTRAL',
      probability: calculateProbability(sellConditionsMet, 'SOTISH'),
      trend: conditions.trendDown ? 'Tushuvchi Trend' : 'O\'suvchi Trend',
      pattern: candlePattern.pattern,
      reason: `${sellConditionsMet}/4 SOTISH shartlari bajarildi`,
      conditionsMet: sellConditionsMet
    };
  }

  // Agar kuchli shartlar bajarilmagan bo'lsa, NEYTRAL qilish
  return {
    signal: 'NEYTRAL',
    probability: calculateProbability(0, 'NEYTRAL'),
    trend: ema50 > ema200 ? 'O\'suvchi Trend' : ema50 < ema200 ? 'Tushuvchi Trend' : 'Tomonlarga',
    pattern: candlePattern.pattern,
    reason: 'Aniq trend yoki signal shartlari bajarilmadi',
    conditionsMet: 0
  };
}

// Bajarilgan shartlar asosida ehtimollikni hisoblash funksiyasi
function calculateProbability(conditionsMet, signalType) {
  if (signalType === 'NEYTRAL' || conditionsMet === 0) {
    return Math.floor(Math.random() * 41); // 0-40% neytral uchun
  }

  // SOTIB OLISH/SOTISH signallari uchun
  switch(conditionsMet) {
    case 4:
      return Math.floor(Math.random() * 6) + 90; // 90-95%
    case 3:
      return Math.floor(Math.random() * 11) + 75; // 75-85%
    case 2:
      return Math.floor(Math.random() * 11) + 55; // 55-65%
    case 1:
      return Math.floor(Math.random() * 21) + 20; // 20-40%
    default:
      return Math.floor(Math.random() * 41); // 0-40% zaxira variant
  }
}

// Signal javobini formatlash funksiyasi
function formatSignalResponse(price, rsi, ema50, ema200, candlePattern, signal, probability, trend, reason, conditionsMet) {
  if (signal === 'XATO') {
    return `⚠️ *Signal Yaratishda Xatolik*

${reason}

*Iltimos keyinroq qayta urinib ko'ring yoki API sozlamalarini tekshiring.*`;
  }

  // Sham patterni aniqlanganmi aniqlash
  const patternDetected = candlePattern.pattern !== 'YOK';

  // Signal nomini o'zbekcha ko'rinishga o'tkazish
  let signalText;
  switch(signal) {
    case 'SOTIB_OLISH':
      signalText = 'SOTIB OLISH';
      break;
    case 'SOTISH':
      signalText = 'SOTISH';
      break;
    case 'NEYTRAL':
      signalText = 'NEYTRAL';
      break;
    default:
      signalText = signal;
  }

  return `📊 *XAU/USD Kengaytirilgan Savdo Signali*

💰 *Narx:* $${price.toFixed(2)}
📊 *RSI (14):* ${rsi.toFixed(2)}
📊 *EMA (50):* $${ema50.toFixed(2)}
📊 *EMA (200):* $${ema200.toFixed(2)}
📈 *Sham Patterni:* ${patternDetected ? '✅ HA' : '❌ YO\'Q'}
${trend}
🎯 *Signal:* ${signalText}
🔮 *Ehtimollik:* ${probability}%

💡 *Sabablar:*
  • ${conditionsMet}/4 shart bajarildi
  • ${reason}

*Eslatma: Bular faqat axborot maqsadida. Har doim o'zingiz savdo qilishdan oldin o'zingiz tekshiruv qiling.*`;
}

// Botni ishga tushirish komandasi
bot.start((ctx) => {
  const welcomeMessage = 'Forex Signal Botga Xush Kelibsiz! 🤖\n\nTugmani bosing va XAU/USD (Oltin) bo\'yicha savdo signallarini oling.';
  const keyboard = {
    reply_markup: {
      keyboard: [
        [{ text: 'XAUUSD 🟡 OLTIN' }]
      ],
      resize_keyboard: true
    }
  };
  ctx.reply(welcomeMessage, keyboard);
});

// XAUUSD tugmasini bosishni qo'llab-quvvatlash
bot.hears('XAUUSD 🟡 OLTIN', async (ctx) => {
  try {
    // Yuklanayotgan xabar yuborish
    await ctx.reply('⏳ XAU/USD signali hisoblanmoqda...');

    // Texnik ko'rsatkichlarni individual xatoliklarni qo'llab-quvvatlab olish
    // TwelveData API bo'yicha oltin uchun XAU belgisi qo'llaniladi
    let price, rsi, ema50, ema200, candles;
    try {
      [price, rsi, ema50, ema200, candles] = await Promise.all([
        fetchPrice('XAU/USD'),
        fetchRSI('XAU/USD', 14),
        fetchEMA50('XAU/USD'),
        fetchEMA200('XAU/USD'),
        fetchCandleData('XAU/USD')
      ]);
    } catch (error) {
      // Agar qandaydir so'rovda xatolik bo'lsa, ularni alohida tekshirib chiqamiz
      price = await fetchPrice('XAU/USD').catch(err => {
        console.error('Narxni olishda xatolik:', err.message);
        return null;
      });

      rsi = await fetchRSI('XAU/USD', 14).catch(err => {
        console.error('RSI olishda xatolik:', err.message);
        return null;
      });

      ema50 = await fetchEMA50('XAU/USD').catch(err => {
        console.error('EMA50 olishda xatolik:', err.message);
        return null;
      });

      ema200 = await fetchEMA200('XAU/USD').catch(err => {
        console.error('EMA200 olishda xatolik:', err.message);
        return null;
      });

      candles = await fetchCandleData('XAU/USD').catch(err => {
        console.error('Sham ma\'lumotlarini olishda xatolik:', err.message);
        return null;
      });

      // Agar qandaydir qiymatlar null bo'lsa, tekshiramiz
      if (price === null || rsi === null || ema50 === null || ema200 === null || candles === null) {
        let errorMessage = 'Ma\'lumotlarni olishda xatolik: ';
        if (price === null) errorMessage += 'Narx, ';
        if (rsi === null) errorMessage += 'RSI, ';
        if (ema50 === null) errorMessage += 'EMA50, ';
        if (ema200 === null) errorMessage += 'EMA200, ';
        if (candles === null) errorMessage += 'Sham Ma\'lumotlari, ';
        errorMessage = errorMessage.slice(0, -2); // Vergul va bo'sh joy olib tashlash
        throw new Error(errorMessage);
      }
    }

    // Sham patternini aniqlash
    const candlePattern = detectCandlePattern(candles);

    // Yangilangan strategiya bo'yicha signalni tahlil qilish
    const signalAnalysis = analyzeSignal(price, rsi, ema50, ema200, candlePattern);

    // Format va javob yuborish
    const response = formatSignalResponse(
      price,
      rsi,
      ema50,
      ema200,
      candlePattern,
      signalAnalysis.signal,
      signalAnalysis.probability,
      signalAnalysis.trend,
      signalAnalysis.reason,
      signalAnalysis.conditionsMet
    );

    await ctx.reply(response, { parse_mode: 'Markdown' });
  } catch (error) {
    console.error('Signal so\'rovi qayta ishlanayotganda xatolik:', error);
    await ctx.reply('❌ Ma\'lumotlarni olishda xatolik. Iltimos keyinroq qaytadan urinib ko\'ring.');
  }
});

// Start the bot
bot.launch();

console.log('Forex Signal Bot is running...');

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
