const handler = require('./email_lambda').handler;

// Simulate Lambda event
const event = {
    httpMethod: 'POST',
    body: JSON.stringify({
        action: 'send-otp',
        email: 'hello@poweramc.co',
        otp: '',
        name: 'Test User (NID: 1100100051224)'
    })
};

const context = {};

console.log('🧪 Testing Email Lambda Function');
console.log('=' .repeat(60));
console.log('Sending test OTP email for National ID: 1100100051224');
console.log('');

handler(event, context)
    .then(result => {
        console.log('');
        console.log('📋 Response:');
        console.log(JSON.stringify(JSON.parse(result.body), null, 2));
        console.log('');
        
        const response = JSON.parse(result.body);
        if (response.success) {
            console.log('✅ EMAIL SENT SUCCESSFULLY!');
            console.log('🎉 Ready to deploy!');
            console.log('');
            console.log('📧 Check inbox at: hello@poweramc.co');
            process.exit(0);
        } else {
            console.log('❌ EMAIL FAILED!');
            console.log('Error:', response.error);
            process.exit(1);
        }
    })
    .catch(error => {
        console.error('');
        console.error('❌ TEST FAILED!');
        console.error('Error:', error.message);
        process.exit(1);
    });
