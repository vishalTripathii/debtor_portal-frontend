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

        // GoDaddy SMTP Configuration - Welleazy Email
        const transporter = nodemailer.createTransport({
            host: 'smtpout.secureserver.net',
            port: 587,
            secure: false, // Use STARTTLS
            auth: {
                user: 'digital.marketing@welleazy.in',
                pass: 'Welcome@123'
            },
            tls: {
                rejectUnauthorized: false
            },
            requireTLS: true,
            name: 'welleazy.in',
            connectionTimeout: 60000,
            greetingTimeout: 30000,
            socketTimeout: 60000,
            debug: true,
            logger: true
        });

        if (action === 'send-otp') {
            // OTP Email: From Welleazy -> To Debtor
            const mailOptions = {
                from: '"PowerAMC Customer Portal" <digital.marketing@welleazy.in>',
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
                                Email: digital.marketing@welleazy.in<br>
                                Website: www.poweramc.com</p>
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
Email: digital.marketing@welleazy.in
Website: www.poweramc.com
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
            
        } else if (action === 'send-payment-notification') {
            // Payment Notification: From Welleazy -> To hello@poweramc.com
            const { 
                debtor_name, debtor_email, debtor_phone, debtor_national_id,
                account_number, original_creditor, debt_type, outstanding_balance,
                payment_type, payment_amount, transaction_number, receipt_filename
            } = body;

            const mailOptions = {
                from: '"PowerAMC Debtor Portal" <digital.marketing@welleazy.in>',
                to: 'hello@poweramc.com',
                replyTo: debtor_email || 'digital.marketing@welleazy.in',
                subject: `💰 Payment Submitted - Account ${account_number}`,
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                            .container { max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
                            .header { background: linear-gradient(135deg, #27ae60, #2ecc71); color: white; 
                                     padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }
                            .content { background: white; padding: 30px; border-radius: 0 0 10px 10px; }
                            .section { margin: 25px 0; padding: 20px; background: #f8f9fa; 
                                      border-left: 4px solid #667eea; border-radius: 5px; }
                            .section h3 { margin-top: 0; color: #667eea; font-size: 18px; }
                            .info-grid { display: grid; gap: 12px; }
                            .info-row { padding: 10px 0; border-bottom: 1px solid #e9ecef; }
                            .info-row:last-child { border-bottom: none; }
                            .info-label { font-weight: bold; color: #495057; display: inline-block; width: 200px; }
                            .info-value { color: #212529; }
                            .highlight { background: linear-gradient(135deg, #d4edda, #c3e6cb); 
                                        border-left: 4px solid #28a745; padding: 20px; 
                                        margin: 25px 0; border-radius: 5px; }
                            .highlight .amount { font-size: 28px; font-weight: bold; color: #28a745; margin: 10px 0; }
                            .footer { margin-top: 25px; padding: 20px; background: #34495e; 
                                     color: white; text-align: center; border-radius: 10px; font-size: 12px; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1 style="margin: 0;">💰 Payment Submitted</h1>
                                <p style="margin: 10px 0 0 0;">Customer Portal Notification</p>
                            </div>
                            <div class="content">
                                <p style="font-size: 16px; margin-bottom: 25px;">
                                    A debtor has submitted a payment through the customer portal. 
                                    Please review the details below:
                                </p>
                                
                                <div class="highlight">
                                    <strong style="font-size: 18px;">💳 Payment Information:</strong>
                                    <div class="amount">฿${payment_amount || 'N/A'}</div>
                                    <div><strong>Transaction #:</strong> ${transaction_number || 'N/A'}</div>
                                    <div><strong>Payment Type:</strong> ${payment_type || 'N/A'}</div>
                                    ${receipt_filename ? `<div><strong>📎 Receipt:</strong> Uploaded (${receipt_filename})</div>` : ''}
                                </div>

                                <div class="section">
                                    <h3>👤 Customer Details</h3>
                                    <div class="info-grid">
                                        <div class="info-row">
                                            <span class="info-label">Account Number:</span>
                                            <span class="info-value">${account_number || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Name:</span>
                                            <span class="info-value">${debtor_name || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">National ID:</span>
                                            <span class="info-value">${debtor_national_id || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Email:</span>
                                            <span class="info-value">${debtor_email || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Phone:</span>
                                            <span class="info-value">${debtor_phone || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>

                                <div class="section">
                                    <h3>💼 Debt Information</h3>
                                    <div class="info-grid">
                                        <div class="info-row">
                                            <span class="info-label">Original Creditor:</span>
                                            <span class="info-value">${original_creditor || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Debt Type:</span>
                                            <span class="info-value">${debt_type || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Outstanding Balance:</span>
                                            <span class="info-value">฿${outstanding_balance || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>

                                <p style="margin-top: 30px; padding: 15px; background: #e7f3ff; 
                                         border-left: 4px solid #0066cc; border-radius: 5px;">
                                    <strong>⏰ Submitted:</strong> ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })} (Bangkok Time)
                                </p>
                            </div>
                            <div class="footer">
                                <p style="margin: 0;">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p style="margin: 10px 0 0 0;">Automated notification from Debtor Portal</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `,
                text: `
PAYMENT SUBMITTED - PowerAMC Debtor Portal

A debtor has submitted a payment through the customer portal.

💳 PAYMENT INFORMATION:
- Amount: ฿${payment_amount || 'N/A'}
- Transaction #: ${transaction_number || 'N/A'}
- Payment Type: ${payment_type || 'N/A'}
${receipt_filename ? `- Receipt: Uploaded (${receipt_filename})` : ''}

👤 CUSTOMER DETAILS:
- Account Number: ${account_number || 'N/A'}
- Name: ${debtor_name || 'N/A'}
- National ID: ${debtor_national_id || 'N/A'}
- Email: ${debtor_email || 'N/A'}
- Phone: ${debtor_phone || 'N/A'}

💼 DEBT INFORMATION:
- Original Creditor: ${original_creditor || 'N/A'}
- Debt Type: ${debt_type || 'N/A'}
- Outstanding Balance: ฿${outstanding_balance || 'N/A'}

⏰ Submitted: ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })} (Bangkok Time)

---
PowerAMC Collections Team
This is an automated notification from the Debtor Portal.
                `
            };

            const info = await transporter.sendMail(mailOptions);
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    success: true,
                    messageId: info.messageId,
                    message: 'Payment notification sent successfully'
                })
            };

        } else if (action === 'send-support-request') {
            // Support Request: From Welleazy -> To hello@poweramc.com
            const { 
                debtor_name, debtor_email, debtor_phone, debtor_national_id,
                account_number, original_creditor, debt_type, outstanding_balance,
                reason, notes, instalment_plan,
                preferred_contact_date, preferred_contact_time, 
                preferred_contact_method, preferred_contact_value
            } = body;

            const mailOptions = {
                from: '"PowerAMC Debtor Portal" <digital.marketing@welleazy.in>',
                to: 'hello@poweramc.com',
                replyTo: debtor_email || 'digital.marketing@welleazy.in',
                subject: `🆘 Support Request - Account ${account_number}`,
                html: `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <style>
                            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
                            .container { max-width: 700px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
                            .header { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; 
                                     padding: 25px; text-align: center; border-radius: 10px 10px 0 0; }
                            .content { background: white; padding: 30px; border-radius: 0 0 10px 10px; }
                            .section { margin: 25px 0; padding: 20px; background: #f8f9fa; 
                                      border-left: 4px solid #667eea; border-radius: 5px; }
                            .section h3 { margin-top: 0; color: #667eea; font-size: 18px; }
                            .info-grid { display: grid; gap: 12px; }
                            .info-row { padding: 10px 0; border-bottom: 1px solid #e9ecef; }
                            .info-row:last-child { border-bottom: none; }
                            .info-label { font-weight: bold; color: #495057; display: inline-block; width: 200px; }
                            .info-value { color: #212529; }
                            .highlight { background: linear-gradient(135deg, #fff3cd, #ffeaa7); 
                                        border-left: 4px solid #ffc107; padding: 20px; 
                                        margin: 25px 0; border-radius: 5px; }
                            .notes-box { background: #e7f3ff; padding: 15px; margin: 15px 0; 
                                        border-radius: 5px; border-left: 4px solid #0066cc; }
                            .footer { margin-top: 25px; padding: 20px; background: #34495e; 
                                     color: white; text-align: center; border-radius: 10px; font-size: 12px; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <div class="header">
                                <h1 style="margin: 0;">🆘 Support Request</h1>
                                <p style="margin: 10px 0 0 0;">Customer Needs Assistance</p>
                            </div>
                            <div class="content">
                                <p style="font-size: 16px; margin-bottom: 25px;">
                                    A debtor has submitted a support request through the customer portal. 
                                    They need assistance with their payment. Please review and follow up:
                                </p>
                                
                                <div class="highlight">
                                    <strong style="font-size: 18px;">📋 Reason:</strong>
                                    <div style="font-size: 20px; margin: 15px 0; font-weight: bold; color: #d63031;">
                                        ${reason || 'Not specified'}
                                    </div>
                                    ${instalment_plan ? `<div><strong>Requested Plan:</strong> ${instalment_plan}</div>` : ''}
                                </div>

                                ${notes ? `
                                <div class="notes-box">
                                    <strong>📝 Additional Notes:</strong>
                                    <p style="margin: 10px 0 0 0; white-space: pre-wrap;">${notes}</p>
                                </div>
                                ` : ''}

                                <div class="section">
                                    <h3>📞 Contact Preferences</h3>
                                    <div class="info-grid">
                                        ${preferred_contact_date ? `
                                        <div class="info-row">
                                            <span class="info-label">Preferred Date:</span>
                                            <span class="info-value">${preferred_contact_date}</span>
                                        </div>
                                        ` : ''}
                                        ${preferred_contact_time ? `
                                        <div class="info-row">
                                            <span class="info-label">Preferred Time:</span>
                                            <span class="info-value">${preferred_contact_time}</span>
                                        </div>
                                        ` : ''}
                                        ${preferred_contact_method ? `
                                        <div class="info-row">
                                            <span class="info-label">Contact Method:</span>
                                            <span class="info-value">${preferred_contact_method}${preferred_contact_value ? ': ' + preferred_contact_value : ''}</span>
                                        </div>
                                        ` : ''}
                                    </div>
                                </div>

                                <div class="section">
                                    <h3>👤 Customer Details</h3>
                                    <div class="info-grid">
                                        <div class="info-row">
                                            <span class="info-label">Account Number:</span>
                                            <span class="info-value">${account_number || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Name:</span>
                                            <span class="info-value">${debtor_name || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">National ID:</span>
                                            <span class="info-value">${debtor_national_id || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Email:</span>
                                            <span class="info-value">${debtor_email || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Phone:</span>
                                            <span class="info-value">${debtor_phone || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>

                                <div class="section">
                                    <h3>💼 Debt Information</h3>
                                    <div class="info-grid">
                                        <div class="info-row">
                                            <span class="info-label">Original Creditor:</span>
                                            <span class="info-value">${original_creditor || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Debt Type:</span>
                                            <span class="info-value">${debt_type || 'N/A'}</span>
                                        </div>
                                        <div class="info-row">
                                            <span class="info-label">Outstanding Balance:</span>
                                            <span class="info-value">฿${outstanding_balance || 'N/A'}</span>
                                        </div>
                                    </div>
                                </div>

                                <p style="margin-top: 30px; padding: 15px; background: #fee; 
                                         border-left: 4px solid #e74c3c; border-radius: 5px;">
                                    <strong>⚠️ Action Required:</strong> Please follow up with this customer as soon as possible.
                                </p>

                                <p style="margin-top: 15px; padding: 15px; background: #e7f3ff; 
                                         border-left: 4px solid #0066cc; border-radius: 5px;">
                                    <strong>⏰ Submitted:</strong> ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })} (Bangkok Time)
                                </p>
                            </div>
                            <div class="footer">
                                <p style="margin: 0;">© ${new Date().getFullYear()} PowerAMC. All rights reserved.</p>
                                <p style="margin: 10px 0 0 0;">Automated notification from Debtor Portal</p>
                            </div>
                        </div>
                    </body>
                    </html>
                `,
                text: `
SUPPORT REQUEST - PowerAMC Debtor Portal

A debtor has submitted a support request and needs assistance with their payment.

📋 REASON: ${reason || 'Not specified'}
${instalment_plan ? `Requested Plan: ${instalment_plan}` : ''}

${notes ? `📝 ADDITIONAL NOTES:\n${notes}\n` : ''}

📞 CONTACT PREFERENCES:
${preferred_contact_date ? `- Preferred Date: ${preferred_contact_date}` : ''}
${preferred_contact_time ? `- Preferred Time: ${preferred_contact_time}` : ''}
${preferred_contact_method ? `- Contact Method: ${preferred_contact_method}${preferred_contact_value ? ': ' + preferred_contact_value : ''}` : ''}

👤 CUSTOMER DETAILS:
- Account Number: ${account_number || 'N/A'}
- Name: ${debtor_name || 'N/A'}
- National ID: ${debtor_national_id || 'N/A'}
- Email: ${debtor_email || 'N/A'}
- Phone: ${debtor_phone || 'N/A'}

💼 DEBT INFORMATION:
- Original Creditor: ${original_creditor || 'N/A'}
- Debt Type: ${debt_type || 'N/A'}
- Outstanding Balance: ฿${outstanding_balance || 'N/A'}

⚠️ ACTION REQUIRED: Please follow up with this customer as soon as possible.

⏰ Submitted: ${new Date().toLocaleString('en-US', { timeZone: 'Asia/Bangkok' })} (Bangkok Time)

---
PowerAMC Collections Team
This is an automated notification from the Debtor Portal.
                `
            };

            const info = await transporter.sendMail(mailOptions);
            
            return {
                statusCode: 200,
                headers,
                body: JSON.stringify({
                    success: true,
                    messageId: info.messageId,
                    message: 'Support request sent successfully'
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