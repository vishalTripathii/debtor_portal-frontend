const nodemailer = require('nodemailer');

async function testZohoEmail() {
    console.log('Testing Zoho email credentials...');
    console.log('Email: firoz.khan@welleazy.com');
    console.log('Testing multiple Zoho SMTP configurations...\n');
    
    const configurations = [
        {
            name: 'Zoho SMTP - Port 587 (TLS)',
            config: {
                host: 'smtp.zoho.com',
                port: 587,
                secure: false,
                auth: {
                    user: 'firoz.khan@welleazy.com',
                    pass: 'Master@$1122'
                },
                tls: {
                    rejectUnauthorized: false,
                    ciphers: 'SSLv3'
                },
                requireTLS: true
            }
        },
        {
            name: 'Zoho SMTP - Port 465 (SSL)',
            config: {
                host: 'smtp.zoho.com',
                port: 465,
                secure: true,
                auth: {
                    user: 'firoz.khan@welleazy.com',
                    pass: 'Master@$1122'
                },
                tls: {
                    rejectUnauthorized: false
                }
            }
        },
        {
            name: 'Zoho SMTP - Alternative host',
            config: {
                host: 'smtp.zoho.in',
                port: 587,
                secure: false,
                auth: {
                    user: 'firoz.khan@welleazy.com',
                    pass: 'Master@$1122'
                },
                tls: {
                    rejectUnauthorized: false
                }
            }
        }
    ];

    for (const setup of configurations) {
        console.log(`🔍 Testing: ${setup.name}`);
        console.log(`   Host: ${setup.config.host}:${setup.config.port}`);
        console.log(`   Secure: ${setup.config.secure}`);
        
        const transporter = nodemailer.createTransport({
            ...setup.config,
            connectionTimeout: 60000,
            greetingTimeout: 30000,
            socketTimeout: 60000,
            debug: false,
            logger: false
        });

        try {
            // Test connection and authentication
            console.log('   ⏳ Testing connection...');
            await transporter.verify();
            console.log('   ✅ SUCCESS! Authentication worked');
            
            // Send test email
            console.log('   📧 Sending test email...');
            const result = await transporter.sendMail({
                from: '"PowerAMC Portal Test" <firoz.khan@welleazy.com>',
                to: 'firoz.khan@welleazy.com',
                subject: `Zoho Test - ${setup.name}`,
                html: `
                    <h3>✅ Zoho SMTP Test Successful!</h3>
                    <p><strong>Configuration:</strong> ${setup.name}</p>
                    <p><strong>Host:</strong> ${setup.config.host}:${setup.config.port}</p>
                    <p><strong>Time:</strong> ${new Date().toISOString()}</p>
                    <p>This configuration is working correctly!</p>
                `
            });
            
            console.log('   ✅ Email sent successfully!');
            console.log(`   📧 Message ID: ${result.messageId}`);
            console.log('');
            
            transporter.close();
            return {
                valid: true,
                working_config: setup,
                message: `Success with ${setup.name}`,
                messageId: result.messageId
            };
            
        } catch (error) {
            console.log(`   ❌ Failed: ${error.code || 'Unknown'} - ${error.message}`);
            console.log('');
            transporter.close();
            continue;
        }
    }
    
    return {
        valid: false,
        working_config: null,
        message: 'All Zoho SMTP configurations failed'
    };
}

// Run the test
testZohoEmail()
    .then(result => {
        console.log('\n' + '='.repeat(60));
        console.log('ZOHO EMAIL TEST RESULTS');
        console.log('='.repeat(60));
        console.log('Credentials Valid:', result.valid);
        console.log('SMTP Working:', result.smtp_working);
        console.log('Message:', result.message);
        console.log('='.repeat(60));
        
        if (result.valid) {
            console.log('\n✅ RECOMMENDATION: Use these Zoho credentials for production');
            console.log('   Email: firoz.khan@welleazy.com');
            console.log('   SMTP: smtp.zoho.com:587 (TLS)');
        } else {
            console.log('\n❌ RECOMMENDATION: Do not use these credentials');
            console.log('   Please check email/password or account settings');
        }
        
        process.exit(0);
    })
    .catch(error => {
        console.error('\n💥 Unexpected error:', error);
        process.exit(1);
    });