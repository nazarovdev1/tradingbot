require('dotenv').config();
const axios = require('axios');

async function testTwelveData() {
    try {
        console.log('Testing TwelveData API for XAU/USD...');
        
        const response = await axios.get('https://api.twelvedata.com/time_series', {
            params: {
                symbol: 'XAU/USD',
                interval: '15min',
                outputsize: 5, // Only get last 5 candles for testing
                apikey: process.env.TWELVEDATA_KEY
            }
        });

        if (response.data.status === 'error') {
            console.error('TwelveData API Error:', response.data.message);
            return;
        }

        console.log('TwelveData Response Status:', response.data.status);
        console.log('Data Values:', response.data.values);

        if (response.data.values && response.data.values.length > 0) {
            console.log('\nLast 5 candles:');
            for (let i = 0; i < Math.min(5, response.data.values.length); i++) {
                const candle = response.data.values[i];
                console.log(`Candle ${i+1}: Open: ${candle.open}, High: ${candle.high}, Low: ${candle.low}, Close: ${candle.close}, Volume: ${candle.volume}, Time: ${candle.datetime}`);
            }
            
            // Check if the price values are reasonable for XAU/USD
            const firstCandle = response.data.values[0];
            const closePrice = parseFloat(firstCandle.close);
            
            if (closePrice < 1000 || closePrice > 3000) {
                console.warn(`⚠️  Warning: Close price ${closePrice} seems unusual for XAU/USD. Should be around 2000-2100 range.`);
            } else {
                console.log(`✅ Close price ${closePrice} looks reasonable for XAU/USD`);
            }
        } else {
            console.error('No data received from TwelveData');
        }
    } catch (error) {
        console.error('Error testing TwelveData API:', error.message);
    }
}

testTwelveData();