const nodemailer = require('nodemailer');

async function testGoDaddyWelleazy() {
    console.log('🔐 GODADDY MAILBOX VALIDATION - WELLEAZY.IN');
    console.log('=' .repeat(80));
    
    const EMAIL = 'digital.marketing@welleazy.in';
    const PASSWORD = 'Welcome@123';
    const TEST_RECIPIENT = 'firoz.khan@veriright.com';
    const SYSTEM_EMAIL = 'digital.marketing@welleazy.in';
    
    console.log(`📧 Email: ${EMAIL}`);
    console.log(`🔑 Password: ${PASSWORD}`);
    console.log(`📬 Test Recipient: ${TEST_RECIPIENT}`);
    console.log(`📬 System Email: ${SYSTEM_EMAIL}\n`);
    
    // Comprehensive GoDaddy SMTP configurations
    const configs = [
        {
            name: 'GoDaddy Professional Email - Port 587 (STARTTLS)',
            host: 'smtpout.secureserver.net',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Professional Email - Port 465 (SSL)',
            host: 'smtpout.secureserver.net',
            port: 465,
            secure: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Professional Email - Port 25',
            host: 'smtpout.secureserver.net',
            port: 25,
            secure: false,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Professional Email - Port 80',
            host: 'smtpout.secureserver.net',
            port: 80,
            secure: false,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Professional Email - Port 3535',
            host: 'smtpout.secureserver.net',
            port: 3535,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy EMEA - Port 587',
            host: 'smtpout.europe.secureserver.net',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Asia - Port 587',
            host: 'smtpout.asia.secureserver.net',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Relay - relay-hosting.secureserver.net:25',
            host: 'relay-hosting.secureserver.net',
            port: 25,
            secure: false,
            tls: { rejectUnauthorized: false }
        }
    ];
    
    for (const config of configs) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`🧪 ${config.name}`);
        console.log(`   🌐 ${config.host}:${config.port}`);
        
        const transporter = nodemailer.createTransport({
            host: config.host,
            port: config.port,
            secure: config.secure,
            auth: {
                user: EMAIL,
                pass: PASSWORD
            },
            tls: config.tls,
            requireTLS: config.requireTLS,
            connectionTimeout: 15000,
            greetingTimeout: 10000,
            socketTimeout: 15000,
            name: 'welleazy.in',
            pool: false,
            debug: true,
            logger: true
        });
        
        try {
            console.log('\n   📡 Step 1: Testing Connection & Authentication...');
            await transporter.verify();
            console.log('   ✅ Authentication: SUCCESS!\n');
            
            // Send OTP email
            console.log('   📧 Step 2: Sending OTP Email...');
            const testOTP = Math.floor(100000 + Math.random() * 900000).toString();
            
            const otpEmail = {
                from: `"PowerAMC Portal" <${EMAIL}>`,
                to: TEST_RECIPIENT,
                replyTo: EMAIL,
                subject: `✅ EMAIL WORKING - OTP: ${testOTP}`,
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head><meta charset="utf-8"><style>
                        body{font-family:Arial,sans-serif;margin:0;padding:0;color:#333}
                        .container{max-width:600px;margin:0 auto;padding:20px}
                        .success{background:linear-gradient(135deg,#27ae60,#2ecc71);color:white;padding:30px;text-align:center;border-radius:10px 10px 0 0}
                        .content{background:#f9f9f9;padding:30px;border-radius:0 0 10px 10px}
                        .otp{font-size:36px;font-weight:bold;color:#667eea;text-align:center;letter-spacing:8px;
                             padding:25px;background:linear-gradient(135deg,#f5f7fa,#c3cfe2);border-radius:10px;
                             margin:25px 0;box-shadow:0 4px 6px rgba(0,0,0,0.1);border:3px solid #27ae60}
                        .config{background:#e7f3ff;border-left:4px solid#0066cc;padding:15px;margin:20px 0;border-radius:5px}
                        .warning{color:#e74c3c;background:#fee;padding:15px;border-left:4px solid#e74c3c;margin:20px 0;border-radius:5px}
                        .footer{background:#34495e;color:white;padding:20px;text-align:center;font-size:12px;margin-top:20px;border-radius:10px}
                    </style></head>
                    <body>
                        <div class="container">
                            <div class="success">
                                <h1 style="margin:0">✅ GODADDY EMAIL WORKING!</h1>
                                <p style="margin:10px 0 0 0">${config.name}</p>
                            </div>
                            <div class="content">
                                <h2>🎉 Dear Customer,</h2>
                                <p>Your GoDaddy email configuration is working perfectly! Your One-Time Password (OTP) is:</p>
                                <div class="otp">${testOTP}</div>
                                <p><strong>⏰ This code expires in 5 minutes.</strong></p>
                                <div class="warning">
                                    <strong>Security Notice:</strong> Never share this code. PowerAMC will never ask for your OTP via phone or email.
                                </div>
                                <div class="config">
                                    <h3 style="margin-top:0">📋 Working Configuration:</h3>
                                    <ul style="margin:10px 0">
                                        <li><strong>Provider:</strong> GoDaddy Professional Email</li>
                                        <li><strong>Email:</strong> ${EMAIL}</li>
                                        <li><strong>SMTP:</strong> ${config.host}:${config.port}</li>
                                        <li><strong>Security:</strong> ${config.secure ? 'SSL' : 'TLS/STARTTLS'}</li>
                                        <li><strong>Status:</strong> <span style="color:#27ae60;font-weight:bold">OPERATIONAL ✅</span></li>
                                        <li><strong>Time:</strong> ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})} (Bangkok)</li>
                                    </ul>
                                </div>
                                <hr style="border:none;border-top:1px solid#ddd;margin:20px 0">
                                <p><strong>PowerAMC Collections Team</strong><br>
                                Email: ${EMAIL}<br>Website: www.poweramc.com</p>
                            </div>
                            <div class="footer">
                                <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p style="margin:5px 0 0 0">GoDaddy Email Test - Configuration Verified</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `
            };
            
            const info1 = await transporter.sendMail(otpEmail);
            console.log(`   ✅ OTP Email Sent! Message ID: ${info1.messageId}\n`);
            
            // Send system notification
            console.log('   📬 Step 3: Sending System Notification...');
            
            const sysEmail = {
                from: `"PowerAMC System" <${EMAIL}>`,
                to: SYSTEM_EMAIL,
                replyTo: TEST_RECIPIENT,
                subject: '✅ TEST - Payment Request Notification',
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head><meta charset="utf-8"><style>
                        body{font-family:Arial,sans-serif;margin:0;padding:0;color:#333}
                        .container{max-width:700px;margin:0 auto;padding:20px;background:#f5f5f5}
                        .header{background:#27ae60;color:white;padding:20px;text-align:center;border-radius:10px 10px 0 0}
                        .content{background:white;padding:30px;border-radius:0 0 10px 10px}
                        .section{margin:20px 0;padding:15px;background:#f8f9fa;border-left:4px solid#667eea;border-radius:5px}
                        .section h3{margin-top:0;color:#667eea}
                        .section ul{list-style:none;padding:0}
                        .section li{padding:8px 0;border-bottom:1px solid#e9ecef}
                        .section li:last-child{border-bottom:none}
                        .section li strong{display:inline-block;width:180px;color:#495057}
                        .badge{background:#d4edda;border-left:4px solid#28a745;padding:15px;margin:20px 0;border-radius:5px}
                        .footer{margin-top:20px;padding:15px;background:#34495e;color:white;text-align:center;border-radius:10px;font-size:12px}
                    </style></head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1 style="margin:0">✅ SYSTEM EMAIL TEST</h1>
                                <p style="margin:10px 0 0 0">Payment Request Notification</p>
                            </div>
                            <div class="content">
                                <div class="badge">
                                    <strong>🎉 GoDaddy Email System Working!</strong><br>
                                    Configuration: ${config.name}
                                </div>
                                <h2>Payment Request Submitted</h2>
                                <div class="section">
                                    <h3>👤 Customer Details:</h3>
                                    <ul>
                                        <li><strong>Account:</strong> TEST-${Date.now()}</li>
                                        <li><strong>Name:</strong> Test Customer</li>
                                        <li><strong>National ID:</strong> 1234567890123</li>
                                        <li><strong>Email:</strong> ${TEST_RECIPIENT}</li>
                                        <li><strong>Phone:</strong> +66 812345678</li>
                                    </ul>
                                </div>
                                <div class="section">
                                    <h3>💰 Debt Information:</h3>
                                    <ul>
                                        <li><strong>Creditor:</strong> Test Bank Ltd.</li>
                                        <li><strong>Outstanding:</strong> ฿50,000.00</li>
                                        <li><strong>Debt Type:</strong> Personal Loan</li>
                                    </ul>
                                </div>
                                <div class="section">
                                    <h3>📝 Payment Details:</h3>
                                    <ul>
                                        <li><strong>Amount:</strong> ฿50,000.00</li>
                                        <li><strong>Transaction:</strong> TXN-${Date.now()}</li>
                                        <li><strong>Method:</strong> Bank Transfer</li>
                                    </ul>
                                </div>
                                <div class="badge">
                                    <strong>✅ Email Configuration:</strong>
                                    <ul style="list-style:none;padding:10px 0 0 0;margin:0">
                                        <li>📧 From: ${EMAIL}</li>
                                        <li>📬 To: ${SYSTEM_EMAIL}</li>
                                        <li>🌐 SMTP: ${config.host}:${config.port}</li>
                                        <li>✅ Status: Operational</li>
                                    </ul>
                                </div>
                            </div>
                            <div class="footer">
                                <p style="margin:0">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `
            };
            
            const info2 = await transporter.sendMail(sysEmail);
            console.log(`   ✅ System Email Sent! Message ID: ${info2.messageId}\n`);
            
            console.log(`${'='.repeat(80)}`);
            console.log('🎉🎉🎉 ALL TESTS PASSED! 🎉🎉🎉');
            console.log(`${'='.repeat(80)}\n`);
            console.log('📋 USE THIS CONFIGURATION:\n');
            console.log(`host: '${config.host}'`);
            console.log(`port: ${config.port}`);
            console.log(`secure: ${config.secure}`);
            console.log(`auth: {`);
            console.log(`  user: '${EMAIL}',`);
            console.log(`  pass: '${PASSWORD}'`);
            console.log(`}`);
            console.log(`tls: { rejectUnauthorized: false }`);
            if (config.requireTLS) console.log(`requireTLS: true`);
            console.log(`\n📧 CHECK INBOXES:`);
            console.log(`   1️⃣  ${TEST_RECIPIENT} - OTP Email`);
            console.log(`   2️⃣  ${SYSTEM_EMAIL} - System Notification`);
            console.log(`\n🚀 READY FOR PRODUCTION!\n`);
            
            transporter.close();
            return;
            
        } catch (error) {
            console.log(`   ❌ FAILED: ${error.message.substring(0, 100)}`);
            if (error.code === 'EAUTH') {
                console.log(`   🔑 Authentication rejected - wrong credentials`);
            }
        }
    }
    
    console.log(`\n${'='.repeat(80)}`);
    console.log('❌ NO WORKING CONFIGURATION FOUND');
    console.log(`${'='.repeat(80)}\n`);
    console.log(`Tested all GoDaddy SMTP servers and ports.`);
    console.log(`Credentials: ${EMAIL} / ${PASSWORD}\n`);
}

console.log('Starting GoDaddy mailbox validation...\n');
testGoDaddyWelleazy().catch(console.error);
