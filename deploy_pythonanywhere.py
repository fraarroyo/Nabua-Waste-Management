#!/usr/bin/env python3
"""
PythonAnywhere Deployment Script for Nabua Waste Management System
Run this script after setting up your PythonAnywhere account
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and print the result"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} failed")
            if result.stderr:
                print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error during {description}: {e}")
        return False

def main():
    print("🚀 PythonAnywhere Deployment Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found. Please run this script from the project directory.")
        return
    
    print("📋 Deployment Steps:")
    print("1. Upload files to PythonAnywhere")
    print("2. Install dependencies")
    print("3. Set up database")
    print("4. Configure WSGI")
    print("5. Test deployment")
    
    print("\n📁 Files to upload to PythonAnywhere:")
    files_to_upload = [
        'app.py',
        'add_nabua_barangays.py',
        'pythonanywhere_wsgi.py',
        'requirements_pythonanywhere.txt',
        'templates/',
        'static/',
        'instance/'
    ]
    
    for file in files_to_upload:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ⚠️  {file} (not found)")
    
    print("\n🔧 Commands to run on PythonAnywhere:")
    print("1. Create virtual environment:")
    print("   mkvirtualenv --python=/usr/bin/python3.10 nabua-waste")
    print("   workon nabua-waste")
    
    print("\n2. Install dependencies:")
    print("   pip install -r requirements_pythonanywhere.txt")
    
    print("\n3. Initialize database:")
    print("   python -c \"from app import app, db; app.app_context().push(); db.create_all()\"")
    
    print("\n4. Load barangays:")
    print("   python -c \"from add_nabua_barangays import add_nabua_barangays; add_nabua_barangays()\"")
    
    print("\n5. Test the application:")
    print("   python -c \"from app import app; print('App loaded successfully')\"")
    
    print("\n📝 WSGI Configuration:")
    print("In PythonAnywhere Web tab, set WSGI file to:")
    print("  /home/fraarroyo/Nabua-Waste-Management/pythonanywhere_wsgi.py")
    
    print("\n🌐 Domain Configuration:")
    print("Your app will be available at:")
    print("  https://fraarroyo.pythonanywhere.com/")
    
    print("\n✅ Deployment preparation complete!")
    print("Follow the steps above to complete the deployment on PythonAnywhere.")

if __name__ == "__main__":
    main()
