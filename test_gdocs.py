#!/usr/bin/env python3

import os
import sys

def test_google_docs_setup():
    """Test if Google Docs integration is properly configured"""
    
    print("Testing Google Docs Integration Setup...")
    print("=" * 50)
    
    # Check if credentials file exists
    creds_file = "credentials.json"
    if os.path.exists(creds_file):
        print("✅ credentials.json found")
    else:
        print("❌ credentials.json NOT found")
        print("   You need to download this from Google Cloud Console")
        print("   See: https://console.cloud.google.com/")
        return False
    
    # Check if Google API libraries are installed
    try:
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import Flow
        print("✅ Google API libraries installed")
    except ImportError as e:
        print("❌ Google API libraries missing")
        print(f"   Install with: new_env/bin/python -m pip install google-api-python-client google-auth-oauthlib")
        return False
    
    # Test the Google Docs tool
    try:
        sys.path.insert(0, 'src')
        from youtube_summarizer.tools.google_docs_tool import GoogleDocsIntegrationTool
        
        tool = GoogleDocsIntegrationTool()
        print("✅ Google Docs tool loaded successfully")
        print("\nTo test Google Docs integration:")
        print("1. Run a video summary in the web interface")
        print("2. Check the 'Publish to Google Docs' checkbox")
        print("3. The first time will require browser authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading Google Docs tool: {e}")
        return False

if __name__ == "__main__":
    success = test_google_docs_setup()
    
    if success:
        print("\n🎉 Google Docs integration is ready to test!")
    else:
        print("\n⚠️  Please fix the issues above before using Google Docs integration")
