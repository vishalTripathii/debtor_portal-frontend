const nodemailer = require('nodemailer');

async function testGoDaddyEmail() {
    console.log('🔧 Testing GoDaddy Email Configuration...');
    
    // GoDaddy SMTP configurations based on official documentation
    const configurations = [
        {
            name: 'GoDaddy Professional Email (Titan) - Port 465 SSL',
            host: 'smtpout.secureserver.net',
            port: 465,
            secure: true, // SSL
            auth: { user: 'hello@poweramc.co', pass: 'Strive*12345' },
            tls: { rejectUnauthorized: false }
        },
        {
            name: 'GoDaddy Professional Email (Titan) - Port 587 TLS',
            host: 'smtpout.secureserver.net',
            port: 587,
            secure: false, // STARTTLS
            auth: { user: 'hello@poweramc.co', pass: 'Strive*12345' },
            tls: { rejectUnauthorized: false },
            requireTLS: true
        },
        {
            name: 'GoDaddy Microsoft 365 Email - Port 587 STARTTLS',
            host: 'smtp.office365.com',
            port: 587,
            secure: false, // STARTTLS
            auth: { user: 'hello@poweramc.co', pass: 'Strive*12345' },
            tls: { rejectUnauthorized: false },
            requireTLS: true
        }
    ];

    for (const config of configurations) {
        console.log(`\n🧪 Testing: ${config.name}`);
        
        const transporter = nodemailer.createTransport({
            ...config,
            connectionTimeout: 10000,
            greetingTimeout: 5000,
            socketTimeout: 10000,
            name: 'poweramc.co', // Add HELO hostname
            logger: false, // Disable debug logs
            debug: false
        });

        try {
            console.log('📡 Testing SMTP connection...');
            await transporter.verify();
            console.log('✅ SMTP connection successful!');
            
            // Send test email with working configuration
            console.log('📧 Sending test OTP email...');
            
            const testOTP = '123456';
            const testEmail = 'john.test@email.com';
            
            const mailOptions = {
                from: '"PowerAMC Customer Portal" <hello@poweramc.co>',
                to: testEmail,
                subject: 'TEST SUCCESS - OTP Code - PowerAMC',
                html: `
                    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 2px solid green;">
                        <div style="background-color: #27ae60; color: white; padding: 20px; text-align: center;">
                            <h1>✅ EMAIL WORKING!</h1>
                            <p>Configuration: ${config.name}</p>
                        </div>
                        <div style="padding: 30px;">
                            <h2>Hello John Smith (NID-123456789),</h2>
                            <p>🎉 Great news! Your email system is now working perfectly!</p>
                            
                            <div style="font-size: 32px; font-weight: bold; color: #27ae60; text-align: center; 
                                       letter-spacing: 5px; padding: 20px; background-color: #ecf0f1; 
                                       border-radius: 5px; margin: 20px 0; border: 2px solid #27ae60;">
                                ${testOTP}
                            </div>
                            
                            <p><strong>✅ This email was sent successfully using:</strong></p>
                            <ul>
                                <li>📧 Email: hello@poweramc.co</li>
                                <li>🔐 Password: Strive*12345</li>
                                <li>🌐 Server: ${config.host}:${config.port}</li>
                                <li>🔒 Security: ${config.secure ? 'SSL' : 'TLS'}</li>
                            </ul>
                            
                            <p style="color: #27ae60; font-weight: bold;">🚀 Ready for deployment!</p>
                        </div>
                    </div>
                `,
                text: `
EMAIL WORKING! Configuration: ${config.name}

Hello John Smith (NID-123456789),
Your OTP code is: ${testOTP}

Email sent successfully using:
- Email: hello@poweramc.co  
- Password: Strive*12345
- Server: ${config.host}:${config.port}
- Security: ${config.secure ? 'SSL' : 'TLS'}

Ready for deployment!
                `
            };

            const info = await transporter.sendMail(mailOptions);
            
            console.log('🎉 SUCCESS! Email sent with working configuration!');
            console.log('📝 Message ID:', info.messageId);
            console.log('🔧 Working config:', config.name);
            
            return {
                success: true,
                messageId: info.messageId,
                workingConfig: config,
                email: testEmail,
                otp: testOTP
            };
            
        } catch (error) {
            console.log(`❌ ${config.name} failed:`, error.message.substring(0, 100));
            continue; // Try next configuration
        }
    }
    
    // If we get here, all configurations failed
    console.log('\n💥 All configurations failed!');
    return {
        success: false,
        error: 'All SMTP configurations failed',
        testedConfigs: configurations.length
    };
}

// Run the test
testGoDaddyEmail()
    .then(result => {
        console.log('\n📋 Test Results:');
        console.log(JSON.stringify(result, null, 2));
        
        if (result.success) {
            console.log('\n🎉 EMAIL SERVICE IS READY!');
            console.log('✅ Nodemailer + GoDaddy SMTP working perfectly');
            console.log('✅ Ready to deploy with working OTP emails');
        } else {
            console.log('\n🚨 EMAIL SERVICE NEEDS FIXING');
            console.log('❌ Please fix the configuration before deploying');
        }
    })
    .catch(error => {
        console.error('💥 Test script failed:', error);
    });