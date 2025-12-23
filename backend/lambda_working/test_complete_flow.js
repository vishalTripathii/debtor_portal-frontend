const axios = require('axios');

async function testCompleteOTPFlow() {
    console.log('🧪 TESTING COMPLETE OTP FLOW');
    console.log('=' .repeat(50));
    
    try {
        // Test with a real debtor record
        console.log('📱 Step 1: Requesting OTP for National ID: 1450200007861');
        
        const loginResponse = await axios.post(
            'https://jxnu8wrip2.execute-api.ap-southeast-1.amazonaws.com/dev/api/debtor-login/', 
            {
                login_value: '1450200007861',
                login_method: 'national_id', 
                language: 'en'
            },
            {
                headers: {
                    'Content-Type': 'application/json'
                }
            }
        );
        
        console.log('✅ API Response received');
        console.log('Response data:', JSON.stringify(loginResponse.data, null, 2));
        
        // Check if OTP is in response (should NOT be there)
        if (loginResponse.data.otp) {
            console.log('❌ PROBLEM: OTP found in API response!');
            console.log('🔑 OTP Value:', loginResponse.data.otp);
            console.log('⚠️  This should NOT appear - needs frontend fix');
        } else {
            console.log('✅ GOOD: No OTP in API response (production mode)');
        }
        
        // Check if email was sent
        if (loginResponse.data.email_sent === true) {
            console.log('✅ GOOD: Email marked as sent successfully');
        } else {
            console.log('❌ PROBLEM: Email not sent or failed');
        }
        
        console.log('📧 Masked Email:', loginResponse.data.masked_email);
        console.log('🏦 Account Count:', loginResponse.data.account_count);
        
    } catch (error) {
        console.log('❌ API Error:', error.response?.status);
        console.log('Error details:', error.response?.data || error.message);
    }
    
    console.log('\n' + '=' .repeat(50));
    console.log('📋 CHECKING REQUIREMENTS:');
    console.log('=' .repeat(50));
    console.log('1. ❓ OTP should NOT be displayed on screen');
    console.log('2. ❓ Email should be sent to debtor\'s actual email');
    console.log('3. ❓ Using Zoho SMTP (firoz.khan@welleazy.com)');
    console.log('4. ❓ No demo OTP references in frontend');
}

testCompleteOTPFlow();