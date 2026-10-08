"""
SQLAlchemy models for the Inventory Management System.

These mirror the original Django models:

    accounts.models.UserProfile  -> User (role lives directly on the user)
    products.models.Category     -> Category
    products.models.Product      -> Product
    products.models.StockMovement -> StockMovement
"""

from datetime import datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def utcnow():
    """Naive UTC timestamp (matches Django's USE_TZ = False style storage).

    Uses the timezone-aware form rather than the deprecated
    ``datetime.utcnow()`` so it stays warning-free on Python 3.12+.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Choices / labels
# ---------------------------------------------------------------------------

ROLE_CHOICES = [
    ("admin", "Administrator"),
    ("staff", "Staff Member"),
    ("viewer", "Read-Only Viewer"),
]
ROLE_LABELS = dict(ROLE_CHOICES)

STATUS_CHOICES = [
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("discontinued", "Discontinued"),
]
STATUS_LABELS = dict(STATUS_CHOICES)

MOVEMENT_TYPES = [
    ("in", "Stock In"),
    ("out", "Stock Out"),
    ("adjustment", "Adjustment"),
    ("return", "Return"),
]
MOVEMENT_LABELS = dict(MOVEMENT_TYPES)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(UserMixin, db.Model):
    """Application user with role-based access control."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    first_name = db.Column(db.String(30), default="")
    last_name = db.Column(db.String(30), default="")
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="staff", nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    # NOTE: this column intentionally shadows UserMixin.is_active so accounts
    # can be deactivated; Flask-Login refuses to log in inactive users.
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    date_joined = db.Column(db.DateTime, default=utcnow, nullable=False)

    # ---- password helpers -------------------------------------------------
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    # ---- role helpers -----------------------------------------------------
    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)

    def get_role_display(self):
        return self.role_label

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_staff_member(self):
        return self.role in ("admin", "staff")

    @property
    def can_edit(self):
        return self.role in ("admin", "staff")

    @property
    def can_delete(self):
        return self.role == "admin"

    @property
    def profile(self):
        """Kept so templates written for Django (``user.profile.role``) work."""
        return self

    # ---- display helpers --------------------------------------------------
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    @property
    def display_name(self):
        return self.full_name or self.username

    @property
    def avatar_initial(self):
        return (self.first_name or self.username or "?")[:1].upper()

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class Category(db.Model):
    """Product category used to organise inventory."""

    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    products = db.relationship("Product", back_populates="category")

    # ---- aggregates (computed in Python from the loaded relationship) -----
    @property
    def num_products(self):
        return len(self.products)

    @property
    def total_quantity(self):
        return sum(p.quantity for p in self.products)

    @property
    def total_value(self):
        return sum(
            ((p.price or Decimal("0.00")) * p.quantity for p in self.products),
            Decimal("0.00"),
        )

    def __repr__(self):
        return f"<Category {self.name}>"


# ---------------------------------------------------------------------------
# Product
# ---------------------------------------------------------------------------

class Product(db.Model):
    """Core inventory item with stock tracking."""

    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.01"))
    quantity = db.Column(db.Integer, nullable=False, default=0)
    minimum_stock = db.Column(db.Integer, nullable=False, default=10)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    category = db.relationship("Category", back_populates="products")
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    movements = db.relationship(
        "StockMovement",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="StockMovement.created_at.desc()",
    )

    __table_args__ = (
        db.Index("ix_products_category_status", "category_id", "status"),
    )

    # ---- computed properties ---------------------------------------------
    @property
    def is_low_stock(self):
        return self.quantity <= self.minimum_stock

    @property
    def stock_status(self):
        if self.quantity == 0:
            return "out_of_stock"
        if self.is_low_stock:
            return "low_stock"
        return "in_stock"

    @property
    def stock_value(self):
        return (self.price or Decimal("0.00")) * self.quantity

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)

    def get_status_display(self):
        return self.status_label

    # ---- stock operations (record an audit trail) -------------------------
    def add_stock(self, quantity, user=None, notes=""):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        self.quantity += quantity
        db.session.add(
            StockMovement(
                product=self,
                movement_type="in",
                quantity=quantity,
                reference=f"Stock added: {quantity} units",
                notes=notes,
                performed_by=user,
            )
        )

    def remove_stock(self, quantity, user=None, notes=""):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self.quantity:
            raise ValueError(f"Insufficient stock. Available: {self.quantity}")
        self.quantity -= quantity
        db.session.add(
            StockMovement(
                product=self,
                movement_type="out",
                quantity=quantity,
                reference=f"Stock removed: {quantity} units",
                notes=notes,
                performed_by=user,
            )
        )

    def __repr__(self):
        return f"<Product {self.name} ({self.sku})>"


# ---------------------------------------------------------------------------
# StockMovement
# ---------------------------------------------------------------------------

class StockMovement(db.Model):
    """Audit trail entry for every stock change."""

    __tablename__ = "stock_movements"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    reference = db.Column(db.String(200))
    notes = db.Column(db.Text)
    performed_by_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=utcnow, index=True)

    product = db.relationship("Product", back_populates="movements")
    performed_by = db.relationship("User", foreign_keys=[performed_by_id])

    @property
    def movement_type_label(self):
        return MOVEMENT_LABELS.get(self.movement_type, self.movement_type)

    def get_movement_type_display(self):
        return self.movement_type_label

    @property
    def performed_by_name(self):
        return self.performed_by.display_name if self.performed_by else "-"

    def __repr__(self):
        return (
            f"<StockMovement {self.movement_type} "
            f"{self.product_id} ({self.quantity})>"
        )
