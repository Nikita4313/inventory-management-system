#!/usr/bin/env python
"""
Setup script for initializing the Inventory Management System (Flask)
"""
import os
import sys
from app import create_app, db
from models import User, UserProfile


def setup_database():
    """Create database tables"""
    print("Initializing database...")
    app = create_app()
    with app.app_context():
        db.create_all()
        print("✓ Database initialized successfully")


def create_admin_user():
    """Create an admin user"""
    app = create_app()
    with app.app_context():
        print("\n" + "="*50)
        print("Creating Admin User")
        print("="*50)
        
        username = input("Enter admin username: ").strip()
        email = input("Enter admin email: ").strip()
        password = input("Enter admin password: ").strip()
        first_name = input("Enter admin first name (optional): ").strip() or "Admin"
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            print("✗ Username already exists!")
            return False
        
        if User.query.filter_by(email=email).first():
            print("✗ Email already exists!")
            return False
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Create profile with admin role
        profile = UserProfile(user_id=user.id, role='admin')
        db.session.add(profile)
        db.session.commit()
        
        print(f"\n✓ Admin user '{username}' created successfully!")
        return True


def create_sample_data():
    """Create sample categories and products"""
    app = create_app()
    with app.app_context():
        from models import Category, Product
        
        # Check if data already exists
        if Category.query.first():
            print("\n⚠ Sample data already exists. Skipping...")
            return
        
        print("\nCreating sample categories...")
        
        categories = [
            Category(name='Electronics', description='Electronic devices and equipment'),
            Category(name='Office Supplies', description='Office and stationery supplies'),
            Category(name='Furniture', description='Office furniture'),
            Category(name='Tools', description='Hand and power tools'),
        ]
        
        for cat in categories:
            db.session.add(cat)
        
        db.session.commit()
        print("✓ Sample categories created")
        
        print("Creating sample products...")
        
        products_data = [
            ('LAPTOP-001', 'Dell Laptop', 999.99, 5, 2, 'Electronics'),
            ('MOUSE-001', 'Wireless Mouse', 29.99, 50, 10, 'Electronics'),
            ('DESK-001', 'Office Desk', 299.99, 10, 3, 'Furniture'),
            ('CHAIR-001', 'Office Chair', 199.99, 15, 4, 'Furniture'),
            ('PAPER-001', 'A4 Paper (500 sheets)', 5.99, 200, 50, 'Office Supplies'),
            ('DRILL-001', 'Power Drill', 79.99, 8, 2, 'Tools'),
        ]
        
        for sku, name, price, quantity, min_stock, category_name in products_data:
            category = Category.query.filter_by(name=category_name).first()
            product = Product(
                sku=sku,
                name=name,
                price=price,
                quantity=quantity,
                minimum_stock=min_stock,
                category=category,
                status='active'
            )
            db.session.add(product)
        
        db.session.commit()
        print("✓ Sample products created")


def main():
    """Main setup function"""
    print("\n" + "="*50)
    print("Inventory Management System - Setup")
    print("="*50 + "\n")
    
    # Initialize database
    try:
        setup_database()
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        sys.exit(1)
    
    # Ask to create admin user
    create_admin = input("\nCreate admin user? (y/n): ").lower().strip() == 'y'
    if create_admin:
        try:
            if not create_admin_user():
                sys.exit(1)
        except Exception as e:
            print(f"✗ Error creating admin user: {e}")
            sys.exit(1)
    
    # Ask to create sample data
    create_samples = input("\nCreate sample data? (y/n): ").lower().strip() == 'y'
    if create_samples:
        try:
            create_sample_data()
        except Exception as e:
            print(f"✗ Error creating sample data: {e}")
    
    print("\n" + "="*50)
    print("Setup Complete!")
    print("="*50)
    print("\nTo start the application, run:")
    print("  python run.py")
    print("\nThen visit: http://127.0.0.1:5000")
    print()


if __name__ == '__main__':
    main()
