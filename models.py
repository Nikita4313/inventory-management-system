"""
SQLAlchemy models for inventory management
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model with authentication"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = db.relationship('UserProfile', uselist=False, backref='user', cascade='all, delete-orphan')
    created_products = db.relationship('Product', backref='created_by', foreign_keys='Product.created_by_id')
    stock_movements = db.relationship('StockMovement', backref='performed_by')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)

    @property
    def date_joined(self):
        return self.created_at

    def get_full_name(self):
        return f'{self.first_name or ""} {self.last_name or ""}'.strip()

    @property
    def role_label(self):
        return 'Admin' if self.profile and self.profile.role == 'admin' else 'User'

    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    """Extended user profile with role-based access control"""
    __tablename__ = 'user_profile'
    
    ROLE_CHOICES = {
        'admin': 'Administrator',
        'staff': 'Staff Member',
        'viewer': 'Read-Only Viewer',
    }
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    role = db.Column(db.String(20), default='staff', nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_staff_member(self):
        return self.role in ['admin', 'staff']
    
    @property
    def can_edit(self):
        return self.role in ['admin', 'staff']
    
    @property
    def can_delete(self):
        return self.role == 'admin'
    
    def get_role_display(self):
        return self.ROLE_CHOICES.get(self.role, self.role)
    
    def __repr__(self):
        return f'<UserProfile {self.user.username} - {self.role}>'


class Category(db.Model):
    """Product category for organizing inventory"""
    __tablename__ = 'category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='category', cascade='all, delete-orphan')
    
    def __repr__(self):
        return self.name


class Product(db.Model):
    """Core inventory item with stock tracking"""
    __tablename__ = 'product'
    
    STATUS_CHOICES = {
        'active': 'Active',
        'inactive': 'Inactive',
        'discontinued': 'Discontinued',
    }
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, default=0, nullable=False)
    minimum_stock = db.Column(db.Integer, default=10, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    movements = db.relationship('StockMovement', backref='product', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'{self.name} ({self.sku})'
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock
    
    @property
    def stock_status(self):
        if self.quantity == 0:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        return 'in_stock'
    
    @property
    def stock_value(self):
        return Decimal(self.price) * Decimal(self.quantity)
    
    def get_status_display(self):
        return self.STATUS_CHOICES.get(self.status, self.status)
    
    def add_stock(self, quantity, user=None, notes=''):
        """Add stock and record the movement"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        self.quantity += quantity
        db.session.commit()
        
        StockMovement.create(
            product_id=self.id,
            movement_type='in',
            quantity=quantity,
            reference=f"Stock added: {quantity} units",
            notes=notes,
            performed_by_id=user.id if user else None
        )
    
    def remove_stock(self, quantity, user=None, notes=''):
        """Remove stock and record the movement"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self.quantity:
            raise ValueError(f"Insufficient stock. Available: {self.quantity}")
        
        self.quantity -= quantity
        db.session.commit()
        
        StockMovement.create(
            product_id=self.id,
            movement_type='out',
            quantity=quantity,
            reference=f"Stock removed: {quantity} units",
            notes=notes,
            performed_by_id=user.id if user else None
        )


class StockMovement(db.Model):
    """Audit trail for all stock changes"""
    __tablename__ = 'stock_movement'
    
    MOVEMENT_TYPES = {
        'in': 'Stock In',
        'out': 'Stock Out',
        'adjustment': 'Adjustment',
        'return': 'Return',
    }
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    performed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'{self.get_movement_type_display()} - {self.product.name} ({self.quantity})'
    
    def get_movement_type_display(self):
        return self.MOVEMENT_TYPES.get(self.movement_type, self.movement_type)
    
    @staticmethod
    def create(product_id, movement_type, quantity, reference='', notes='', performed_by_id=None):
        """Factory method to create a stock movement"""
        movement = StockMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity,
            reference=reference,
            notes=notes,
            performed_by_id=performed_by_id
        )
        db.session.add(movement)
        db.session.commit()
        return movement
