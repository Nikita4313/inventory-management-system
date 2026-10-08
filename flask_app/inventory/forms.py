"""
Lightweight form validation.

The original project relied on Django forms. Instead of adding WTForms, the
validation is implemented as small pure functions returning
``(cleaned_values, errors)`` so the hand-written templates stay close to the
originals.
"""

import re
from decimal import Decimal, InvalidOperation

from .extensions import db
from .models import MOVEMENT_TYPES, STATUS_CHOICES, Category, Product, User

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_RE = re.compile(r"^[\w.@+-]+$")


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------

def _text(form, key):
    value = form.get(key)
    return value.strip() if isinstance(value, str) else ""


def _int(value, default=None):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def _decimal(value, default=None):
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# registration / account
# ---------------------------------------------------------------------------

def validate_registration(form):
    errors = {}
    username = _text(form, "username")
    email = _text(form, "email")
    first_name = _text(form, "first_name")
    last_name = _text(form, "last_name")
    password1 = form.get("password1") or ""
    password2 = form.get("password2") or ""

    if not username:
        errors["username"] = "Username is required."
    elif len(username) > 150:
        errors["username"] = "Username must be 150 characters or fewer."
    elif not USERNAME_RE.match(username):
        errors["username"] = (
            "Enter a valid username (letters, digits and @/./+/-/_ only)."
        )
    elif User.query.filter_by(username=username).first():
        errors["username"] = "This username is already taken."

    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    elif User.query.filter_by(email=email).first():
        errors["email"] = "This email is already registered."

    if not first_name:
        errors["first_name"] = "First name is required."
    if not last_name:
        errors["last_name"] = "Last name is required."

    if not password1:
        errors["password1"] = "Password is required."
    elif len(password1) < 8:
        errors["password1"] = "Password must be at least 8 characters."

    if not password2:
        errors["password2"] = "Please confirm your password."
    elif password1 and password1 != password2:
        errors["password2"] = "The two password fields did not match."

    cleaned = {
        "username": username,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password1": password1,
    }
    return cleaned, errors


def validate_profile(form, instance=None):
    errors = {}
    first_name = _text(form, "first_name")
    last_name = _text(form, "last_name")
    email = _text(form, "email")
    phone = _text(form, "phone")
    department = _text(form, "department")

    if not email:
        errors["email"] = "Email is required."
    elif not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    else:
        query = User.query.filter(db.func.lower(User.email) == email.lower())
        if instance is not None:
            query = query.filter(User.id != instance.id)
        if query.first():
            errors["email"] = "This email is already in use by another account."

    cleaned = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone,
        "department": department,
    }
    return cleaned, errors


# ---------------------------------------------------------------------------
# categories
# ---------------------------------------------------------------------------

def validate_category(form, instance=None):
    errors = {}
    name = _text(form, "name")
    description = (form.get("description") or "").strip()

    if not name:
        errors["name"] = "Category name is required."
    elif len(name) > 100:
        errors["name"] = "Category name must be 100 characters or fewer."
    else:
        query = Category.query.filter(db.func.lower(Category.name) == name.lower())
        if instance is not None:
            query = query.filter(Category.id != instance.id)
        if query.first():
            errors["name"] = "A category with this name already exists."

    return {"name": name, "description": description}, errors


# ---------------------------------------------------------------------------
# products
# ---------------------------------------------------------------------------

def validate_product(form, instance=None):
    errors = {}
    name = _text(form, "name")
    sku = _text(form, "sku")
    description = (form.get("description") or "").strip()
    status = _text(form, "status") or "active"
    category_id = _int(form.get("category"))
    price = _decimal(form.get("price"))
    quantity = _int(form.get("quantity"))
    minimum_stock = _int(form.get("minimum_stock"))

    if not name:
        errors["name"] = "Product name is required."
    elif len(name) > 200:
        errors["name"] = "Product name must be 200 characters or fewer."

    if not sku:
        errors["sku"] = "SKU is required."
    elif len(sku) > 50:
        errors["sku"] = "SKU must be 50 characters or fewer."
    else:
        query = Product.query.filter(db.func.lower(Product.sku) == sku.lower())
        if instance is not None:
            query = query.filter(Product.id != instance.id)
        if query.first():
            errors["sku"] = "A product with this SKU already exists."

    if price is None:
        errors["price"] = "Enter a valid price."
    elif price <= Decimal("0.00"):
        errors["price"] = "Price must be greater than zero."

    if quantity is None:
        errors["quantity"] = "Enter a valid quantity."
    elif quantity < 0:
        errors["quantity"] = "Quantity cannot be negative."

    if minimum_stock is None:
        errors["minimum_stock"] = "Enter a valid minimum stock level."
    elif minimum_stock < 0:
        errors["minimum_stock"] = "Minimum stock cannot be negative."

    if status not in dict(STATUS_CHOICES):
        errors["status"] = "Select a valid status."

    if category_id and not db.session.get(Category, category_id):
        errors["category"] = "Select a valid category."

    cleaned = {
        "name": name,
        "sku": sku,
        "description": description,
        "status": status,
        "category_id": category_id or None,
        "price": price,
        "quantity": quantity,
        "minimum_stock": minimum_stock,
    }
    return cleaned, errors


# ---------------------------------------------------------------------------
# stock adjustment
# ---------------------------------------------------------------------------

def validate_stock_adjustment(form):
    errors = {}
    adjustment_type = _text(form, "adjustment_type")
    quantity = _int(form.get("quantity"))
    notes = (form.get("notes") or "").strip()

    if adjustment_type not in ("add", "remove", "set"):
        errors["adjustment_type"] = "Select a valid adjustment type."

    if quantity is None:
        errors["quantity"] = "Enter a valid quantity."
    elif adjustment_type in ("add", "remove") and quantity < 1:
        errors["quantity"] = "Quantity must be at least 1 for add/remove operations."
    elif adjustment_type == "set" and quantity < 0:
        errors["quantity"] = "Quantity cannot be negative."

    return {
        "adjustment_type": adjustment_type,
        "quantity": quantity,
        "notes": notes,
    }, errors
