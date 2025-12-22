import axios from 'axios';

const API_BASE_URL = 'https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev';

async function testCompleteOTPFlow() {
    console.log('🧪 Testing Complete OTP Flow...\n');
    
    try {
        // Test with a known debtor ID
        const testNationalId = '1450200007861'; // User mentioned this ID
        
        console.log('📱 Step 1: Requesting OTP for national ID:', testNationalId);
        
        const otpResponse = await axios.post(`${API_BASE_URL}/api/debtors/login`, {
            national_id: testNationalId,
            login_method: 'email'
        });
        
        console.log('✅ OTP Request Response:');
        console.log('Status:', otpResponse.status);
        console.log('Data:', JSON.stringify(otpResponse.data, null, 2));
        
        // Check if response contains any OTP value (which should NOT be there)
        const responseStr = JSON.stringify(otpResponse.data).toLowerCase();
        if (responseStr.includes('otp') && (responseStr.includes('123456') || responseStr.includes('"otp":'))) {
            console.log('❌ ERROR: OTP value found in response!');
            console.log('Response contains OTP:', responseStr);
        } else {
            console.log('✅ Good: No OTP value exposed in API response');
        }
        
        // Check if email was properly masked
        if (otpResponse.data.masked_email && otpResponse.data.masked_email.includes('@')) {
            console.log('✅ Email properly masked:', otpResponse.data.masked_email);
        } else {
            console.log('⚠️  No masked email in response');
        }
        
    } catch (error) {
        console.error('❌ Error during OTP flow test:', error.response?.data || error.message);
    }
}

async function testEmailLambdaDirectly() {
    console.log('\n📧 Testing Email Lambda Directly...\n');
    
    try {
        const testEmail = {
            email: 'hello@poweramc.co',
            otp: '999999',
            name: 'Test User'
        };
        
        const response = await axios.post(`${API_BASE_URL}/email/send-otp`, testEmail);
        
        console.log('✅ Email Lambda Response:');
        console.log('Status:', response.status);
        console.log('Data:', JSON.stringify(response.data, null, 2));
        
    } catch (error) {
        console.error('❌ Email Lambda Error:', error.response?.data || error.message);
    }
}

async function runAllTests() {
    await testCompleteOTPFlow();
    await testEmailLambdaDirectly();
    
    console.log('\n🎯 Summary:');
    console.log('1. Backend deployed with GoDaddy SMTP configuration');
    console.log('2. Frontend deployed with complete OTP display removal');  
    console.log('3. Cache-busting headers applied for fresh browser load');
    console.log('\n📱 Next step: Test in browser and clear all browser cache if OTP still appears');
}

runAllTests();