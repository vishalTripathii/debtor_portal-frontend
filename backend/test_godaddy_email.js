const nodemailer = require('nodemailer');

async function testGoDaddyEmail() {
    try {
        console.log('Testing GoDaddy SMTP configuration...');
        
        const transporter = nodemailer.createTransport({
            host: 'smtpout.secureserver.net',
            port: 587,
            secure: false, // Use STARTTLS
            auth: {
                user: 'hello@poweramc.co',
                pass: 'Strive*12345'
            },
            tls: {
                rejectUnauthorized: false
            },
            requireTLS: true,
            connectionTimeout: 60000,
            greetingTimeout: 30000,
            socketTimeout: 60000,
            debug: true,
            logger: true
        });

        // Verify connection
        await transporter.verify();
        console.log('✅ SMTP connection verified successfully!');

        // Send test email
        const mailOptions = {
            from: 'hello@poweramc.co',
            to: 'hello@poweramc.co', // Send to self for testing
            subject: 'Test OTP Email from GoDaddy SMTP',
            html: `
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Your OTP Code</h2>
                    <p>Your One-Time Password is: <strong>123456</strong></p>
                    <p>This code will expire in 10 minutes.</p>
                </div>
            `
        };

        const info = await transporter.sendMail(mailOptions);
        console.log('✅ Email sent successfully!');
        console.log('Message ID:', info.messageId);
        console.log('Response:', info.response);

    } catch (error) {
        console.error('❌ Error:', error);
    }
}

testGoDaddyEmail();