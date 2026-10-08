"""
Small helpers shared across the application:

* access-control decorators (admin / edit permission)
* Jinja filters that replace Django's ``intcomma``, ``timesince`` and
  ``truncatewords``
* a context processor that injects the current user and the active nav page
"""

from decimal import Decimal
from functools import wraps

from flask import flash, redirect, request, url_for
from flask_login import current_user

from .extensions import db
from .models import Product, utcnow


# ---------------------------------------------------------------------------
# Access control decorators
# ---------------------------------------------------------------------------

def admin_required(view):
    """Allow only users whose role is ``admin``."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(
                url_for("auth.login", next=request.full_path.rstrip("?"))
            )
        if not current_user.is_admin:
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for("products.dashboard"))
        return view(*args, **kwargs)

    return wrapper


def edit_required(view):
    """Allow only users who can modify inventory (admin or staff)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(
                url_for("auth.login", next=request.full_path.rstrip("?"))
            )
        if not current_user.can_edit:
            flash("You do not have permission to perform this action.", "danger")
            return redirect(url_for("products.dashboard"))
        return view(*args, **kwargs)

    return wrapper


# ---------------------------------------------------------------------------
# Jinja filters
# ---------------------------------------------------------------------------

def intcomma(value):
    """Format numbers with thousand separators (Django's ``intcomma``)."""
    if value is None:
        return "0"
    try:
        if isinstance(value, bool):
            return str(value)
        if isinstance(value, int):
            return f"{value:,}"
        if isinstance(value, Decimal):
            return f"{value:,.2f}"
        if isinstance(value, float):
            return f"{value:,.2f}"
        # Strings / other numerics (e.g. raw aggregates)
        return f"{Decimal(str(value)):,.2f}"
    except (ValueError, ArithmeticError):
        return str(value)


def timesince(value):
    """Human readable "time ago" string (simplified Django ``timesince``)."""
    if not value:
        return ""
    if isinstance(value, str):
        return value
    seconds = int((utcnow() - value).total_seconds())
    if seconds < 5:
        return "a few seconds"
    if seconds < 60:
        return f"{seconds} second{'s' if seconds != 1 else ''}"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    days = hours // 24
    if days < 30:
        return f"{days} day{'s' if days != 1 else ''}"
    months = days // 30
    if months < 12:
        return f"{months} month{'s' if months != 1 else ''}"
    years = months // 12
    return f"{years} year{'s' if years != 1 else ''}"


def truncatewords(value, count=10, end="\u2026"):
    """Truncate to ``count`` words (Django's ``truncatewords``)."""
    if not value:
        return value or ""
    words = str(value).split()
    if len(words) <= count:
        return value
    return " ".join(words[:count]) + end


def pluralize(value, singular="", plural="s"):
    """Django's ``pluralize`` for the common case."""
    try:
        return singular if float(value) == 1 else plural
    except (TypeError, ValueError):
        return plural


# ---------------------------------------------------------------------------
# Registration helper
# ---------------------------------------------------------------------------

def register_template_helpers(app):
    """Register custom filters and the global context processor."""

    app.jinja_env.filters["intcomma"] = intcomma
    app.jinja_env.filters["timesince"] = timesince
    app.jinja_env.filters["truncatewords"] = truncatewords
    app.jinja_env.filters["pluralize"] = pluralize

    @app.context_processor
    def inject_globals():
        """Expose the current user and active navigation entry to templates."""
        endpoint = request.endpoint or ""
        active_page = endpoint.split(".")[-1] if endpoint else ""

        low_stock_count = 0
        if current_user.is_authenticated:
            low_stock_count = (
                db.session.query(db.func.count(Product.id))
                .filter(Product.quantity <= Product.minimum_stock)
                .scalar()
                or 0
            )

        return {
            "user": current_user,          # Django-style alias for current_user
            "current_user": current_user,
            "active_page": active_page,    # e.g. 'dashboard', 'product_list'
            "endpoint": endpoint,
            "low_stock_count": low_stock_count,
        }
