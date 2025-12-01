#!/usr/bin/env python3
"""
Database Initialization Script
Run this script manually to initialize the database if automatic initialization fails
Works on both Windows and Linux (including PythonAnywhere)
"""

import sys
import os
from pathlib import Path

# Get the directory where this script is located
script_dir = Path(__file__).parent.absolute()
project_dir = str(script_dir)

# Add the project directory to the path
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Change to project directory
os.chdir(project_dir)

print("=" * 60)
print("Database Initialization Script")
print("=" * 60)

try:
    from app import app, db, User, Barangay, WasteItem, WasteTracking, CollectionRoute
    from add_nabua_barangays import add_nabua_barangays
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        print("\n1. Creating database tables...")
        try:
            db.create_all()
            print("   [SUCCESS] Tables created successfully")
        except Exception as e:
            print(f"   [ERROR] Error creating tables: {e}")
            sys.exit(1)
        
        print("\n2. Checking if barangays exist...")
        barangay_count = Barangay.query.count()
        if barangay_count == 0:
            print("   No barangays found, loading...")
            try:
                add_nabua_barangays()
                barangay_count = Barangay.query.count()
                print(f"   [SUCCESS] Loaded {barangay_count} barangays")
            except Exception as e:
                print(f"   [ERROR] Error loading barangays: {e}")
        else:
            print(f"   [SUCCESS] Found {barangay_count} existing barangays")
        
        print("\n3. Checking if admin user exists...")
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("   Creating admin user...")
            try:
                admin = User(
                    username='admin',
                    email='admin@nabua.gov.ph',
                    full_name='System Administrator',
                    phone='+63-999-000-0001',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("   [SUCCESS] Admin user created successfully")
                print("   Username: admin")
                print("   Password: admin123")
            except Exception as e:
                print(f"   [ERROR] Error creating admin user: {e}")
        else:
            print("   [SUCCESS] Admin user already exists")
        
        print("\n4. Verifying database...")
        user_count = User.query.count()
        waste_count = WasteItem.query.count()
        print(f"   Users: {user_count}")
        print(f"   Barangays: {barangay_count}")
        print(f"   Waste Items: {waste_count}")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Database initialization complete!")
        print("=" * 60)
        print("\nYou can now access the application.")
        print("Default login:")
        print("  Username: admin")
        print("  Password: admin123")
        print("=" * 60)
        
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    print("\nMake sure you're in the correct directory and all dependencies are installed.")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
