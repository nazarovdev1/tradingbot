const axios = require('axios');

async function testStrategyServer() {
    console.log('Strategy server test qilinmoqda...');
    
    try {
        // Oddiy test ma'lumotlari
        const testData = {
            symbol: 'XAU/USD',
            open: [2660, 2662, 2661, 2663, 2662, 2664, 2663, 2665, 2664, 2666],
            high: [2665, 2667, 2666, 2668, 2667, 2669, 2668, 2670, 2669, 2671],
            low: [2658, 2660, 2659, 2661, 2660, 2662, 2661, 2663, 2662, 2664],
            close: [2663, 2665, 2664, 2666, 2665, 2667, 2666, 2668, 2667, 2669],
            volume: [100, 120, 110, 130, 125, 140, 135, 150, 145, 160]
        };

        const response = await axios.post('http://localhost:5000/analyze', testData, {
            timeout: 10000
        });

        console.log('Strategy server javobi:', response.data);
    } catch (error) {
        console.error('Xato:', error.message);
        if (error.response) {
            console.error('Response data:', error.response.data);
            console.error('Response status:', error.response.status);
            console.error('Response headers:', error.response.headers);
        }
    }
}

testStrategyServer();