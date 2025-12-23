#!/usr/bin/env node
/**
 * Test OTP Email via Production API
 */

const https = require('https');

const API_URL = 'https://29o7gp9n8l.execute-api.ap-southeast-1.amazonaws.com/dev/email/send-otp';

const payload = JSON.stringify({
    email: 'tilakagrawal7777@gmail.com',
    otp: '789456',
    name: 'ศราวุธ ชัยมงคล'
});

console.log('🧪 Testing Email Service via Production API');
console.log('=' .repeat(60));
console.log('API Endpoint:', API_URL);
console.log('National ID: 1100100051224');
console.log('To: tilakagrawal7777@gmail.com');
console.log('OTP: 789456');
console.log('');
console.log('📡 Sending request...');
console.log('');

const options = {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': payload.length
    }
};

const req = https.request(API_URL, options, (res) => {
    let data = '';

    res.on('data', (chunk) => {
        data += chunk;
    });

    res.on('end', () => {
        console.log('📋 Response:');
        console.log('Status Code:', res.statusCode);
        console.log('');
        
        try {
            const response = JSON.parse(data);
            console.log(JSON.stringify(response, null, 2));
            console.log('');
            
            if (response.success) {
                console.log('✅ EMAIL SENT SUCCESSFULLY via Production API!');
                console.log('📧 OTP sent to: tilakagrawal7777@gmail.com');
                console.log('📧 From: hello@poweramc.co');
                console.log('🔢 OTP Code: 789456');
                console.log('💬 Message ID:', response.messageId);
                console.log('');
                console.log('🎉 Production email service is working perfectly!');
                console.log('');
                console.log('=' .repeat(60));
                console.log('✅ READY FOR DEBTOR LOGIN TEST');
                console.log('');
                console.log('Next Steps:');
                console.log('1. Go to: http://debtor-portal-frontend-dev.s3-website-ap-southeast-1.amazonaws.com');
                console.log('2. Enter National ID: 1100100051224');
                console.log('3. Check email for OTP');
                console.log('4. Login successfully!');
                process.exit(0);
            } else {
                console.log('❌ EMAIL FAILED!');
                console.log('Error:', response.error);
                process.exit(1);
            }
        } catch (error) {
            console.log('Raw Response:', data);
            console.error('Parse Error:', error.message);
            process.exit(1);
        }
    });
});

req.on('error', (error) => {
    console.error('');
    console.error('❌ REQUEST FAILED!');
    console.error('Error:', error.message);
    process.exit(1);
});

req.write(payload);
req.end();
