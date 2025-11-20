const axios = require('axios');

// Test script to verify the integration between Node.js and Python strategy server
async function testIntegration() {
    console.log('Testing integration between Node.js and Python strategy server...');
    
    try {
        // Test data - simulated XAU/USD candle data
        const testData = {
            symbol: 'XAU/USD',
            open: [2000, 2001, 2002, 2001.5, 2003, 2002.5, 2004, 2003.5, 2005, 2004.5],
            high: [2005, 2006, 2005.5, 2007, 2006.5, 2008, 2007.5, 2009, 2008.5, 2010],
            low: [1998, 1999, 2000, 1998.5, 2001, 1999.5, 2002, 2000.5, 2003, 2001.5],
            close: [2003, 2004, 2003.5, 2006, 2005.5, 2007.5, 2006.5, 2008.5, 2007.5, 2009.5],
            volume: [1000, 1200, 1100, 1300, 1250, 1400, 1350, 1500, 1450, 1600]
        };

        console.log('Sending test data to strategy server...');
        const response = await axios.post('http://localhost:5000/analyze', testData, {
            timeout: 15000
        });

        console.log('✅ Integration test successful!');
        console.log('Response:', JSON.stringify(response.data, null, 2));
        
        return true;
    } catch (error) {
        console.error('❌ Integration test failed:', error.message);
        if (error.response) {
            console.error('Response data:', error.response.data);
            console.error('Response status:', error.response.status);
        }
        return false;
    }
}

// Run the test
testIntegration().then(success => {
    if (success) {
        console.log('\n🎉 Integration test passed! The strategy server is working correctly.');
        console.log('You can now run both servers:');
        console.log('1. Start strategy server: python strategy_server.py');
        console.log('2. Start Telegram bot: node index.js');
    } else {
        console.log('\n💥 Integration test failed. Please make sure:');
        console.log('- The strategy server is running on http://localhost:5000');
        console.log('- All required Python dependencies are installed');
        console.log('- The model files exist in the models directory');
    }
});