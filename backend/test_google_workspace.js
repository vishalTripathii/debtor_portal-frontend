const nodemailer = require('nodemailer');

async function testGoogleWorkspace() {
    console.log('🔐 GOOGLE WORKSPACE EMAIL VALIDATION');
    console.log('=' .repeat(80));
    console.log('Testing Google Workspace for poweramc.com domain (Thailand)\n');
    
    const EMAIL = 'hello@poweramc.com';
    const APP_PASSWORD = 'auzsoajwasucpedy'; // Google App Password
    const TEST_RECIPIENT = 'tilakagrawal7777@gmail.com';
    const SYSTEM_EMAIL = 'hello@poweramc.com'; // For system notifications
    
    console.log(`📧 Email: ${EMAIL}`);
    console.log(`🔑 App Password: ${'*'.repeat(16)}`);
    console.log(`📬 Test Recipient: ${TEST_RECIPIENT}`);
    console.log(`📬 System Notifications: ${SYSTEM_EMAIL}\n`);
    
    // Google Workspace SMTP configurations
    const configs = [
        {
            name: 'Google Workspace - Port 587 (STARTTLS) - RECOMMENDED',
            host: 'smtp.gmail.com',
            port: 587,
            secure: false,
            auth: {
                user: EMAIL,
                pass: APP_PASSWORD
            },
            tls: {
                rejectUnauthorized: true,
                minVersion: 'TLSv1.2'
            }
        },
        {
            name: 'Google Workspace - Port 465 (SSL)',
            host: 'smtp.gmail.com',
            port: 465,
            secure: true,
            auth: {
                user: EMAIL,
                pass: APP_PASSWORD
            },
            tls: {
                rejectUnauthorized: true,
                minVersion: 'TLSv1.2'
            }
        },
        {
            name: 'Google Workspace - Port 25 (TLS)',
            host: 'smtp.gmail.com',
            port: 25,
            secure: false,
            auth: {
                user: EMAIL,
                pass: APP_PASSWORD
            },
            tls: {
                rejectUnauthorized: true,
                minVersion: 'TLSv1.2'
            }
        },
        {
            name: 'Google Workspace - Port 587 (Relaxed TLS)',
            host: 'smtp.gmail.com',
            port: 587,
            secure: false,
            auth: {
                user: EMAIL,
                pass: APP_PASSWORD
            },
            tls: {
                rejectUnauthorized: false
            }
        }
    ];
    
    let successCount = 0;
    
    for (const config of configs) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`🧪 Testing: ${config.name}`);
        console.log(`   🌐 Server: ${config.host}:${config.port}`);
        
        const transporter = nodemailer.createTransport({
            host: config.host,
            port: config.port,
            secure: config.secure,
            auth: config.auth,
            tls: config.tls,
            connectionTimeout: 15000,
            greetingTimeout: 10000,
            socketTimeout: 15000,
            name: 'poweramc.com',
            pool: false,
            debug: true,
            logger: true
        });
        
        try {
            // TEST 1: Connection & Authentication
            console.log('\n   📡 Step 1: Testing SMTP Connection & Authentication...');
            await transporter.verify();
            console.log('   ✅ Connection & Authentication: SUCCESS!\n');
            
            // TEST 2: Send OTP Email to Test Recipient
            console.log('   📧 Step 2: Sending OTP Email to Test Recipient...');
            const testOTP = Math.floor(100000 + Math.random() * 900000).toString();
            
            const otpEmail = {
                from: `"PowerAMC Customer Portal" <${EMAIL}>`,
                to: TEST_RECIPIENT,
                replyTo: EMAIL,
                subject: `✅ SUCCESS - Your OTP Code: ${testOTP}`,
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head><meta charset="utf-8"><style>
                        body{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0}
                        .container{max-width:600px;margin:0 auto;padding:20px}
                        .success{background:linear-gradient(135deg,#27ae60,#2ecc71);color:white;padding:30px;text-align:center;border-radius:10px 10px 0 0}
                        .content{background:#f9f9f9;padding:30px;border-radius:0 0 10px 10px}
                        .otp{font-size:36px;font-weight:bold;color:#667eea;text-align:center;letter-spacing:8px;
                             padding:25px;background:linear-gradient(135deg,#f5f7fa,#c3cfe2);border-radius:10px;
                             margin:25px 0;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
                        .config{background:#e7f3ff;border-left:4px solid#0066cc;padding:15px;margin:20px 0;border-radius:5px;font-size:14px}
                        .warning{color:#e74c3c;font-weight:bold;background:#fee;padding:15px;border-left:4px solid#e74c3c;margin:20px 0;border-radius:5px}
                        .footer{background:#34495e;color:white;padding:20px;text-align:center;font-size:12px;margin-top:20px;border-radius:10px}
                    </style></head>
                    <body>
                        <div class="container">
                            <div class="success">
                                <h1 style="margin:0">✅ GOOGLE WORKSPACE EMAIL WORKING!</h1>
                                <p style="margin:10px 0 0 0">${config.name}</p>
                            </div>
                            <div class="content">
                                <h2>🎉 Dear Valued Customer,</h2>
                                <p>Great news! Your Google Workspace email configuration is working perfectly. 
                                   Your One-Time Password (OTP) is:</p>
                                <div class="otp">${testOTP}</div>
                                <p><strong>⏰ This code will expire in 5 minutes.</strong></p>
                                <div class="warning">
                                    <strong>Security Notice:</strong> Do not share this code with anyone.
                                    PowerAMC will never ask for your OTP via phone or email.
                                </div>
                                <div class="config">
                                    <h3 style="margin-top:0">📋 Working Configuration:</h3>
                                    <ul style="margin:10px 0;padding-left:20px">
                                        <li><strong>Provider:</strong> Google Workspace</li>
                                        <li><strong>Email:</strong> ${EMAIL}</li>
                                        <li><strong>SMTP Server:</strong> ${config.host}</li>
                                        <li><strong>Port:</strong> ${config.port}</li>
                                        <li><strong>Security:</strong> ${config.secure ? 'SSL/TLS' : 'STARTTLS'}</li>
                                        <li><strong>Region:</strong> Thailand</li>
                                        <li><strong>Status:</strong> <span style="color:#27ae60;font-weight:bold">OPERATIONAL ✅</span></li>
                                        <li><strong>Timestamp:</strong> ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})} (Bangkok Time)</li>
                                    </ul>
                                </div>
                                <hr style="border:none;border-top:1px solid#ddd;margin:20px 0">
                                <p><strong>PowerAMC Collections Team</strong><br>
                                Email: ${EMAIL}<br>
                                Website: www.poweramc.com</p>
                            </div>
                            <div class="footer">
                                <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p style="margin:5px 0 0 0">Test Email - Google Workspace Configuration</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `,
                text: `
✅ GOOGLE WORKSPACE EMAIL WORKING!
${config.name}

Dear Valued Customer,

Your One-Time Password (OTP) is: ${testOTP}

This code will expire in 5 minutes.

Working Configuration:
- Provider: Google Workspace
- Email: ${EMAIL}
- SMTP Server: ${config.host}
- Port: ${config.port}
- Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}
- Region: Thailand
- Status: OPERATIONAL ✅
- Timestamp: ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})} (Bangkok Time)

Security Notice: Do not share this code with anyone.

PowerAMC Collections Team
Email: ${EMAIL}
Website: www.poweramc.com
                `
            };
            
            const info1 = await transporter.sendMail(otpEmail);
            console.log(`   ✅ OTP Email Sent Successfully!`);
            console.log(`   📨 Message ID: ${info1.messageId}\n`);
            
            // TEST 3: Send System Notification Email
            console.log('   📬 Step 3: Sending System Notification to PowerAMC...');
            
            const notificationEmail = {
                from: `"PowerAMC Portal System" <${EMAIL}>`,
                to: SYSTEM_EMAIL,
                replyTo: TEST_RECIPIENT,
                subject: '✅ TEST - Payment Request Submitted by Customer',
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head><meta charset="utf-8"><style>
                        body{font-family:Arial,sans-serif;line-height:1.6;color:#333;margin:0;padding:0}
                        .container{max-width:700px;margin:0 auto;padding:20px;background:#f5f5f5}
                        .header{background:#27ae60;color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0}
                        .content{background:white;padding:30px;border-radius:0 0 10px 10px}
                        .section{margin:25px 0;padding:15px;background:#f8f9fa;border-left:4px solid#667eea;border-radius:5px}
                        .section h3{margin-top:0;color:#667eea}
                        .section ul{list-style:none;padding:0;margin:10px 0}
                        .section li{padding:8px 0;border-bottom:1px solid#e9ecef}
                        .section li:last-child{border-bottom:none}
                        .section li strong{color:#495057;display:inline-block;width:180px}
                        .success-badge{background:#d4edda;border-left:4px solid#28a745;padding:15px;margin:20px 0;border-radius:5px}
                        .footer{margin-top:20px;padding:15px;background:#34495e;color:white;text-align:center;border-radius:10px;font-size:12px}
                    </style></head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1 style="margin:0">✅ SYSTEM EMAIL TEST SUCCESSFUL</h1>
                                <p style="margin:10px 0 0 0">Payment Request Notification</p>
                            </div>
                            <div class="content">
                                <div class="success-badge">
                                    <strong>🎉 System Notification Email Working!</strong><br>
                                    Configuration: ${config.name}
                                </div>
                                <h2>Payment Request Submitted</h2>
                                <p>A customer has submitted a payment request through the debtor portal.</p>
                                <div class="section">
                                    <h3>👤 Customer Details:</h3>
                                    <ul>
                                        <li><strong>Account Number:</strong> TEST-ACC-${Date.now()}</li>
                                        <li><strong>Full Name:</strong> Test Customer (Thailand)</li>
                                        <li><strong>National ID:</strong> 1234567890123</li>
                                        <li><strong>Email:</strong> ${TEST_RECIPIENT}</li>
                                        <li><strong>Phone:</strong> +66 812345678</li>
                                    </ul>
                                </div>
                                <div class="section">
                                    <h3>💰 Debt Information:</h3>
                                    <ul>
                                        <li><strong>Creditor:</strong> Test Bank (Thailand) Ltd.</li>
                                        <li><strong>Debt Type:</strong> Personal Loan</li>
                                        <li><strong>Outstanding Balance:</strong> ฿50,000.00</li>
                                        <li><strong>Contract Date:</strong> 15/01/2023</li>
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
                                    <strong>✅ Email Configuration Verified:</strong>
                                    <ul style="list-style:none;padding:10px 0 0 0;margin:0">
                                        <li>📧 From: ${EMAIL}</li>
                                        <li>📬 To: ${SYSTEM_EMAIL}</li>
                                        <li>🔐 Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}</li>
                                        <li>🌐 SMTP: ${config.host}:${config.port}</li>
                                        <li>✅ Status: Operational (Google Workspace)</li>
                                    </ul>
                                </div>
                                <p style="color:#666;font-size:14px;margin-top:25px">
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
                            </div>
                            <div class="footer">
                                <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p style="margin:5px 0 0 0">Automated System Notification - Google Workspace</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `,
                text: `
✅ SYSTEM EMAIL TEST SUCCESSFUL
Payment Request Notification

A customer has submitted a payment request through the debtor portal.

CUSTOMER DETAILS:
- Account Number: TEST-ACC-${Date.now()}
- Full Name: Test Customer (Thailand)
- National ID: 1234567890123
- Email: ${TEST_RECIPIENT}
- Phone: +66 812345678

DEBT INFORMATION:
- Creditor: Test Bank (Thailand) Ltd.
- Debt Type: Personal Loan
- Outstanding Balance: ฿50,000.00
- Contract Date: 15/01/2023

PAYMENT DETAILS:
- Payment Type: Full Payment
- Amount Paid: ฿50,000.00
- Transaction Number: TXN-TEST-${Date.now()}
- Payment Method: Bank Transfer
- Payment Date: ${new Date().toLocaleDateString('en-GB')}

✅ Email Configuration Verified:
- From: ${EMAIL}
- To: ${SYSTEM_EMAIL}
- Security: ${config.secure ? 'SSL/TLS' : 'STARTTLS'}
- SMTP: ${config.host}:${config.port}
- Status: Operational (Google Workspace)

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
Automated System Notification - Google Workspace
                `
            };
            
            const info2 = await transporter.sendMail(notificationEmail);
            console.log(`   ✅ System Notification Sent Successfully!`);
            console.log(`   📨 Message ID: ${info2.messageId}\n`);
            
            // SUCCESS!
            successCount++;
            console.log(`${'='.repeat(80)}`);
            console.log('🎉🎉🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉🎉🎉');
            console.log(`${'='.repeat(80)}\n`);
            console.log('✅ VALIDATION COMPLETE - Google Workspace Email Operational!\n');
            console.log('📋 USE THIS CONFIGURATION FOR PRODUCTION:\n');
            console.log(`host: '${config.host}'`);
            console.log(`port: ${config.port}`);
            console.log(`secure: ${config.secure}`);
            console.log(`auth: {`);
            console.log(`  user: '${EMAIL}',`);
            console.log(`  pass: '${APP_PASSWORD}'`);
            console.log(`}`);
            console.log(`tls: {`);
            console.log(`  rejectUnauthorized: ${config.tls.rejectUnauthorized}`);
            if (config.tls.minVersion) {
                console.log(`  minVersion: '${config.tls.minVersion}'`);
            }
            console.log(`}`);
            console.log(`\n📧 CHECK THESE INBOXES:`);
            console.log(`\n   1️⃣  ${TEST_RECIPIENT}`);
            console.log(`      - OTP Email (Debtor Login Flow)`);
            console.log(`      - Beautiful HTML template with OTP code\n`);
            console.log(`   2️⃣  ${SYSTEM_EMAIL}`);
            console.log(`      - Payment Notification (System Email)`);
            console.log(`      - Collection team notification format\n`);
            console.log(`🚀 READY FOR LAMBDA DEPLOYMENT!\n`);
            
            transporter.close();
            return; // Stop testing once we find a working config
            
        } catch (error) {
            console.log(`   ❌ FAILED: ${error.message.substring(0, 100)}\n`);
            
            if (error.code === 'EAUTH' || error.message.includes('authentication') || error.message.includes('Username and Password')) {
                console.log(`   🔑 Authentication Error - Possible Issues:`);
                console.log(`      1. App password might be incorrect: ${APP_PASSWORD}`);
                console.log(`      2. 2-Step Verification might not be enabled`);
                console.log(`      3. App password might be expired or revoked`);
                console.log(`      4. Less secure app access might be disabled`);
                console.log(`\n   📖 To fix:`);
                console.log(`      1. Go to: https://myaccount.google.com/apppasswords`);
                console.log(`      2. Sign in to: ${EMAIL}`);
                console.log(`      3. Generate NEW app password for "Mail"`);
                console.log(`      4. Copy the 16-character code\n`);
            }
        }
    }
    
    if (successCount === 0) {
        console.log(`\n${'='.repeat(80)}`);
        console.log('❌ NO WORKING CONFIGURATION FOUND');
        console.log(`${'='.repeat(80)}\n`);
        console.log(`⚠️  None of the Google Workspace configurations worked.\n`);
        console.log(`🔍 Please verify:\n`);
        console.log(`   1. Email: ${EMAIL}`);
        console.log(`   2. App Password: ${APP_PASSWORD} (16 characters)`);
        console.log(`   3. This is a Google Workspace account for poweramc.com domain`);
        console.log(`   4. 2-Step Verification is enabled`);
        console.log(`   5. App password was generated from Google Account settings\n`);
        console.log(`📖 Steps to generate Google Workspace App Password:\n`);
        console.log(`   1. Sign in to Google Admin (admin.google.com) or user account`);
        console.log(`   2. Go to Security → 2-Step Verification`);
        console.log(`   3. Enable 2-Step Verification if not already enabled`);
        console.log(`   4. Go to App passwords: https://myaccount.google.com/apppasswords`);
        console.log(`   5. Select "Mail" and your device`);
        console.log(`   6. Copy the generated 16-character password`);
        console.log(`   7. Use that password (remove spaces)\n`);
    }
}

console.log('Starting Google Workspace email validation...\n');
testGoogleWorkspace().catch(error => {
    console.error('\n💥 CRITICAL ERROR:', error.message);
    console.error('\nPlease check your credentials and try again.');
    process.exit(1);
});
