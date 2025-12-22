#!/usr/bin/env python3
"""
Test SMTP Credentials Locally
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection():
    """Test SMTP connection with original GoDaddy credentials"""
    
    # Original GoDaddy SMTP settings
    smtp_host = "smtpout.secureserver.net"
    smtp_port = 587
    email = "hello@poweramc.co"
    password = "Poweramc@123"
    
    print("🔍 Testing SMTP Connection...")
    print(f"Host: {smtp_host}")
    print(f"Port: {smtp_port}")
    print(f"Email: {email}")
    print("=" * 50)
    
    try:
        # Test TLS connection (port 587)
        print("📡 Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.set_debuglevel(1)  # Show debug info
        
        print("🔒 Starting TLS...")
        server.starttls()
        
        print("🔐 Logging in...")
        server.login(email, password)
        
        print("✅ LOGIN SUCCESS!")
        
        # Send test email
        print("📧 Sending test email...")
        
        msg = MIMEMultipart()
        msg['From'] = email
        msg['To'] = email  # Send to self
        msg['Subject'] = "SMTP Test - Success!"
        
        body = """
        🎉 SMTP Test Successful!
        
        Your Gmail credentials are working correctly.
        
        Credentials tested:
        - Host: smtp.gmail.com
        - Port: 587 (TLS)
        - Email: tripathivishalknpd@gmail.com
        
        This email was sent via Python SMTP test.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.sendmail(email, email, msg.as_string())
        server.quit()
        
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("🎉 GoDaddy SMTP is working perfectly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ AUTHENTICATION ERROR: {e}")
        print("💡 Check email/password combination")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("💡 Check host/port settings")
        return False
        
    except Exception as e:
        print(f"❌ GENERAL ERROR: {e}")
        return False

def test_ssl_connection():
    """Test SSL connection (port 465) with Gmail"""
    
    smtp_host = "smtp.gmail.com" 
    smtp_port = 465
    email = "tripathivishalknpd@gmail.com"
    password = "Vistri@123"
    
    print("\n🔍 Testing SSL Connection...")
    print(f"Host: {smtp_host}")
    print(f"Port: {smtp_port}")
    print("=" * 50)
    
    try:
        print("📡 Connecting with SSL...")
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
        server.set_debuglevel(1)
        
        print("🔐 Logging in...")
        server.login(email, password)
        
        print("✅ SSL LOGIN SUCCESS!")
        server.quit()
        return True
        
    except Exception as e:
        print(f"❌ SSL ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🧪 SMTP Credential Test")
    print("=" * 50)
    
    # Test TLS first (recommended)
    tls_success = test_smtp_connection()
    
    if not tls_success:
        # Try SSL if TLS fails
        ssl_success = test_ssl_connection()
        
        if not ssl_success:
            print("\n💥 Both TLS and SSL failed!")
            print("🔧 Possible issues:")
            print("   - Wrong email/password")
            print("   - Account locked")
            print("   - Firewall blocking ports")
            exit(1)
        else:
            print("\n✅ Use SSL configuration (port 465)")
    else:
        print("\n✅ Use TLS configuration (port 587)")
    
    print("\n🎉 Email credentials verified!")
    print("🚀 Ready to deploy with working SMTP!")