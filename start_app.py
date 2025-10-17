#!/usr/bin/env python3
"""
Startup script for PythonAnywhere deployment
This ensures the database and barangays are properly initialized
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def initialize_app():
    """Initialize the application with database and barangays"""
    try:
        from app import app, db, Barangay, User
        
        with app.app_context():
            print("Initializing Nabua Waste Management System...")
            
            # Create tables if they don't exist
            db.create_all()
            print("Database tables created/verified")
            
            # Check if barangays exist
            barangay_count = Barangay.query.count()
            if barangay_count == 0:
                print("Loading barangays...")
                from add_nabua_barangays import add_nabua_barangays
                add_nabua_barangays()
                print(f"Loaded {Barangay.query.count()} barangays")
            else:
                print(f"Found {barangay_count} existing barangays")
            
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                print("Creating admin user...")
                from app import create_default_users
                create_default_users()
            else:
                print("Admin user already exists")
            
            print("Application initialization complete!")
            return True
            
    except Exception as e:
        print(f"Error during initialization: {e}")
        return False

if __name__ == "__main__":
    success = initialize_app()
    if success:
        print("✅ Application ready for deployment!")
    else:
        print("❌ Application initialization failed!")
        sys.exit(1)
