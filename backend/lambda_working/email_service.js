const nodemailer = require('nodemailer');

// Create transporter for GoDaddy SMTP
const transporter = nodemailer.createTransporter({
    host: 'smtpout.secureserver.net',
    port: 465,
    secure: true, // true for 465, false for other ports
    auth: {
        user: 'hello@poweramc.co',
        pass: 'Strive*12345'
    },
    tls: {
        rejectUnauthorized: false
    }
});

// Function to send OTP email
async function sendOTPEmail(email, otp, name = 'User') {
    try {
        const mailOptions = {
            from: '"PowerAMC Customer Portal" <hello@poweramc.co>',
            to: email,
            subject: 'Your OTP Code - PowerAMC Customer Portal',
            html: `
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>OTP Verification</title>
                    <style>
                        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                        .header { background-color: #2c3e50; color: white; padding: 20px; text-align: center; }
                        .content { background-color: #f9f9f9; padding: 30px; }
                        .otp-code { font-size: 32px; font-weight: bold; color: #e74c3c; text-align: center; 
                                   letter-spacing: 5px; padding: 20px; background-color: #ecf0f1; 
                                   border-radius: 5px; margin: 20px 0; }
                        .footer { background-color: #34495e; color: white; padding: 15px; text-align: center; font-size: 12px; }
                        .warning { color: #e74c3c; font-weight: bold; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>PowerAMC Customer Portal</h1>
                            <p>OTP Verification Code</p>
                        </div>
                        <div class="content">
                            <h2>Dear ${name},</h2>
                            <p>Thank you for using the PowerAMC Customer Portal. Please use the following One-Time Password (OTP) to complete your login:</p>
                            
                            <div class="otp-code">${otp}</div>
                            
                            <p><strong>This code will expire in 5 minutes.</strong></p>
                            
                            <p class="warning"><strong>Security Notice:</strong> Do not share this code with anyone. PowerAMC will never ask for your OTP via phone or email.</p>
                            
                            <p>If you did not request this code, please ignore this email.</p>
                            
                            <hr>
                            <p><strong>PowerAMC Collections Team</strong><br>
                            Email: hello@poweramc.co<br>
                            Website: www.poweramc.co</p>
                        </div>
                        <div class="footer">
                            <p>© 2025 PowerAMC. All rights reserved.</p>
                            <p>This is an automated message. Please do not reply to this email.</p>
                        </div>
                    </div>
                </body>
                </html>
            `,
            text: `
Dear ${name},

Thank you for using the PowerAMC Customer Portal.

Your One-Time Password (OTP) is: ${otp}

This code will expire in 5 minutes.

Security Notice: Do not share this code with anyone.

If you did not request this code, please ignore this email.

Best regards,
PowerAMC Collections Team
Email: hello@poweramc.co
Website: www.poweramc.co
            `
        };

        const info = await transporter.sendMail(mailOptions);
        
        return {
            success: true,
            messageId: info.messageId,
            response: info.response
        };
        
    } catch (error) {
        console.error('Email send error:', error);
        return {
            success: false,
            error: error.message,
            code: error.code
        };
    }
}

// Test email function
async function testEmail() {
    try {
        const result = await sendOTPEmail('test@example.com', '123456', 'Test User');
        return result;
    } catch (error) {
        return { success: false, error: error.message };
    }
}

module.exports = {
    sendOTPEmail,
    testEmail
};