const nodemailer = require('nodemailer');

async function testRealPassword() {
    console.log('🔐 TESTING WITH REAL PASSWORD');
    console.log('=' .repeat(80));
    
    const EMAIL = 'hello@poweramc.co';
    const PASSWORD = String('Strive*12345'); // Ensure it's treated as a literal string
    const TEST_RECIPIENT = 'tilakagrawal7777@gmail.com';
    
    console.log(`📋 Password Check: "${PASSWORD}" (Length: ${PASSWORD.length})`);
    
    console.log(`📧 Email: ${EMAIL}`);
    console.log(`🔑 Password: ${PASSWORD}`);
    console.log(`📬 Test Recipient: ${TEST_RECIPIENT}\n`);
    
    // Most common SMTP configurations for custom domains
    const configs = [
        // GoDaddy (most common for .co domains)
        {
            name: 'GoDaddy Professional Email - Port 587',
            host: 'smtpout.secureserver.net',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Professional Email - Port 465',
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
        // Google Workspace
        {
            name: 'Google Workspace - Port 587',
            host: 'smtp.gmail.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        },
        {
            name: 'Google Workspace - Port 465',
            host: 'smtp.gmail.com',
            port: 465,
            secure: true,
            tls: { rejectUnauthorized: true }
        },
        // Microsoft 365
        {
            name: 'Microsoft 365 - Port 587',
            host: 'smtp.office365.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        },
        // Zoho
        {
            name: 'Zoho Mail - Port 587',
            host: 'smtp.zoho.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        },
        {
            name: 'Zoho Mail - Port 465',
            host: 'smtp.zoho.com',
            port: 465,
            secure: true,
            tls: { rejectUnauthorized: true }
        },
        // Custom domain attempts
        {
            name: 'Custom Domain - mail.poweramc.co:587',
            host: 'mail.poweramc.co',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'Custom Domain - mail.poweramc.co:465',
            host: 'mail.poweramc.co',
            port: 465,
            secure: true,
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
            name: 'poweramc.co',
            pool: false,
            debug: true,
            logger: true
        });
        
        try {
            // Test connection
            console.log('\n   📡 Testing connection...');
            await transporter.verify();
            console.log('   ✅ Connection & Authentication: SUCCESS!');
            
            // Send test email
            console.log('   📧 Sending test email...');
            const testOTP = Math.floor(100000 + Math.random() * 900000).toString();
            
            const mailOptions = {
                from: `"PowerAMC Portal" <${EMAIL}>`,
                to: TEST_RECIPIENT,
                subject: `✅ EMAIL WORKING - OTP: ${testOTP}`,
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head><meta charset="utf-8"><style>
                        body{font-family:Arial,sans-serif;line-height:1.6;color:#333}
                        .container{max-width:600px;margin:0 auto;padding:20px}
                        .success{background:#27ae60;color:white;padding:20px;text-align:center;border-radius:10px}
                        .otp{font-size:36px;font-weight:bold;color:#27ae60;text-align:center;
                             letter-spacing:8px;padding:25px;background:#f0f8ff;border-radius:10px;
                             margin:25px 0;border:3px solid #27ae60}
                        .config{background:#e7f3ff;padding:15px;margin:20px 0;border-radius:5px}
                    </style></head>
                    <body>
                        <div class="container">
                            <div class="success">
                                <h1 style="margin:0">✅ EMAIL IS WORKING!</h1>
                                <p style="margin:10px 0 0 0">${config.name}</p>
                            </div>
                            <h2>🎉 Success! Your Email System is Operational</h2>
                            <div class="otp">${testOTP}</div>
                            <div class="config">
                                <h3 style="margin-top:0">📋 Working Configuration:</h3>
                                <ul>
                                    <li><strong>Email:</strong> ${EMAIL}</li>
                                    <li><strong>SMTP:</strong> ${config.host}:${config.port}</li>
                                    <li><strong>Security:</strong> ${config.secure ? 'SSL' : 'TLS'}</li>
                                    <li><strong>Time:</strong> ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})}</li>
                                </ul>
                            </div>
                            <p style="color:#27ae60;font-weight:bold;font-size:18px">
                                ✅ Ready for Production!
                            </p>
                        </div>
                    </body>
                    </html>
                `,
                text: `
✅ EMAIL IS WORKING!
${config.name}

Your OTP: ${testOTP}

Configuration:
- Email: ${EMAIL}
- SMTP: ${config.host}:${config.port}
- Security: ${config.secure ? 'SSL' : 'TLS'}
- Time: ${new Date().toLocaleString('en-US', {timeZone: 'Asia/Bangkok'})}

✅ Ready for Production!
                `
            };
            
            const info = await transporter.sendMail(mailOptions);
            console.log(`   ✅ Email sent successfully!`);
            console.log(`   📨 Message ID: ${info.messageId}\n`);
            
            console.log(`${'='.repeat(80)}`);
            console.log('🎉 SUCCESS! FOUND WORKING CONFIGURATION!');
            console.log(`${'='.repeat(80)}\n`);
            console.log('📋 USE THIS CONFIGURATION:\n');
            console.log(`host: '${config.host}'`);
            console.log(`port: ${config.port}`);
            console.log(`secure: ${config.secure}`);
            console.log(`auth: {`);
            console.log(`  user: '${EMAIL}',`);
            console.log(`  pass: '${PASSWORD}'`);
            console.log(`}`);
            if (config.requireTLS) {
                console.log(`requireTLS: true`);
            }
            console.log(`tls: { rejectUnauthorized: false }`);
            console.log(`\n📧 Check inbox: ${TEST_RECIPIENT}\n`);
            
            transporter.close();
            return;
            
        } catch (error) {
            console.log(`   ❌ Failed: ${error.message.substring(0, 100)}`);
        }
    }
    
    console.log(`\n${'='.repeat(80)}`);
    console.log('❌ No working configuration found');
    console.log(`${'='.repeat(80)}`);
}

testRealPassword().catch(console.error);
