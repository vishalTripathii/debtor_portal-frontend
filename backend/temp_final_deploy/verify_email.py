#!/usr/bin/env python3
"""
Verify Email Account Existence
"""

import socket
import re

def verify_email_domain(email):
    """Check if email domain has MX record"""
    domain = email.split('@')[1]
    
    try:
        import dns.resolver
        mx_records = dns.resolver.resolve(domain, 'MX')
        print(f"✅ Domain {domain} has MX records:")
        for mx in mx_records:
            print(f"   - {mx}")
        return True
    except:
        try:
            # Fallback to basic socket test
            socket.getaddrinfo(domain, 25)
            print(f"✅ Domain {domain} exists")
            return True
        except:
            print(f"❌ Domain {domain} not found")
            return False

def test_smtp_server_availability():
    """Test if SMTP server is reachable"""
    host = "smtpout.secureserver.net"
    ports = [587, 465, 25]
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ Port {port}: Open")
            else:
                print(f"❌ Port {port}: Closed")
        except Exception as e:
            print(f"❌ Port {port}: Error - {e}")

if __name__ == "__main__":
    email = "hello@poweramc.co"
    
    print("🔍 Email Account Verification")
    print("=" * 50)
    print(f"Email: {email}")
    print()
    
    print("1. Checking domain...")
    verify_email_domain(email)
    
    print("\n2. Checking SMTP server ports...")
    test_smtp_server_availability()
    
    print("\n💡 Possible Issues:")
    print("   1. Password might be incorrect")
    print("   2. Account might be locked")
    print("   3. Two-factor auth enabled")
    print("   4. Account suspended")
    print("   5. Need to enable 'Less secure apps'")
    print("\n🔧 Try these steps:")
    print("   1. Login to GoDaddy webmail directly")
    print("   2. Check account status")
    print("   3. Verify password works in webmail")
    print("   4. Check email settings in cPanel")