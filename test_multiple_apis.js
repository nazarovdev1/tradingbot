require('dotenv').config();
const { Telegraf } = require('telegraf');
const axios = require('axios');

const bot = new Telegraf(process.env.BOT_TOKEN);

// Farkli API'larni sinash uchun funksiya
async function fetchXAUUSDData() {
    // Birinchi TwelveData'dan sinab ko'ramiz
    if (process.env.TWELVEDATA_KEY) {
        try {
            const response = await axios.get('https://api.twelvedata.com/time_series', {
                params: {
                    symbol: 'XAU/USD',
                    interval: '15min',
                    outputsize: 100,
                    apikey: process.env.TWELVEDATA_KEY
                }
            });

            if (response.data.status !== 'error' && response.data.values) {
                console.log('TwelveData ishlayapti');
                const values = Array.isArray(response.data.values) ? response.data.values.slice().reverse() : [];
                return {
                    open: values.map(item => parseFloat(item.open)),
                    high: values.map(item => parseFloat(item.high)),
                    low: values.map(item => parseFloat(item.low)),
                    close: values.map(item => parseFloat(item.close)),
                    volume: values.map(item => parseFloat(item.volume || 0)),
                    timestamps: values.map(item => new Date(item.datetime).getTime())
                };
            }
        } catch (error) {
            console.log('TwelveData ishlamadi:', error.message);
        }
    }
    
    // Agar TwelveData ishlamasa, Alpha Vantage API'dan foydalanamiz
    if (process.env.ALPHA_VANTAGE_KEY) {
        try {
            const response = await axios.get('https://www.alphavantage.co/query', {
                params: {
                    function: 'FX_INTRADAY',
                    from_symbol: 'XAU',
                    to_symbol: 'USD',
                    interval: '15min',
                    outputsize: 'compact',
                    apikey: process.env.ALPHA_VANTAGE_KEY
                }
            });

            // Alpha Vantage format: "Time Series FX (15min)"
            const timeSeriesKey = Object.keys(response.data).find(key => key.startsWith('Time Series FX'));
            if (timeSeriesKey && response.data[timeSeriesKey]) {
                console.log('Alpha Vantage ishlayapti');
                const data = response.data[timeSeriesKey];
                const sortedData = Object.entries(data).sort((a, b) => new Date(a[0]) - new Date(b[0])); // Eski ma'lumotlardan yangisiga
                return {
                    open: sortedData.map(([time, values]) => parseFloat(values['1. open'])),
                    high: sortedData.map(([time, values]) => parseFloat(values['2. high'])),
                    low: sortedData.map(([time, values]) => parseFloat(values['3. low'])),
                    close: sortedData.map(([time, values]) => parseFloat(values['4. close'])),
                    volume: sortedData.map(([time, values]) => parseFloat(values['5. volume'])),
                    timestamps: sortedData.map(([time]) => new Date(time).getTime())
                };
            }
        } catch (error) {
            console.log('Alpha Vantage ishlamadi:', error.message);
        }
    }

    // Agar ikkalasi ham ishlamasa, yana alternativ variant sifatida binance dan XAUUSDT (synthetic) ma'lumot olishga harakat qilamiz
    try {
        // Using Binance to get XAUUSDT which is a synthetic representation
        const response = await axios.get('https://api.binance.com/api/v3/klines', {
            params: {
                symbol: 'XAUUSDT',
                interval: '15m',
                limit: 100
            }
        });

        if (response.data && response.data.length > 0) {
            console.log('Binance XAUUSDT ma\'lumoti olingan');
            return {
                open: response.data.map(candle => parseFloat(candle[1])),
                high: response.data.map(candle => parseFloat(candle[2])),
                low: response.data.map(candle => parseFloat(candle[3])),
                close: response.data.map(candle => parseFloat(candle[4])),
                volume: response.data.map(candle => parseFloat(candle[7])),
                timestamps: response.data.map(candle => candle[0])
            };
        }
    } catch (error) {
        console.log('Binance ham ishlamadi:', error.message);
    }

    throw new Error('Hech qanday API ishlamadi. TwelveData, Alpha Vantage yoki Binance ma\'lumoti ololmadik.');
}

// Test funksiyasini chaqirish
fetchXAUUSDData()
    .then(data => {
        console.log('So\'nggi narx:', data.close[data.close.length - 1]);
        console.log('Ma\'lumotlar soni:', data.close.length);
    })
    .catch(error => {
        console.error('XAU/USD ma\'lumoti olinmadi:', error.message);
    });