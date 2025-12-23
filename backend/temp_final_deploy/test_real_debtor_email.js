const handler = require('./email_lambda').handler;

// Test email for National ID: 1100100051224
const event = {
    httpMethod: 'POST',
    body: JSON.stringify({
        action: 'send-otp',
        email: 'tilakagrawal7777@gmail.com',
        otp: '654321',
        name: 'ศราวุธ ชัยมงคล'
    })
};

const context = {};

console.log('🧪 Sending Test OTP Email');
console.log('=' .repeat(60));
console.log('From: hello@poweramc.co');
console.log('To: tilakagrawal7777@gmail.com');
console.log('Name: ศราวุธ ชัยมงคล');
console.log('National ID: 1100100051224');
console.log('OTP: 654321');
console.log('');

handler(event, context)
    .then(result => {
        console.log('');
        console.log('📋 Response:');
        const response = JSON.parse(result.body);
        console.log(JSON.stringify(response, null, 2));
        console.log('');
        
        if (response.success) {
            console.log('✅ EMAIL SENT SUCCESSFULLY!');
            console.log('📧 OTP email sent to: tilakagrawal7777@gmail.com');
            console.log('📧 From: hello@poweramc.co');
            console.log('🔢 OTP Code: 654321');
            console.log('');
            console.log('🎉 Email system is working perfectly!');
            console.log('✅ Ready to deploy!');
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
