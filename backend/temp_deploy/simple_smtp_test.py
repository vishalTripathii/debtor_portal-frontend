#!/usr/bin/env python3
"""
Simple SMTP Test - Minimal Connection Test
"""

import smtplib

def simple_smtp_test():
    """Just test basic SMTP connection without complex auth"""
    
    print("🔍 Simple SMTP Connection Test")
    print("=" * 40)
    
    # Test 1: Just connect to server
    try:
        print("📡 Testing server connection...")
        server = smtplib.SMTP("smtpout.secureserver.net", 587)
        print("✅ Connected to GoDaddy SMTP server")
        
        print("🔒 Testing STARTTLS...")
        server.starttls()
        print("✅ TLS connection established")
        
        print("🔐 Testing login...")
        server.login("hello@poweramc.co", "Strive*12345")
        print("✅ LOGIN SUCCESSFUL!")
        
        server.quit()
        print("🎉 Email credentials are working!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Auth Error: {e}")
        print("🔧 Try different password or check account")
        return False
        
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return False

def test_different_passwords():
    """Test with variations of the password"""
    
    passwords = [
        "Strive*12345",      # Correct password
        "Poweramc@123",      # Previous password
        "strive*12345",      # lowercase
        "STRIVE*12345"       # uppercase
    ]
    
    print("\n🔍 Testing Different Passwords...")
    print("=" * 40)
    
    for i, pwd in enumerate(passwords, 1):
        print(f"\n{i}. Testing password: {pwd[:5]}***")
        
        try:
            server = smtplib.SMTP("smtpout.secureserver.net", 587)
            server.starttls()
            server.login("hello@poweramc.co", pwd)
            server.quit()
            
            print(f"✅ SUCCESS! Working password: {pwd}")
            return pwd
            
        except Exception as e:
            print(f"❌ Failed: {str(e)[:50]}...")
    
    return None

if __name__ == "__main__":
    # Test original credentials
    success = simple_smtp_test()
    
    if not success:
        print("\n🔄 Trying password variations...")
        working_pwd = test_different_passwords()
        
        if working_pwd:
            print(f"\n🎉 FOUND WORKING PASSWORD: {working_pwd}")
        else:
            print("\n💥 No working password found")
            print("🔧 Possible solutions:")
            print("   1. Check GoDaddy webmail login")
            print("   2. Reset email password") 
            print("   3. Check account status")
    else:
        print("\n🚀 Ready to deploy with original credentials!")