const axios = require('axios');

async function testStrategyServerDetailed() {
    console.log('Strategy server test qilinmoqda...');
    
    // Oddiy test ma'lumotlari
    const testData = {
        symbol: 'XAU/USD',
        open: [2660, 2662, 2661, 2663, 2662, 2664, 2663, 2665, 2664, 2666],
        high: [2665, 2667, 2666, 2668, 2667, 2669, 2668, 2670, 2669, 2671],
        low: [2658, 2660, 2659, 2661, 2660, 2662, 2661, 2663, 2662, 2664],
        close: [2663, 2665, 2664, 2666, 2665, 2667, 2666, 2668, 2667, 2669],
        volume: [100, 120, 110, 130, 125, 140, 135, 150, 145, 160]
    };

    try {
        console.log('Test ma\'lumotlari:', JSON.stringify(testData, null, 2));
        console.log('\nRequest yuborilmoqda...');
        
        const response = await axios.post('http://localhost:5000/analyze', testData, {
            timeout: 15000,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log('Status:', response.status);
        console.log('Javob:', JSON.stringify(response.data, null, 2));
    } catch (error) {
        console.error('\nXato turi:', error.constructor.name);
        console.error('Xato xabari:', error.message);
        
        if (error.response) {
            console.error('Status kod:', error.response.status);
            console.error('Xato javobi:', error.response.data);
            console.error('Headerlar:', error.response.headers);
        } else if (error.request) {
            console.error('So\'rov yuborildi, javob yo\'q:', error.request);
        } else {
            console.error('Xato tavsifi:', error);
        }
    }
}

testStrategyServerDetailed();