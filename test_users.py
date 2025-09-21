#!/usr/bin/env python3
"""
Test script to check user authentication
"""
from app import app, db, User

def test_users():
    with app.app_context():
        print("🔍 Testing User Authentication")
        print("=" * 50)
        
        # Check all users
        users = User.query.all()
        print(f"Total users in database: {len(users)}")
        print("\nUsers found:")
        for user in users:
            print(f"- Username: {user.username}")
            print(f"  Role: {user.role}")
            print(f"  Full Name: {user.full_name}")
            print(f"  Email: {user.email}")
            print(f"  Password Set: {user.password_hash is not None}")
            print()
        
        # Test admin login
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("🔐 Testing Admin Authentication:")
            print(f"Admin user exists: {admin is not None}")
            print(f"Password check (admin123): {admin.check_password('admin123')}")
            print(f"Password check (wrong): {admin.check_password('wrong')}")
        else:
            print("❌ Admin user not found!")
        
        print("\n" + "=" * 50)
        print("✅ Test completed!")

if __name__ == '__main__':
    test_users()
