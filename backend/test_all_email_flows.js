const nodemailer = require('nodemailer');

async function testAllEmailFlows() {
    console.log('\n🔐 TESTING ALL EMAIL FLOWS - GODADDY WELLEAZY CONFIGURATION');
    console.log('=' .repeat(100));
    
    const EMAIL = 'digital.marketing@welleazy.in';
    const PASSWORD = 'Welcome@123';
    const TEST_DEBTOR_EMAIL = 'tilakagrawal7777@gmail.com';
    const ADMIN_EMAIL = 'hello@poweramc.com';
    
    console.log(`\n📧 Sender Email: ${EMAIL}`);
    console.log(`🔑 Password: ${PASSWORD}`);
    console.log(`📬 Test Debtor: ${TEST_DEBTOR_EMAIL}`);
    console.log(`📬 Admin Email: ${ADMIN_EMAIL}\n`);
    
    // Configure GoDaddy SMTP
    const transporter = nodemailer.createTransport({
        host: 'smtpout.secureserver.net',
        port: 587,
        secure: false,
        auth: {
            user: EMAIL,
            pass: PASSWORD
        },
        requireTLS: true,
        tls: { rejectUnauthorized: false },
        name: 'welleazy.in',
        connectionTimeout: 15000,
        greetingTimeout: 10000,
        socketTimeout: 15000
    });
    
    try {
        console.log('🔌 Testing SMTP Connection...');
        await transporter.verify();
        console.log('✅ SMTP Connection: SUCCESS\n');
    } catch (error) {
        console.log(`❌ SMTP Connection Failed: ${error.message}`);
        return;
    }
    
    const testOTP = Math.floor(100000 + Math.random() * 900000).toString();
    const testResults = [];
    
    // ============================================================
    // TEST 1: OTP Email (Welleazy -> Debtor)
    // ============================================================
    console.log('=' .repeat(100));
    console.log('TEST 1: OTP EMAIL FLOW');
    console.log('=' .repeat(100));
    console.log(`📤 From: ${EMAIL}`);
    console.log(`📥 To: ${TEST_DEBTOR_EMAIL}`);
    console.log(`🔢 OTP: ${testOTP}\n`);
    
    try {
        const otpEmail = {
            from: `"PowerAMC Customer Portal" <${EMAIL}>`,
            to: TEST_DEBTOR_EMAIL,
            subject: `✅ TEST - Your OTP Code: ${testOTP}`,
            html: `
                <!DOCTYPE html>
                <html>
                <head><meta charset="utf-8"><style>
                    body{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0}
                    .container{max-width:600px;margin:0 auto;padding:20px}
                    .header{background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:30px;text-align:center;border-radius:10px 10px 0 0}
                    .content{background:#f9f9f9;padding:30px;border-radius:0 0 10px 10px}
                    .otp-code{font-size:36px;font-weight:bold;color:#667eea;text-align:center;letter-spacing:8px;
                             padding:25px;background:linear-gradient(135deg,#f5f7fa,#c3cfe2);border-radius:10px;
                             margin:25px 0;box-shadow:0 4px 6px rgba(0,0,0,0.1);border:3px solid#667eea}
                    .warning{color:#e74c3c;font-weight:bold;background:#fee;padding:15px;border-left:4px solid#e74c3c;margin:20px 0;border-radius:5px}
                    .success-badge{background:#d4edda;border-left:4px solid#28a745;padding:15px;margin:20px 0;border-radius:5px}
                    .footer{background:#34495e;color:white;padding:20px;text-align:center;font-size:12px;margin-top:20px;border-radius:10px}
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="margin:0">PowerAMC</h1>
                            <p style="margin:10px 0 0 0">Customer Portal - OTP Verification</p>
                        </div>
                        <div class="content">
                            <div class="success-badge">
                                <strong>✅ Email Flow Test 1: OTP Email</strong><br>
                                Configuration: GoDaddy Welleazy (digital.marketing@welleazy.in)
                            </div>
                            <h2>Dear Valued Customer,</h2>
                            <p>Thank you for using the PowerAMC Customer Portal. Please use the following One-Time Password (OTP) to complete your login:</p>
                            <div class="otp-code">${testOTP}</div>
                            <p><strong>⏰ This code will expire in 5 minutes.</strong></p>
                            <div class="warning">
                                <strong>Security Notice:</strong> Do not share this code with anyone. 
                                PowerAMC will never ask for your OTP via phone or email.
                            </div>
                            <p>If you did not request this code, please ignore this email.</p>
                            <hr style="border:none;border-top:1px solid#ddd;margin:20px 0">
                            <p><strong>PowerAMC Collections Team</strong><br>
                            Email: ${EMAIL}<br>Website: www.poweramc.com</p>
                        </div>
                        <div class="footer">
                            <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                            <p style="margin:5px 0 0 0">This is an automated test message.</p>
                        </div>
                    </div>
                </body>
                </html>
            `
        };
        
        const info1 = await transporter.sendMail(otpEmail);
        console.log(`✅ OTP Email Sent Successfully!`);
        console.log(`   📧 Message ID: ${info1.messageId}`);
        console.log(`   📬 Check inbox: ${TEST_DEBTOR_EMAIL}\n`);
        testResults.push({ test: 'OTP Email', status: 'PASS', messageId: info1.messageId });
    } catch (error) {
        console.log(`❌ OTP Email Failed: ${error.message}\n`);
        testResults.push({ test: 'OTP Email', status: 'FAIL', error: error.message });
    }
    
    // ============================================================
    // TEST 2: Payment Notification (Welleazy -> hello@poweramc.com)
    // ============================================================
    console.log('=' .repeat(100));
    console.log('TEST 2: PAYMENT NOTIFICATION FLOW');
    console.log('=' .repeat(100));
    console.log(`📤 From: ${EMAIL}`);
    console.log(`📥 To: ${ADMIN_EMAIL}`);
    console.log(`💰 Transaction: TXN-TEST-${Date.now()}\n`);
    
    try {
        const transactionNumber = `TXN-TEST-${Date.now()}`;
        const paymentEmail = {
            from: `"PowerAMC Debtor Portal" <${EMAIL}>`,
            to: ADMIN_EMAIL,
            replyTo: TEST_DEBTOR_EMAIL,
            subject: `💰 TEST - Payment Submitted - Account TEST-12345`,
            html: `
                <!DOCTYPE html>
                <html>
                <head><meta charset="utf-8"><style>
                    body{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0}
                    .container{max-width:700px;margin:0 auto;padding:20px;background:#f5f5f5}
                    .header{background:linear-gradient(135deg,#27ae60,#2ecc71);color:white;padding:25px;text-align:center;border-radius:10px 10px 0 0}
                    .content{background:white;padding:30px;border-radius:0 0 10px 10px}
                    .section{margin:25px 0;padding:20px;background:#f8f9fa;border-left:4px solid#667eea;border-radius:5px}
                    .section h3{margin-top:0;color:#667eea;font-size:18px}
                    .info-row{padding:10px 0;border-bottom:1px solid#e9ecef}
                    .info-row:last-child{border-bottom:none}
                    .info-label{font-weight:bold;color:#495057;display:inline-block;width:200px}
                    .info-value{color:#212529}
                    .highlight{background:linear-gradient(135deg,#d4edda,#c3e6cb);border-left:4px solid#28a745;padding:20px;margin:25px 0;border-radius:5px}
                    .highlight .amount{font-size:28px;font-weight:bold;color:#28a745;margin:10px 0}
                    .footer{margin-top:25px;padding:20px;background:#34495e;color:white;text-align:center;border-radius:10px;font-size:12px}
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="margin:0">💰 Payment Submitted</h1>
                            <p style="margin:10px 0 0 0">Email Flow Test 2: Payment Notification</p>
                        </div>
                        <div class="content">
                            <p style="font-size:16px;margin-bottom:25px">
                                A debtor has submitted a payment through the customer portal. Please review the details below:
                            </p>
                            <div class="highlight">
                                <strong style="font-size:18px">💳 Payment Information:</strong>
                                <div class="amount">฿25,000.00</div>
                                <div><strong>Transaction #:</strong> ${transactionNumber}</div>
                                <div><strong>Payment Type:</strong> Full Payment (Test)</div>
                            </div>
                            <div class="section">
                                <h3>👤 Customer Details</h3>
                                <div class="info-row">
                                    <span class="info-label">Account Number:</span>
                                    <span class="info-value">TEST-12345</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Name:</span>
                                    <span class="info-value">Test Debtor</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Email:</span>
                                    <span class="info-value">${TEST_DEBTOR_EMAIL}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Phone:</span>
                                    <span class="info-value">+66 812345678</span>
                                </div>
                            </div>
                            <div class="section">
                                <h3>💼 Debt Information</h3>
                                <div class="info-row">
                                    <span class="info-label">Original Creditor:</span>
                                    <span class="info-value">Test Bank Ltd.</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Outstanding Balance:</span>
                                    <span class="info-value">฿50,000.00</span>
                                </div>
                            </div>
                            <p style="margin-top:30px;padding:15px;background:#e7f3ff;border-left:4px solid#0066cc;border-radius:5px">
                                <strong>⏰ Submitted:</strong> ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})} (Bangkok Time)
                            </p>
                        </div>
                        <div class="footer">
                            <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                            <p style="margin:10px 0 0 0">Automated test notification from Debtor Portal</p>
                        </div>
                    </div>
                </body>
                </html>
            `
        };
        
        const info2 = await transporter.sendMail(paymentEmail);
        console.log(`✅ Payment Notification Sent Successfully!`);
        console.log(`   📧 Message ID: ${info2.messageId}`);
        console.log(`   📬 Check inbox: ${ADMIN_EMAIL}\n`);
        testResults.push({ test: 'Payment Notification', status: 'PASS', messageId: info2.messageId });
    } catch (error) {
        console.log(`❌ Payment Notification Failed: ${error.message}\n`);
        testResults.push({ test: 'Payment Notification', status: 'FAIL', error: error.message });
    }
    
    // ============================================================
    // TEST 3: Support Request (Welleazy -> hello@poweramc.com)
    // ============================================================
    console.log('=' .repeat(100));
    console.log('TEST 3: SUPPORT REQUEST FLOW');
    console.log('=' .repeat(100));
    console.log(`📤 From: ${EMAIL}`);
    console.log(`📥 To: ${ADMIN_EMAIL}`);
    console.log(`🆘 Reason: Financial difficulty\n`);
    
    try {
        const supportEmail = {
            from: `"PowerAMC Debtor Portal" <${EMAIL}>`,
            to: ADMIN_EMAIL,
            replyTo: TEST_DEBTOR_EMAIL,
            subject: `🆘 TEST - Support Request - Account TEST-12345`,
            html: `
                <!DOCTYPE html>
                <html>
                <head><meta charset="utf-8"><style>
                    body{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0}
                    .container{max-width:700px;margin:0 auto;padding:20px;background:#f5f5f5}
                    .header{background:linear-gradient(135deg,#e74c3c,#c0392b);color:white;padding:25px;text-align:center;border-radius:10px 10px 0 0}
                    .content{background:white;padding:30px;border-radius:0 0 10px 10px}
                    .section{margin:25px 0;padding:20px;background:#f8f9fa;border-left:4px solid#667eea;border-radius:5px}
                    .section h3{margin-top:0;color:#667eea;font-size:18px}
                    .info-row{padding:10px 0;border-bottom:1px solid#e9ecef}
                    .info-row:last-child{border-bottom:none}
                    .info-label{font-weight:bold;color:#495057;display:inline-block;width:200px}
                    .info-value{color:#212529}
                    .highlight{background:linear-gradient(135deg,#fff3cd,#ffeaa7);border-left:4px solid#ffc107;padding:20px;margin:25px 0;border-radius:5px}
                    .notes-box{background:#e7f3ff;padding:15px;margin:15px 0;border-radius:5px;border-left:4px solid#0066cc}
                    .footer{margin-top:25px;padding:20px;background:#34495e;color:white;text-align:center;border-radius:10px;font-size:12px}
                </style></head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1 style="margin:0">🆘 Support Request</h1>
                            <p style="margin:10px 0 0 0">Email Flow Test 3: Customer Needs Assistance</p>
                        </div>
                        <div class="content">
                            <p style="font-size:16px;margin-bottom:25px">
                                A debtor has submitted a support request through the customer portal. 
                                They need assistance with their payment. Please review and follow up:
                            </p>
                            <div class="highlight">
                                <strong style="font-size:18px">📋 Reason:</strong>
                                <div style="font-size:20px;margin:15px 0;font-weight:bold;color:#d63031">
                                    Financial difficulty - Need payment plan
                                </div>
                                <div><strong>Requested Plan:</strong> 3-month installment plan</div>
                            </div>
                            <div class="notes-box">
                                <strong>📝 Additional Notes:</strong>
                                <p style="margin:10px 0 0 0">
                                    I lost my job last month and need time to arrange payment. 
                                    Would appreciate if we can discuss an installment plan.
                                </p>
                            </div>
                            <div class="section">
                                <h3>📞 Contact Preferences</h3>
                                <div class="info-row">
                                    <span class="info-label">Preferred Date:</span>
                                    <span class="info-value">${new Date(Date.now() + 86400000).toISOString().split('T')[0]}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Preferred Time:</span>
                                    <span class="info-value">Morning (9AM - 12PM)</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Contact Method:</span>
                                    <span class="info-value">Phone: +66 812345678</span>
                                </div>
                            </div>
                            <div class="section">
                                <h3>👤 Customer Details</h3>
                                <div class="info-row">
                                    <span class="info-label">Account Number:</span>
                                    <span class="info-value">TEST-12345</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Name:</span>
                                    <span class="info-value">Test Debtor</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Email:</span>
                                    <span class="info-value">${TEST_DEBTOR_EMAIL}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Phone:</span>
                                    <span class="info-value">+66 812345678</span>
                                </div>
                            </div>
                            <div class="section">
                                <h3>💼 Debt Information</h3>
                                <div class="info-row">
                                    <span class="info-label">Original Creditor:</span>
                                    <span class="info-value">Test Bank Ltd.</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Outstanding Balance:</span>
                                    <span class="info-value">฿50,000.00</span>
                                </div>
                            </div>
                            <p style="margin-top:30px;padding:15px;background:#fee;border-left:4px solid#e74c3c;border-radius:5px">
                                <strong>⚠️ Action Required:</strong> Please follow up with this customer as soon as possible.
                            </p>
                            <p style="margin-top:15px;padding:15px;background:#e7f3ff;border-left:4px solid#0066cc;border-radius:5px">
                                <strong>⏰ Submitted:</strong> ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})} (Bangkok Time)
                            </p>
                        </div>
                        <div class="footer">
                            <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                            <p style="margin:10px 0 0 0">Automated test notification from Debtor Portal</p>
                        </div>
                    </div>
                </body>
                </html>
            `
        };
        
        const info3 = await transporter.sendMail(supportEmail);
        console.log(`✅ Support Request Sent Successfully!`);
        console.log(`   📧 Message ID: ${info3.messageId}`);
        console.log(`   📬 Check inbox: ${ADMIN_EMAIL}\n`);
        testResults.push({ test: 'Support Request', status: 'PASS', messageId: info3.messageId });
    } catch (error) {
        console.log(`❌ Support Request Failed: ${error.message}\n`);
        testResults.push({ test: 'Support Request', status: 'FAIL', error: error.message });
    }
    
    // ============================================================
    // FINAL SUMMARY
    // ============================================================
    console.log('=' .repeat(100));
    console.log('FINAL TEST SUMMARY');
    console.log('=' .repeat(100));
    
    const passCount = testResults.filter(r => r.status === 'PASS').length;
    const failCount = testResults.filter(r => r.status === 'FAIL').length;
    
    console.log(`\n📊 Results: ${passCount} PASSED / ${failCount} FAILED / ${testResults.length} TOTAL\n`);
    
    testResults.forEach((result, index) => {
        const icon = result.status === 'PASS' ? '✅' : '❌';
        console.log(`${icon} Test ${index + 1}: ${result.test} - ${result.status}`);
        if (result.messageId) {
            console.log(`   Message ID: ${result.messageId}`);
        }
        if (result.error) {
            console.log(`   Error: ${result.error}`);
        }
    });
    
    console.log('\n' + '=' .repeat(100));
    
    if (passCount === testResults.length) {
        console.log('\n🎉🎉🎉 ALL TESTS PASSED! EMAIL CONFIGURATION IS WORKING PERFECTLY! 🎉🎉🎉\n');
        console.log('📋 PRODUCTION CONFIGURATION:');
        console.log('=' .repeat(100));
        console.log(`Email: ${EMAIL}`);
        console.log(`Password: ${PASSWORD}`);
        console.log(`SMTP: smtpout.secureserver.net:587`);
        console.log(`Security: STARTTLS`);
        console.log('=' .repeat(100));
        console.log('\n📧 EMAIL FLOWS:');
        console.log(`   1️⃣  OTP Emails: ${EMAIL} → Debtor Email`);
        console.log(`   2️⃣  Payment Notifications: ${EMAIL} → ${ADMIN_EMAIL}`);
        console.log(`   3️⃣  Support Requests: ${EMAIL} → ${ADMIN_EMAIL}`);
        console.log('\n📬 CHECK INBOXES:');
        console.log(`   🔹 ${TEST_DEBTOR_EMAIL} - Should have OTP email`);
        console.log(`   🔹 ${ADMIN_EMAIL} - Should have 2 notifications (payment + support)`);
        console.log('\n🚀 READY FOR LAMBDA DEPLOYMENT!\n');
    } else {
        console.log('\n⚠️  SOME TESTS FAILED - PLEASE REVIEW ERRORS ABOVE\n');
    }
    
    transporter.close();
}

console.log('Starting comprehensive email flow tests...\n');
testAllEmailFlows().catch(console.error);
