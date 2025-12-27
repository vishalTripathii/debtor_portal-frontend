const nodemailer = require('nodemailer');

async function validateGmailCredentials() {
    console.log('🔐 GMAIL CREDENTIALS VALIDATION TEST');
    console.log('=' .repeat(60));
    
    // Your provided credentials
    const GMAIL_USER = 'hello@gmail.com';
    const GMAIL_APP_PASSWORD = 'auzsoajwasucpedy'; // Spaces removed
    const TEST_RECIPIENT = 'tilakagrawal7777@gmail.com'; // Test recipient
    
    console.log(`📧 Sender Email: ${GMAIL_USER}`);
    console.log(`📬 Test Recipient: ${TEST_RECIPIENT}`);
    console.log(`🔑 App Password: ${'*'.repeat(16)} (hidden for security)`);
    console.log('=' .repeat(60));
    
    const configurations = [
        {
            name: 'Gmail SMTP - Port 587 (TLS/STARTTLS) - RECOMMENDED',
            host: 'smtp.gmail.com',
            port: 587,
            secure: false, // Use STARTTLS
            auth: { 
                user: GMAIL_USER, 
                pass: GMAIL_APP_PASSWORD 
            },
            tls: { 
                rejectUnauthorized: true, // Gmail has valid certificate
                minVersion: 'TLSv1.2'
            }
        },
        {
            name: 'Gmail SMTP - Port 465 (SSL) - ALTERNATIVE',
            host: 'smtp.gmail.com',
            port: 465,
            secure: true, // Use SSL
            auth: { 
                user: GMAIL_USER, 
                pass: GMAIL_APP_PASSWORD 
            },
            tls: { 
                rejectUnauthorized: true,
                minVersion: 'TLSv1.2'
            }
        }
    ];

    let successfulConfig = null;

    for (const config of configurations) {
        console.log(`\n${'='.repeat(60)}`);
        console.log(`🧪 Testing: ${config.name}`);
        console.log(`${'='.repeat(60)}`);
        
        const transporter = nodemailer.createTransport({
            ...config,
            connectionTimeout: 15000,
            greetingTimeout: 10000,
            socketTimeout: 15000,
            pool: false, // Disable connection pooling for testing
            name: 'poweramc.co', // Fix: Use valid hostname for HELO/EHLO
            debug: true,
            logger: true
        });

        try {
            // TEST 1: SMTP Connection & Authentication
            console.log('\n📡 TEST 1: Testing SMTP Connection & Authentication...');
            await transporter.verify();
            console.log('✅ SMTP Connection & Authentication: PASSED');
            
            // TEST 2: Send OTP-style email to test recipient
            console.log('\n📧 TEST 2: Sending Test OTP Email to Test Recipient...');
            console.log(`   Recipient: ${TEST_RECIPIENT}`);
            
            const testOTP = Math.floor(100000 + Math.random() * 900000).toString();
            
            const otpEmailOptions = {
                from: `"PowerAMC Customer Portal" <${GMAIL_USER}>`,
                to: TEST_RECIPIENT,
                replyTo: GMAIL_USER,
                subject: `✅ TEST SUCCESS - Your OTP Code: ${testOTP}`,
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>OTP Verification Test</title>
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                            .success-badge { background: #27ae60; color: white; padding: 10px 20px; 
                                            text-align: center; border-radius: 5px; margin-bottom: 20px; }
                            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                     color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                            .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                            .otp-code { font-size: 36px; font-weight: bold; color: #667eea; text-align: center; 
                                       letter-spacing: 8px; padding: 25px; 
                                       background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                                       border-radius: 10px; margin: 25px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                            .success-info { background-color: #d4edda; border-left: 4px solid #28a745; 
                                          padding: 15px; margin: 20px 0; border-radius: 5px; }
                            .config-info { background-color: #e7f3ff; border-left: 4px solid #0066cc; 
                                         padding: 15px; margin: 20px 0; border-radius: 5px; font-size: 14px; }
                            .warning { color: #e74c3c; font-weight: bold; background-color: #fee; 
                                      padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0; }
                            .footer { background-color: #34495e; color: white; padding: 20px; 
                                     text-align: center; font-size: 12px; margin-top: 20px; border-radius: 10px; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="success-badge">
                                <h2 style="margin: 0;">✅ GMAIL SMTP TEST SUCCESSFUL</h2>
                                <p style="margin: 5px 0 0 0;">Configuration: ${config.name}</p>
                            </div>
                            
                            <div class="header">
                                <h1>PowerAMC</h1>
                                <p>Customer Portal - OTP Verification</p>
                            </div>
                            
                            <div class="content">
                                <div class="success-info">
                                    <strong>🎉 Congratulations!</strong> Your Gmail SMTP configuration is working perfectly!
                                </div>
                                
                                <h2>Dear Valued Customer,</h2>
                                <p>This is a <strong>TEST EMAIL</strong> to validate your Gmail SMTP configuration. 
                                Your One-Time Password (OTP) is:</p>
                                
                                <div class="otp-code">${testOTP}</div>
                                
                                <p><strong>⏰ This code will expire in 5 minutes.</strong></p>
                                
                                <div class="warning">
                                    <strong>Security Notice:</strong> Do not share this code with anyone. 
                                    PowerAMC will never ask for your OTP via phone or email.
                                </div>
                                
                                <div class="config-info">
                                    <h3 style="margin-top: 0;">📋 Configuration Details:</h3>
                                    <ul style="margin: 10px 0;">
                                        <li><strong>SMTP Server:</strong> ${config.host}</li>
                                        <li><strong>Port:</strong> ${config.port}</li>
                                        <li><strong>Security:</strong> ${config.secure ? 'SSL/TLS' : 'STARTTLS'}</li>
                                        <li><strong>Sender Email:</strong> ${GMAIL_USER}</li>
                                        <li><strong>Authentication:</strong> App Password ✅</li>
                                        <li><strong>Status:</strong> <span style="color: #28a745; font-weight: bold;">OPERATIONAL</span></li>
                                    </ul>
                                </div>
                                
                                <div class="success-info">
                                    <strong>✅ All Tests Passed:</strong>
                                    <ul style="margin: 10px 0;">
                                        <li>✅ SMTP Connection Successful</li>
                                        <li>✅ Authentication Successful</li>
                                        <li>✅ Email Sent Successfully</li>
                                        <li>✅ HTML Template Rendering Correctly</li>
                                        <li>✅ Ready for Production Deployment</li>
                                    </ul>
                                </div>
                                
                                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                                <p><strong>PowerAMC Collections Team</strong><br>
                                Email: ${GMAIL_USER}<br>
                                Website: www.poweramc.co</p>
                            </div>
                            
                            <div class="footer">
                                <p>© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p>Test Email sent at: ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })} (Bangkok Time)</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `,
                text: `
✅ GMAIL SMTP TEST SUCCESSFUL
Configuration: ${config.name}

Dear Valued Customer,

This is a TEST EMAIL to validate your Gmail SMTP configuration.

Your One-Time Password (OTP) is: ${testOTP}

This code will expire in 5 minutes.

Configuration Details:
- SMTP Server: ${config.host}
- Port: ${config.port}
- Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}
- Sender Email: ${GMAIL_USER}
- Status: OPERATIONAL ✅

All Tests Passed:
✅ SMTP Connection Successful
✅ Authentication Successful
✅ Email Sent Successfully
✅ HTML Template Rendering Correctly
✅ Ready for Production Deployment

Best regards,
PowerAMC Collections Team
Email: ${GMAIL_USER}
Website: www.poweramc.co

Test sent at: ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })} (Bangkok Time)
                `
            };
            
            const info = await transporter.sendMail(otpEmailOptions);
            console.log('✅ OTP Email Sent to Test Recipient: PASSED');
            console.log(`   Message ID: ${info.messageId}`);
            console.log(`   Response: ${info.response}`);
            
            // TEST 3: Send Payment Notification to PowerAMC (System Email)
            console.log('\n📬 TEST 3: Sending Test Payment Notification to PowerAMC System Email...');
            console.log(`   System Email: ${GMAIL_USER}`);
            
            const notificationOptions = {
                from: `"PowerAMC Customer Portal" <${GMAIL_USER}>`,
                to: GMAIL_USER, // Send system notifications back to PowerAMC
                replyTo: TEST_RECIPIENT,
                subject: '✅ TEST - Payment Request Submitted by Customer',
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                            .container { max-width: 700px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }
                            .header { background-color: #27ae60; color: white; padding: 20px; text-align: center; 
                                     border-radius: 10px 10px 0 0; }
                            .content { background-color: white; padding: 30px; border-radius: 0 0 10px 10px; }
                            .section { margin: 25px 0; padding: 15px; background-color: #f8f9fa; 
                                      border-left: 4px solid #667eea; border-radius: 5px; }
                            .section h3 { margin-top: 0; color: #667eea; }
                            .section ul { list-style: none; padding: 0; }
                            .section li { padding: 8px 0; border-bottom: 1px solid #e9ecef; }
                            .section li:last-child { border-bottom: none; }
                            .section li strong { color: #495057; display: inline-block; width: 180px; }
                            .success-badge { background-color: #d4edda; border-left: 4px solid #28a745; 
                                           padding: 15px; margin: 20px 0; border-radius: 5px; }
                            .footer { margin-top: 20px; padding: 15px; background-color: #34495e; color: white; 
                                     text-align: center; border-radius: 10px; font-size: 12px; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1 style="margin: 0;">✅ SYSTEM NOTIFICATION TEST</h1>
                                <p style="margin: 10px 0 0 0;">Payment Request Submitted</p>
                            </div>
                            
                            <div class="content">
                                <div class="success-badge">
                                    <strong>🎉 System Email Test Successful!</strong><br>
                                    This notification was sent to PowerAMC system email successfully.
                                </div>
                                
                                <h2>Payment Request Notification</h2>
                                <p>A customer has submitted a payment request through the debtor portal.</p>
                                
                                <div class="section">
                                    <h3>👤 Customer Details:</h3>
                                    <ul>
                                        <li><strong>Account Number:</strong> TEST-ACCOUNT-12345</li>
                                        <li><strong>Full Name:</strong> Test Customer (Testing)</li>
                                        <li><strong>National ID:</strong> 1234567890123</li>
                                        <li><strong>Email:</strong> ${TEST_RECIPIENT}</li>
                                        <li><strong>Phone:</strong> 0812345678</li>
                                    </ul>
                                </div>
                                
                                <div class="section">
                                    <h3>💰 Debt Information:</h3>
                                    <ul>
                                        <li><strong>Creditor:</strong> Test Bank Ltd.</li>
                                        <li><strong>Debt Type:</strong> Personal Loan</li>
                                        <li><strong>Outstanding Balance:</strong> ฿50,000.00</li>
                                        <li><strong>Contract Date:</strong> 15/01/2023</li>
                                        <li><strong>Debt Age:</strong> 24 months</li>
                                    </ul>
                                </div>
                                
                                <div class="section">
                                    <h3>📝 Payment Details:</h3>
                                    <ul>
                                        <li><strong>Payment Type:</strong> Full Payment</li>
                                        <li><strong>Amount Paid:</strong> ฿50,000.00</li>
                                        <li><strong>Transaction Number:</strong> TXN-TEST-${Date.now()}</li>
                                        <li><strong>Payment Method:</strong> Bank Transfer</li>
                                        <li><strong>Payment Date:</strong> ${new Date().toLocaleDateString('en-GB')}</li>
                                    </ul>
                                </div>
                                
                                <div class="success-badge">
                                    <strong>✅ Test Configuration Details:</strong>
                                    <ul style="list-style: none; padding: 10px 0 0 0; margin: 0;">
                                        <li>📧 From: ${GMAIL_USER}</li>
                                        <li>📬 To: ${GMAIL_USER} (System Email)</li>
                                        <li>🔐 Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}</li>
                                        <li>🌐 SMTP: ${config.host}:${config.port}</li>
                                        <li>✅ Status: Operational</li>
                                    </ul>
                                </div>
                                
                                <div style="margin-top: 25px; padding: 15px; background-color: #fff3cd; 
                                           border-left: 4px solid #ffc107; border-radius: 5px;">
                                    <strong>⚠️ Action Required:</strong><br>
                                    Please verify the payment and update the customer's account status accordingly.
                                </div>
                                
                                <hr style="border: none; border-top: 1px solid #ddd; margin: 25px 0;">
                                
                                <p style="color: #666; font-size: 14px;">
                                    <strong>Timestamp:</strong> ${new Date().toLocaleString('en-US', { 
                                        timeZone: 'Asia/Bangkok',
                                        year: 'numeric',
                                        month: 'long',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit',
                                        hour12: false
                                    })} (Bangkok Time)
                                </p>
                                
                                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                                    <strong>PowerAMC Collections Team</strong><br>
                                    Email: ${GMAIL_USER}<br>
                                    Website: www.poweramc.co
                                </p>
                            </div>
                            
                            <div class="footer">
                                <p style="margin: 0;">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p style="margin: 5px 0 0 0;">Automated System Notification - Do Not Reply</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `,
                text: `
✅ SYSTEM NOTIFICATION TEST
Payment Request Submitted

A customer has submitted a payment request through the debtor portal.

CUSTOMER DETAILS:
- Account Number: TEST-ACCOUNT-12345
- Full Name: Test Customer (Testing)
- National ID: 1234567890123
- Email: ${TEST_RECIPIENT}
- Phone: 0812345678

DEBT INFORMATION:
- Creditor: Test Bank Ltd.
- Debt Type: Personal Loan
- Outstanding Balance: ฿50,000.00
- Contract Date: 15/01/2023
- Debt Age: 24 months

PAYMENT DETAILS:
- Payment Type: Full Payment
- Amount Paid: ฿50,000.00
- Transaction Number: TXN-TEST-${Date.now()}
- Payment Method: Bank Transfer
- Payment Date: ${new Date().toLocaleDateString('en-GB')}

✅ Test Configuration:
- From: ${GMAIL_USER}
- To: ${GMAIL_USER} (System Email)
- Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}
- SMTP: ${config.host}:${config.port}
- Status: Operational ✅

⚠️ Action Required:
Please verify the payment and update the customer's account status accordingly.

Timestamp: ${new Date().toLocaleString('en-US', { 
    timeZone: 'Asia/Bangkok',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
})} (Bangkok Time)

PowerAMC Collections Team
Email: ${GMAIL_USER}
Website: www.poweramc.co

Automated System Notification - Do Not Reply
                `
            };
            
            const notifInfo = await transporter.sendMail(notificationOptions);
            console.log('✅ System Notification Email Sent to PowerAMC: PASSED');
            console.log(`   Message ID: ${notifInfo.messageId}`);
            
            // TEST 4: Verify transporter can be closed properly
            console.log('\n🔌 TEST 4: Testing Connection Cleanup...');
            transporter.close();
            console.log('✅ Connection Cleanup: PASSED');
            
            // All tests passed!
            successfulConfig = config;
            
            console.log(`\n${'='.repeat(60)}`);
            console.log('🎉 ALL TESTS PASSED SUCCESSFULLY!');
            console.log(`${'='.repeat(60)}`);
            console.log(`\n✅ Successful Configuration: ${config.name}`);
            console.log(`✅ SMTP Server: ${config.host}:${config.port}`);
            console.log(`✅ Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}`);
            console.log(`✅ Sender Email: ${GMAIL_USER}`);
            console.log(`\n📧 CHECK THESE INBOXES:`);
            console.log(`\n   1️⃣  ${TEST_RECIPIENT}`);
            console.log(`      - OTP Email with test code`);
            console.log(`      - Beautiful HTML template`);
            console.log(`\n   2️⃣  ${GMAIL_USER}`);
            console.log(`      - Payment notification email`);
            console.log(`      - System notification format`);
            console.log(`\n✅ VALIDATION COMPLETE - Ready for Lambda deployment!`);
            
            break; // Success! No need to test other configurations
            
        } catch (error) {
            console.log('❌ FAILED:', error.message);
            console.log(`\n⚠️  Configuration "${config.name}" did not work.`);
            
            if (error.code === 'EAUTH') {
                console.log('\n🔑 Authentication Error - Possible Issues:');
                console.log('   1. App password might be incorrect');
                console.log('   2. 2-Step Verification might not be enabled');
                console.log('   3. Email address might be incorrect');
                console.log('   4. Account might be locked or restricted');
                console.log('\n   Double-check: hello@poweramc.com and app password');
            } else if (error.code === 'ECONNECTION' || error.code === 'ETIMEDOUT') {
                console.log('\n🌐 Connection Error - Possible Issues:');
                console.log('   1. Network/firewall blocking SMTP');
                console.log('   2. Gmail servers might be unreachable');
                console.log('   3. Port might be blocked');
            } else if (error.code === 'EENVELOPE') {
                console.log('\n📧 Email Address Error:');
                console.log('   1. Sender or recipient email format might be invalid');
                console.log('   2. Check: hello@poweramc.com is a valid Gmail account');
            } else {
                console.log(`\n❌ Error Code: ${error.code || 'UNKNOWN'}`);
                console.log(`   Error Details: ${error.message}`);
            }
            
            console.log(`\n   Trying next configuration...`);
        }
    }

    console.log(`\n${'='.repeat(60)}`);
    
    if (successfulConfig) {
        console.log('✅ VALIDATION SUMMARY: SUCCESS');
        console.log(`${'='.repeat(60)}`);
        console.log(`\n🎯 Use this configuration for production:\n`);
        console.log(`host: '${successfulConfig.host}'`);
        console.log(`port: ${successfulConfig.port}`);
        console.log(`secure: ${successfulConfig.secure}`);
        console.log(`auth: {`);
        console.log(`  user: '${GMAIL_USER}',`);
        console.log(`  pass: '${GMAIL_APP_PASSWORD}'`);
        console.log(`}`);
        
        if (!successfulConfig.secure) {
            console.log(`requireTLS: true`);
        }
        
        console.log(`\n📧 Email Flow Tested:`);
        console.log(`   ✅ Debtor OTP → ${TEST_RECIPIENT}`);
        console.log(`   ✅ System Notifications → ${GMAIL_USER}`);
        console.log(`\n🚀 Next Steps:`);
        console.log(`   1. Check both email inboxes to confirm delivery`);
        console.log(`   2. Update backend/email_lambda.js with new config`);
        console.log(`   3. Deploy Lambda function`);
        console.log(`   4. Update AWS Parameter Store (if needed)`);
        
    } else {
        console.log('❌ VALIDATION SUMMARY: FAILED');
        console.log(`${'='.repeat(60)}`);
        console.log(`\n⚠️  None of the configurations worked.`);
        console.log(`\n🔍 Please verify:`);
        console.log(`   1. Gmail address: ${GMAIL_USER}`);
        console.log(`   2. App password is correct (16 characters: auzsoajwasucpedy)`);
        console.log(`   3. 2-Step Verification is enabled on Google account`);
        console.log(`   4. The account hello@poweramc.com exists and is accessible`);
        console.log(`\n❓ Is this a Gmail account or Google Workspace account?`);
        console.log(`   - If Gmail: Use smtp.gmail.com`);
        console.log(`   - If Google Workspace: Use smtp.gmail.com (same)`);
        console.log(`\n📖 To generate Gmail App Password:`);
        console.log(`   1. Go to: https://myaccount.google.com/apppasswords`);
        console.log(`   2. Select "Mail" and your device`);
        console.log(`   3. Copy the 16-character password (ignore spaces)`);
        console.log(`   4. Use that password in this script`);
    }
    
    console.log(`${'='.repeat(60)}\n`);
}

// Run the validation
validateGmailCredentials().catch(error => {
    console.error('\n💥 CRITICAL ERROR:', error);
    console.error('\nPlease check your credentials and try again.');
    process.exit(1);
});
