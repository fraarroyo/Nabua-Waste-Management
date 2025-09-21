#!/usr/bin/env python3
"""
Script to create default admin and collector accounts
"""
from app import app, db, User
from datetime import datetime

def create_default_users():
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        # Check if admin user already exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@nabua.gov.ph',
                full_name='System Administrator',
                phone='+63-999-000-0001',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Admin account created successfully!")
        else:
            print("ℹ️  Admin account already exists")
        
        # Check if collector user already exists
        collector_user = User.query.filter_by(username='collector').first()
        if not collector_user:
            collector = User(
                username='collector',
                email='collector@nabua.gov.ph',
                full_name='Collection Team Member',
                phone='+63-999-000-0002',
                role='collector'
            )
            collector.set_password('collector123')
            db.session.add(collector)
            print("✅ Collector account created successfully!")
        else:
            print("ℹ️  Collector account already exists")
        
        # Create additional demo accounts
        demo_admin = User.query.filter_by(username='demo_admin').first()
        if not demo_admin:
            demo_admin = User(
                username='demo_admin',
                email='demo.admin@nabua.gov.ph',
                full_name='Demo Administrator',
                phone='+63-999-000-0003',
                role='admin'
            )
            demo_admin.set_password('demo123')
            db.session.add(demo_admin)
            print("✅ Demo admin account created successfully!")
        else:
            print("ℹ️  Demo admin account already exists")
        
        demo_collector = User.query.filter_by(username='demo_collector').first()
        if not demo_collector:
            demo_collector = User(
                username='demo_collector',
                email='demo.collector@nabua.gov.ph',
                full_name='Demo Collector',
                phone='+63-999-000-0004',
                role='collector'
            )
            demo_collector.set_password('demo123')
            db.session.add(demo_collector)
            print("✅ Demo collector account created successfully!")
        else:
            print("ℹ️  Demo collector account already exists")
        
        # Commit all changes
        db.session.commit()
        
        print("\n" + "="*60)
        print("🎉 DEFAULT USER ACCOUNTS CREATED")
        print("="*60)
        print("Admin Accounts:")
        print("  Username: admin        | Password: admin123")
        print("  Username: demo_admin   | Password: demo123")
        print("\nCollector Accounts:")
        print("  Username: collector    | Password: collector123")
        print("  Username: demo_collector| Password: demo123")
        print("="*60)
        print("You can now log in to the system!")
        print("="*60)

if __name__ == '__main__':
    create_default_users()
