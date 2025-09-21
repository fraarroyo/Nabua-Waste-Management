#!/usr/bin/env python3
"""
Script to create barangay user accounts for each barangay in Nabua
"""
from app import app, db, User, Barangay
from datetime import datetime

def create_barangay_users():
    with app.app_context():
        # Get all barangays in Nabua
        nabua_barangays = Barangay.query.join(User).filter(User.role == 'admin').first()
        if not nabua_barangays:
            # Get barangays from the first municipality (should be Nabua)
            nabua_barangays = Barangay.query.limit(10).all()  # Get first 10 for demo
        
        print(f"Creating barangay user accounts for {len(nabua_barangays)} barangays...")
        
        created_count = 0
        for i, barangay in enumerate(nabua_barangays):
            # Create username from barangay name
            username = barangay.name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
            username = f"brgy_{username[:20]}"  # Limit length and add prefix
            
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"ℹ️  User {username} already exists")
                continue
            
            # Create barangay user
            user = User(
                username=username,
                email=f"{username}@nabua.gov.ph",
                full_name=f"Barangay {barangay.name} Representative",
                phone=f"+63-999-{i+1:03d}-{i+1:04d}",
                role='barangay'
            )
            user.set_password('barangay123')
            
            db.session.add(user)
            created_count += 1
            print(f"✅ Created user: {username} for {barangay.name}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n🎉 Created {created_count} barangay user accounts!")
        print("="*60)
        print("BARANGAY USER ACCOUNTS CREATED")
        print("="*60)
        print("All barangay accounts use password: barangay123")
        print("Usernames follow pattern: brgy_[barangay_name]")
        print("="*60)
        print("Example accounts:")
        print("  Username: brgy_poblacion")
        print("  Username: brgy_san_antonio")
        print("  Username: brgy_san_esteban")
        print("  Password: barangay123")
        print("="*60)

if __name__ == '__main__':
    create_barangay_users()
