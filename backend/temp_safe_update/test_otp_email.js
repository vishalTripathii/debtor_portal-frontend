#!/usr/bin/env node
/**
 * Test OTP Email Sending
 * Tests the email Lambda function directly before deployment
 */

const nodemailer = require('nodemailer');

async function testOTPEmail() {
    console.log('🧪 Testing OTP Email Configuration');
    console.log('=' .repeat(60));
    console.log('National ID: 1100100051224');
    console.log('Testing GoDaddy SMTP with Port 587 (STARTTLS)');
    console.log('');

    // GoDaddy SMTP - Port 587 (same as in email_lambda.js)
    const transporter = nodemailer.createTransporter({
        host: 'smtpout.secureserver.net',
        port: 587,
        secure: false,  // false for port 587 (STARTTLS)
        auth: {
            user: 'hello@poweramc.co',
            pass: 'Strive*12345'
        },
        tls: {
            rejectUnauthorized: false,
            ciphers: 'SSLv3'
        },
        connectionTimeout: 15000,
        greetingTimeout: 10000,
        socketTimeout: 15000
    });

    try {
        // Step 1: Verify SMTP connection
        console.log('📡 Step 1: Verifying SMTP connection...');
        await transporter.verify();
        console.log('✅ SMTP connection verified successfully!');
        console.log('');

        // Step 2: Send test OTP email
        console.log('📧 Step 2: Sending test OTP email...');
        
        const testOTP = '';
        const testName = 'Test User (NID: 1100100051224)';
        const testEmail = 'hello@poweramc.co'; // Send to yourself for testing
        
        const mailOptions = {
            from: '"PowerAMC Customer Portal" <hello@poweramc.co>',
            to: testEmail,
            subject: '✅ TEST - Your OTP Code - PowerAMC Customer Portal',
            html: `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>OTP Verification</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                 color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                        .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                        .otp-code { font-size: 36px; font-weight: bold; color: #667eea; text-align: center; 
                                   letter-spacing: 8px; padding: 25px; 
                                   background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                                   border-radius: 10px; margin: 25px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                        .warning { color: #e74c3c; font-weight: bold; background-color: #fee; 
                                  padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0; }
                        .success { color: #27ae60; font-weight: bold; background-color: #e8f8f0; 
                                  padding: 15px; border-left: 4px solid #27ae60; margin: 20px 0; }
                        .footer { background-color: #34495e; color: white; padding: 20px; 
                                 text-align: center; font-size: 12px; margin-top: 20px; border-radius: 10px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>PowerAMC</h1>
                            <p>Customer Portal - OTP Verification TEST</p>
                        </div>
                        <div class="content">
                            <div class="success">
                                ✅ <strong>TEST EMAIL - Email System Working!</strong><br>
                                This is a test email to verify the email configuration before deployment.
                            </div>
                            
                            <h2>Dear ${testName},</h2>
                            <p>Thank you for using the PowerAMC Customer Portal. Please use the following One-Time Password (OTP) to complete your login:</p>
                            
                            <div class="otp-code">${testOTP}</div>
                            
                            <p><strong>⏰ This code will expire in 5 minutes.</strong></p>
                            
                            <div class="warning">
                                ⚠️ <strong>Security Notice:</strong> Do not share this code with anyone. 
                                PowerAMC will never ask for your OTP over phone or email.
                            </div>
                            
                            <p>If you did not request this code, please ignore this email.</p>
                            
                            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                            
                            <p><strong>Test Configuration:</strong></p>
                            <ul>
                                <li>SMTP Host: smtpout.secureserver.net</li>
                                <li>Port: 587 (STARTTLS)</li>
                                <li>From: hello@poweramc.co</li>
                                <li>National ID: 1100100051224</li>
                            </ul>
                            
                            <p><strong>PowerAMC Team</strong><br>
                            📧 Email: hello@poweramc.co</p>
                        </div>
                        <div class="footer">
                            <p>© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                            <p>This is an automated TEST message. Please do not reply.</p>
                        </div>
                    </div>
                </body>
                </html>
            `,
            text: `
TEST EMAIL - Email System Working!

Dear ${testName},

Your OTP code for PowerAMC Customer Portal login is: ${testOTP}

This code will expire in 5 minutes.

⚠️ Do not share this code with anyone.

If you did not request this code, please ignore this email.

Test Configuration:
- SMTP Host: smtpout.secureserver.net
- Port: 587 (STARTTLS)
- From: hello@poweramc.co
- National ID: 1100100051224

PowerAMC Team
hello@poweramc.co
            `
        };

        const info = await transporter.sendMail(mailOptions);
        
        console.log('✅ TEST EMAIL SENT SUCCESSFULLY!');
        console.log('');
        console.log('📋 Email Details:');
        console.log(`   Message ID: ${info.messageId}`);
        console.log(`   Response: ${info.response}`);
        console.log(`   To: ${testEmail}`);
        console.log(`   OTP: ${testOTP}`);
        console.log('');
        console.log('🎉 EMAIL SERVICE IS WORKING!');
        console.log('✅ Ready to deploy with working email configuration');
        console.log('');
        console.log('📧 Check your inbox at: hello@poweramc.co');
        console.log('');
        
        return {
            success: true,
            messageId: info.messageId,
            testEmail: testEmail,
            testOTP: testOTP
        };
        
    } catch (error) {
        console.error('');
        console.error('❌ EMAIL TEST FAILED!');
        console.error('');
        console.error('Error Details:');
        console.error(`   Code: ${error.code}`);
        console.error(`   Message: ${error.message}`);
        console.error('');
        console.error('🔧 Troubleshooting:');
        console.error('   1. Check if GoDaddy webmail login works');
        console.error('   2. Verify password is correct');
        console.error('   3. Check if SMTP is enabled in GoDaddy');
        console.error('   4. Try port 465 if 587 fails');
        console.error('');
        
        return {
            success: false,
            error: error.message,
            code: error.code
        };
    }
}

// Run the test
console.log('');
testOTPEmail()
    .then(result => {
        console.log('=' .repeat(60));
        if (result.success) {
            console.log('✅ TEST PASSED - READY TO DEPLOY');
            process.exit(0);
        } else {
            console.log('❌ TEST FAILED - FIX CONFIGURATION BEFORE DEPLOYING');
            process.exit(1);
        }
    })
    .catch(error => {
        console.error('💥 Test script error:', error);
        process.exit(1);
    });
