const nodemailer = require('nodemailer');

exports.handler = async (event, context) => {
    const headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,GET',
        'Content-Type': 'application/json'
    };

    // Handle CORS preflight
    if (event.httpMethod === 'OPTIONS') {
        return {
            statusCode: 200,
            headers,
            body: ''
        };
    }

    try {
        const body = JSON.parse(event.body || '{}');
        
        // Get action from path parameter or body
        const pathAction = event.pathParameters?.action;
        const action = pathAction || body.action || 'send-otp';
        const { email, otp, name } = body;

        // GoDaddy SMTP Configuration
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

        if (action === 'send-otp') {
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
                            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                     color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                            .content { background-color: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                            .otp-code { font-size: 36px; font-weight: bold; color: #667eea; text-align: center; 
                                       letter-spacing: 8px; padding: 25px; 
                                       background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                                       border-radius: 10px; margin: 25px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
                            .warning { color: #e74c3c; font-weight: bold; background-color: #fee; 
                                      padding: 15px; border-left: 4px solid #e74c3c; margin: 20px 0; }
                            .footer { background-color: #34495e; color: white; padding: 20px; 
                                     text-align: center; font-size: 12px; margin-top: 20px; border-radius: 10px; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1>PowerAMC</h1>
                                <p>Customer Portal - OTP Verification</p>
                            </div>
                            <div class="content">
                                <h2>Dear ${name || 'Valued Customer'},</h2>
                                <p>Thank you for using the PowerAMC Customer Portal. Please use the following One-Time Password (OTP) to complete your login:</p>
                                
                                <div class="otp-code">${otp}</div>
                                
                                <p><strong>⏰ This code will expire in 5 minutes.</strong></p>
                                
                                <div class="warning">
                                    <strong>Security Notice:</strong> Do not share this code with anyone. 
                                    PowerAMC will never ask for your OTP via phone or email.
                                </div>
                                
                                <p>If you did not request this code, please ignore this email.</p>
                                
                                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                                <p><strong>PowerAMC Collections Team</strong><br>
                                Email: firoz.khan@welleazy.com<br>
                                Website: www.poweramc.co</p>
                            </div>
                            <div class="footer">
                                <p>© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p>This is an automated message. Please do not reply.</p>
                            </div>
                        </div>
                    </body>
                    </html>
            `,
            text: `
Dear ${name || 'Valued Customer'},

Thank you for using the PowerAMC Customer Portal.

Your One-Time Password (OTP) is: ${otp}

This code will expire in 5 minutes.

Security Notice: Do not share this code with anyone.

If you did not request this code, please ignore this email.

Best regards,
PowerAMC Collections Team
Email: firoz.khan@welleazy.com
Website: www.poweramc.co
                `
            };            const info = await transporter.sendMail(mailOptions);
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    success: true,
                    messageId: info.messageId,
                    message: 'OTP sent successfully'
                })
            };
            
        } else if (action === 'test') {
            // Test connection
            await transporter.verify();
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    success: true,
                    message: 'Email service is working correctly'
                })
            };
        }

    } catch (error) {
        console.error('Email service error:', error);
        
        return {
            statusCode: 500,
            headers,
            body: JSON.stringify({
                success: false,
                error: error.message,
                code: error.code
            })
        };
    }
};