const nodemailer = require('nodemailer');

async function comprehensiveEmailTest() {
    console.log('🔐 COMPREHENSIVE EMAIL VALIDATION TEST');
    console.log('=' .repeat(80));
    console.log('Testing EVERY possible email configuration...\n');
    
    // Credentials to test
    const APP_PASSWORD = 'auzsoajwasucpedy';
    const EMAIL_ADDRESSES = [
        'hello@poweramc.com',
        'hello@poweramc.co',
        'Hello@poweramc.com',
        'Hello@poweramc.co'
    ];
    const TEST_RECIPIENT = 'tilakagrawal7777@gmail.com';
    
    // All possible SMTP configurations
    const SMTP_CONFIGS = [
        // Gmail SMTP (for Google Workspace with custom domain)
        {
            name: 'Google Workspace / Gmail - Port 587 TLS',
            host: 'smtp.gmail.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true, minVersion: 'TLSv1.2' }
        },
        {
            name: 'Google Workspace / Gmail - Port 465 SSL',
            host: 'smtp.gmail.com',
            port: 465,
            secure: true,
            tls: { rejectUnauthorized: true, minVersion: 'TLSv1.2' }
        },
        {
            name: 'Google Workspace / Gmail - Port 25',
            host: 'smtp.gmail.com',
            port: 25,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        // Microsoft 365 / Outlook
        {
            name: 'Microsoft 365 / Outlook - Port 587',
            host: 'smtp.office365.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true, ciphers: 'SSLv3' }
        },
        {
            name: 'Microsoft Outlook - Port 587',
            host: 'smtp-mail.outlook.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        },
        // GoDaddy Professional Email (Titan)
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
        {
            name: 'GoDaddy Professional Email - Port 3535',
            host: 'smtpout.secureserver.net',
            port: 3535,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        // GoDaddy Asia/Europe Alternative
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
        // Zoho Mail
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
        // Generic cPanel/Custom domain attempts
        {
            name: 'Custom Domain - mail.poweramc.com Port 587',
            host: 'mail.poweramc.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'Custom Domain - mail.poweramc.com Port 465',
            host: 'mail.poweramc.com',
            port: 465,
            secure: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'Custom Domain - smtp.poweramc.com Port 587',
            host: 'smtp.poweramc.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'Custom Domain - mail.poweramc.co Port 587',
            host: 'mail.poweramc.co',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'Custom Domain - smtp.poweramc.co Port 587',
            host: 'smtp.poweramc.co',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: false }
        },
        // SendGrid
        {
            name: 'SendGrid - Port 587',
            host: 'smtp.sendgrid.net',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        },
        // Amazon SES
        {
            name: 'Amazon SES US East - Port 587',
            host: 'email-smtp.us-east-1.amazonaws.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        },
        {
            name: 'Amazon SES Singapore - Port 587',
            host: 'email-smtp.ap-southeast-1.amazonaws.com',
            port: 587,
            secure: false,
            requireTLS: true,
            tls: { rejectUnauthorized: true }
        }
    ];
    
    let successfulConfigs = [];
    let testNumber = 0;
    const totalTests = EMAIL_ADDRESSES.length * SMTP_CONFIGS.length;
    
    for (const email of EMAIL_ADDRESSES) {
        console.log(`\n${'='.repeat(80)}`);
        console.log(`📧 TESTING EMAIL: ${email}`);
        console.log(`${'='.repeat(80)}\n`);
        
        for (const config of SMTP_CONFIGS) {
            testNumber++;
            console.log(`[${testNumber}/${totalTests}] 🧪 ${config.name}`);
            console.log(`   📧 Email: ${email}`);
            console.log(`   🌐 Server: ${config.host}:${config.port}`);
            
            const transporter = nodemailer.createTransport({
                host: config.host,
                port: config.port,
                secure: config.secure,
                auth: {
                    user: email,
                    pass: APP_PASSWORD
                },
                tls: config.tls,
                requireTLS: config.requireTLS,
                connectionTimeout: 10000,
                greetingTimeout: 5000,
                socketTimeout: 10000,
                name: 'poweramc.co',
                pool: false,
                debug: false,
                logger: false
            });
            
            try {
                // Test 1: Connection & Authentication
                await transporter.verify();
                console.log(`   ✅ Authentication: SUCCESS`);
                
                // Test 2: Send actual email
                const testOTP = Math.floor(100000 + Math.random() * 900000).toString();
                
                const mailOptions = {
                    from: `"PowerAMC Portal" <${email}>`,
                    to: TEST_RECIPIENT,
                    subject: `✅ SUCCESS - Email Working! OTP: ${testOTP}`,
                    html: `
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                                .success { background: #27ae60; color: white; padding: 20px; text-align: center; border-radius: 10px; }
                                .otp { font-size: 36px; font-weight: bold; color: #27ae60; text-align: center; 
                                       letter-spacing: 8px; padding: 25px; background: #f0f8ff; 
                                       border-radius: 10px; margin: 25px 0; border: 3px solid #27ae60; }
                                .config { background: #e7f3ff; padding: 15px; margin: 20px 0; border-radius: 5px; font-size: 14px; }
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <div class="success">
                                    <h1 style="margin: 0;">✅ EMAIL CONFIGURATION WORKING!</h1>
                                    <p style="margin: 10px 0 0 0;">${config.name}</p>
                                </div>
                                
                                <h2>🎉 Success! Your Email System is Operational</h2>
                                <p>This email confirms that your SMTP configuration is working perfectly.</p>
                                
                                <div class="otp">${testOTP}</div>
                                
                                <div class="config">
                                    <h3 style="margin-top: 0;">📋 Working Configuration:</h3>
                                    <ul style="margin: 10px 0;">
                                        <li><strong>Configuration:</strong> ${config.name}</li>
                                        <li><strong>Email:</strong> ${email}</li>
                                        <li><strong>SMTP Server:</strong> ${config.host}</li>
                                        <li><strong>Port:</strong> ${config.port}</li>
                                        <li><strong>Security:</strong> ${config.secure ? 'SSL' : 'TLS/STARTTLS'}</li>
                                        <li><strong>Timestamp:</strong> ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })}</li>
                                    </ul>
                                </div>
                                
                                <p style="color: #27ae60; font-weight: bold; font-size: 18px;">
                                    ✅ Ready for Production Deployment!
                                </p>
                                
                                <hr style="margin: 30px 0;">
                                <p style="color: #666; font-size: 12px;">
                                    PowerAMC Customer Portal - Automated Email Test<br>
                                    Test conducted on: ${new Date().toISOString()}
                                </p>
                            </div>
                        </body>
                        </html>
                    `,
                    text: `
✅ EMAIL CONFIGURATION WORKING!
${config.name}

Success! Your Email System is Operational

Your OTP Code: ${testOTP}

Working Configuration:
- Configuration: ${config.name}
- Email: ${email}
- SMTP Server: ${config.host}
- Port: ${config.port}
- Security: ${config.secure ? 'SSL' : 'TLS/STARTTLS'}
- Timestamp: ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })}

✅ Ready for Production Deployment!

PowerAMC Customer Portal - Automated Email Test
Test conducted on: ${new Date().toISOString()}
                    `
                };
                
                const info = await transporter.sendMail(mailOptions);
                console.log(`   ✅ Email Sent: SUCCESS (Message ID: ${info.messageId})`);
                console.log(`   🎉 THIS CONFIGURATION WORKS!`);
                
                successfulConfigs.push({
                    email: email,
                    config: config.name,
                    host: config.host,
                    port: config.port,
                    secure: config.secure,
                    messageId: info.messageId
                });
                
                transporter.close();
                
                // Don't test other configs for this email if we found one that works
                console.log(`\n   ⏭️  Skipping remaining tests for ${email} (found working config)\n`);
                break;
                
            } catch (error) {
                let errorType = '❌';
                let errorMsg = error.message;
                
                if (error.code === 'EAUTH' || errorMsg.includes('authentication') || errorMsg.includes('Username and Password')) {
                    errorType = '🔑';
                    errorMsg = 'Authentication failed - wrong credentials or not supported';
                } else if (error.code === 'ECONNECTION' || error.code === 'ETIMEDOUT' || errorMsg.includes('connect')) {
                    errorType = '🌐';
                    errorMsg = 'Connection failed - server unreachable';
                } else if (errorMsg.includes('ENOTFOUND') || errorMsg.includes('getaddrinfo')) {
                    errorType = '🔍';
                    errorMsg = 'DNS lookup failed - server does not exist';
                } else if (errorMsg.includes('certificate') || errorMsg.includes('SSL')) {
                    errorType = '🔒';
                    errorMsg = 'SSL/TLS error - certificate issue';
                }
                
                console.log(`   ${errorType} Failed: ${errorMsg.substring(0, 80)}`);
            }
        }
    }
    
    // Final Summary
    console.log(`\n${'='.repeat(80)}`);
    console.log('📊 COMPREHENSIVE TEST SUMMARY');
    console.log(`${'='.repeat(80)}\n`);
    
    if (successfulConfigs.length > 0) {
        console.log(`✅ SUCCESS! Found ${successfulConfigs.length} working configuration(s):\n`);
        
        successfulConfigs.forEach((config, index) => {
            console.log(`${index + 1}. 🎉 WORKING CONFIGURATION:`);
            console.log(`   📧 Email: ${config.email}`);
            console.log(`   📋 Config: ${config.config}`);
            console.log(`   🌐 SMTP: ${config.host}:${config.port}`);
            console.log(`   🔒 SSL: ${config.secure ? 'Yes' : 'No (TLS/STARTTLS)'}`);
            console.log(`   📨 Message ID: ${config.messageId}`);
            console.log(``);
        });
        
        console.log(`${'='.repeat(80)}`);
        console.log(`🎯 USE THIS FOR PRODUCTION:\n`);
        
        const best = successfulConfigs[0];
        console.log(`host: '${best.host}'`);
        console.log(`port: ${best.port}`);
        console.log(`secure: ${best.secure}`);
        console.log(`auth: {`);
        console.log(`  user: '${best.email}',`);
        console.log(`  pass: '${APP_PASSWORD}'`);
        console.log(`}`);
        if (!best.secure) {
            console.log(`requireTLS: true`);
        }
        
        console.log(`\n📧 Check your inbox at: ${TEST_RECIPIENT}`);
        console.log(`   You should have ${successfulConfigs.length} test email(s)\n`);
        
    } else {
        console.log(`❌ NO WORKING CONFIGURATIONS FOUND\n`);
        console.log(`🔍 Troubleshooting Steps:\n`);
        console.log(`1. Verify email addresses:`);
        console.log(`   - hello@poweramc.com`);
        console.log(`   - hello@poweramc.co`);
        console.log(`\n2. Verify app password: auzsoajwasucpedy`);
        console.log(`   - Is this from Google App Passwords?`);
        console.log(`   - Or from another email provider?`);
        console.log(`\n3. Check email provider:`);
        console.log(`   - Where do you log in to check this email?`);
        console.log(`   - Gmail.com? Outlook? GoDaddy webmail?`);
        console.log(`   - Check with your email hosting provider for correct SMTP settings`);
        console.log(`\n4. Try logging into the email account directly to confirm credentials work\n`);
    }
    
    console.log(`${'='.repeat(80)}`);
    console.log(`\nTotal Tests Run: ${testNumber}`);
    console.log(`Successful: ${successfulConfigs.length}`);
    console.log(`Failed: ${testNumber - successfulConfigs.length}\n`);
}

// Run the comprehensive test
console.log('Starting comprehensive email validation...\n');
comprehensiveEmailTest().catch(error => {
    console.error('\n💥 CRITICAL ERROR:', error.message);
    console.error('\nStack trace:', error.stack);
    process.exit(1);
});
