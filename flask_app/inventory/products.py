"""Inventory blueprint (migrated from the ``products`` Django app)."""

from datetime import datetime, timedelta
from decimal import Decimal

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from .extensions import db
from .forms import (
    validate_category,
    validate_product,
    validate_stock_adjustment,
)
from .models import (
    MOVEMENT_TYPES,
    Category,
    Product,
    StockMovement,
    utcnow,
)
from .utils import edit_required

products_bp = Blueprint("products", __name__)


def _parse_date(value):
    """Accept YYYY-MM-DD (and a couple of common fallbacks)."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _calendar_months_ago(months):
    """First day of the month ``months - 1`` months before the current month.

    A true calendar offset rather than ``months * 30`` days, so the reported
    window lines up with the month buckets it feeds.
    """
    today = utcnow()
    year, month = today.year, today.month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@products_bp.route("/")
@login_required
def dashboard():
    products = Product.query.all()

    total_products = len(products)
    total_stock_value = sum((p.stock_value for p in products), Decimal("0.00"))

    low_stock_products = [p for p in products if p.quantity > 0 and p.is_low_stock]
    out_of_stock = [p for p in products if p.quantity == 0]

    recent_movements = (
        StockMovement.query.order_by(StockMovement.created_at.desc()).limit(10).all()
    )

    category_stats = sorted(
        Category.query.all(), key=lambda c: c.total_value, reverse=True
    )

    return render_template(
        "products/dashboard.html",
        total_products=total_products,
        total_stock_value=total_stock_value,
        low_stock_count=len(low_stock_products),
        out_of_stock_count=len(out_of_stock),
        low_stock_products=low_stock_products[:5],
        recent_movements=recent_movements,
        category_stats=category_stats,
    )


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

@products_bp.route("/categories/")
@login_required
def category_list():
    categories = sorted(Category.query.all(), key=lambda c: c.name.lower())
    return render_template("products/category_list.html", categories=categories)


@products_bp.route("/categories/create/", methods=["GET", "POST"])
@edit_required
def category_create():
    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_category(request.form)
        if not errors:
            db.session.add(
                Category(
                    name=cleaned["name"],
                    description=cleaned["description"] or None,
                )
            )
            db.session.commit()
            flash("Category created successfully!", "success")
            return redirect(url_for("products.category_list"))

    return render_template(
        "products/category_form.html",
        title="Create Category",
        category=None,
        errors=errors,
    )


@products_bp.route("/categories/<int:pk>/edit/", methods=["GET", "POST"])
@edit_required
def category_edit(pk):
    category = db.session.get(Category, pk)
    if category is None:
        abort(404)

    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_category(request.form, instance=category)
        if not errors:
            category.name = cleaned["name"]
            category.description = cleaned["description"] or None
            db.session.commit()
            flash("Category updated successfully!", "success")
            return redirect(url_for("products.category_list"))

    return render_template(
        "products/category_form.html",
        title=f"Edit Category: {category.name}",
        category=category,
        errors=errors,
    )


@products_bp.route("/categories/<int:pk>/delete/", methods=["GET", "POST"])
@login_required
def category_delete(pk):
    if not current_user.can_delete:
        flash("You do not have permission to delete categories.", "danger")
        return redirect(url_for("products.category_list"))

    category = db.session.get(Category, pk)
    if category is None:
        abort(404)

    if request.method == "POST":
        name = category.name
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{name}" deleted successfully!', "success")
        return redirect(url_for("products.category_list"))

    return render_template(
        "products/category_confirm_delete.html", category=category
    )


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@products_bp.route("/products/")
@login_required
def product_list():
    query = (request.args.get("q") or "").strip()
    category_id = request.args.get("category") or ""
    status = request.args.get("status") or ""
    stock_filter = request.args.get("stock") or ""

    products = Product.query

    if query:
        like = f"%{query}%"
        products = products.filter(
            db.or_(
                Product.name.ilike(like),
                Product.sku.ilike(like),
                Product.description.ilike(like),
            )
        )
    if category_id:
        try:
            products = products.filter(Product.category_id == int(category_id))
        except ValueError:
            category_id = ""
    if status:
        products = products.filter(Product.status == status)
    if stock_filter == "low":
        products = products.filter(
            Product.quantity <= Product.minimum_stock, Product.quantity > 0
        )
    elif stock_filter == "out":
        products = products.filter(Product.quantity == 0)
    elif stock_filter == "in_stock":
        products = products.filter(Product.quantity > Product.minimum_stock)

    products = products.order_by(Product.name).all()
    total_stock_value = sum((p.stock_value for p in products), Decimal("0.00"))

    return render_template(
        "products/product_list.html",
        products=products,
        categories=Category.query.order_by(Category.name).all(),
        query=query,
        selected_category=category_id,
        selected_status=status,
        selected_stock=stock_filter,
        total_stock_value=total_stock_value,
    )


@products_bp.route("/products/<int:pk>/")
@login_required
def product_detail(pk):
    product = db.session.get(Product, pk)
    if product is None:
        abort(404)

    movements = (
        StockMovement.query.filter_by(product_id=product.id)
        .order_by(StockMovement.created_at.desc())
        .limit(20)
        .all()
    )
    return render_template(
        "products/product_detail.html",
        product=product,
        movements=movements,
        can_edit=current_user.can_edit,
    )


@products_bp.route("/products/create/", methods=["GET", "POST"])
@edit_required
def product_create():
    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_product(request.form)
        if not errors:
            product = Product(
                name=cleaned["name"],
                sku=cleaned["sku"],
                description=cleaned["description"] or None,
                category_id=cleaned["category_id"],
                price=cleaned["price"],
                quantity=cleaned["quantity"],
                minimum_stock=cleaned["minimum_stock"],
                status=cleaned["status"],
                created_by=current_user,
            )
            db.session.add(product)
            db.session.commit()
            flash(f'Product "{product.name}" created successfully!', "success")
            return redirect(url_for("products.product_detail", pk=product.id))

    return render_template(
        "products/product_form.html",
        title="Add New Product",
        product=None,
        categories=Category.query.order_by(Category.name).all(),
        errors=errors,
    )


@products_bp.route("/products/<int:pk>/edit/", methods=["GET", "POST"])
@edit_required
def product_edit(pk):
    product = db.session.get(Product, pk)
    if product is None:
        abort(404)

    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_product(request.form, instance=product)
        if not errors:
            product.name = cleaned["name"]
            product.sku = cleaned["sku"]
            product.description = cleaned["description"] or None
            product.category_id = cleaned["category_id"]
            product.price = cleaned["price"]
            product.quantity = cleaned["quantity"]
            product.minimum_stock = cleaned["minimum_stock"]
            product.status = cleaned["status"]
            db.session.commit()
            flash(f'Product "{product.name}" updated successfully!', "success")
            return redirect(url_for("products.product_detail", pk=product.id))

    return render_template(
        "products/product_form.html",
        title=f"Edit Product: {product.name}",
        product=product,
        categories=Category.query.order_by(Category.name).all(),
        errors=errors,
    )


@products_bp.route("/products/<int:pk>/delete/", methods=["GET", "POST"])
@login_required
def product_delete(pk):
    if not current_user.can_delete:
        flash("You do not have permission to delete products.", "danger")
        return redirect(url_for("products.product_list"))

    product = db.session.get(Product, pk)
    if product is None:
        abort(404)

    if request.method == "POST":
        name = product.name
        db.session.delete(product)
        db.session.commit()
        flash(f'Product "{name}" deleted successfully!', "success")
        return redirect(url_for("products.product_list"))

    return render_template("products/product_confirm_delete.html", product=product)


# ---------------------------------------------------------------------------
# Stock management
# ---------------------------------------------------------------------------

@products_bp.route("/products/<int:pk>/stock/", methods=["GET", "POST"])
@edit_required
def stock_adjust(pk):
    product = db.session.get(Product, pk)
    if product is None:
        abort(404)

    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_stock_adjustment(request.form)
        if not errors:
            adjustment_type = cleaned["adjustment_type"]
            quantity = cleaned["quantity"]
            notes = cleaned["notes"]
            try:
                if adjustment_type == "add":
                    product.add_stock(quantity, user=current_user, notes=notes)
                    flash(f"Added {quantity} units to {product.name}", "success")
                elif adjustment_type == "remove":
                    product.remove_stock(quantity, user=current_user, notes=notes)
                    flash(f"Removed {quantity} units from {product.name}", "success")
                else:  # set
                    old_quantity = product.quantity
                    product.quantity = quantity
                    db.session.add(
                        StockMovement(
                            product=product,
                            movement_type="adjustment",
                            quantity=abs(quantity - old_quantity),
                            reference=(
                                f"Stock adjusted from {old_quantity} to {quantity}"
                            ),
                            notes=notes,
                            performed_by=current_user,
                        )
                    )
                    flash(f"Set {product.name} quantity to {quantity}", "success")

                db.session.commit()
                return redirect(url_for("products.product_detail", pk=product.id))
            except ValueError as exc:
                db.session.rollback()
                errors["quantity"] = str(exc)

    return render_template(
        "products/stock_adjust.html", product=product, errors=errors
    )


@products_bp.route("/movements/")
@login_required
def stock_movements():
    product_query = (request.args.get("product") or "").strip()
    movement_type = request.args.get("movement_type") or ""
    date_from = request.args.get("date_from") or ""
    date_to = request.args.get("date_to") or ""

    movements = StockMovement.query

    if product_query:
        like = f"%{product_query}%"
        movements = movements.join(Product).filter(
            db.or_(Product.name.ilike(like), Product.sku.ilike(like))
        )
    if movement_type:
        movements = movements.filter(StockMovement.movement_type == movement_type)
    if date_from:
        parsed = _parse_date(date_from)
        if parsed:
            movements = movements.filter(StockMovement.created_at >= parsed)
    if date_to:
        parsed = _parse_date(date_to)
        if parsed:
            movements = movements.filter(
                StockMovement.created_at < parsed + timedelta(days=1)
            )

    movements = movements.order_by(StockMovement.created_at.desc()).limit(100).all()

    filters = {
        "product": product_query,
        "movement_type": movement_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    return render_template(
        "products/stock_movements.html",
        movements=movements,
        movement_types=MOVEMENT_TYPES,
        filters=filters,
    )


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------

@products_bp.route("/reports/low-stock/")
@login_required
def low_stock_report():
    products = (
        Product.query.filter(
            Product.quantity <= Product.minimum_stock,
            Product.status == "active",
        )
        .order_by(Product.quantity)
        .all()
    )

    out_of_stock = [p for p in products if p.quantity == 0]
    low_stock = [p for p in products if p.quantity > 0]

    restock_value = Decimal("0.00")
    for product in low_stock:
        restock_value += product.price * (product.minimum_stock - product.quantity)
    for product in out_of_stock:
        restock_value += product.price * product.minimum_stock

    return render_template(
        "products/low_stock_report.html",
        products=products,
        out_of_stock_count=len(out_of_stock),
        low_count=len(low_stock),
        restock_value=restock_value,
    )


@products_bp.route("/reports/monthly/")
@login_required
def monthly_report():
    try:
        months = max(1, min(int(request.args.get("months", 12)), 60))
    except (TypeError, ValueError):
        months = 12

    start_date = _calendar_months_ago(months)

    raw = (
        StockMovement.query.filter(StockMovement.created_at >= start_date)
        .order_by(StockMovement.created_at)
        .all()
    )

    buckets = {}
    for movement in raw:
        key = movement.created_at.strftime("%Y-%m")
        bucket = buckets.setdefault(
            key,
            {
                "month": movement.created_at,
                "in_quantity": 0,
                "out_quantity": 0,
                "adjustment_quantity": 0,
                "in_count": 0,
                "out_count": 0,
            },
        )
        if movement.movement_type == "in":
            bucket["in_quantity"] += movement.quantity
            bucket["in_count"] += 1
        elif movement.movement_type == "out":
            bucket["out_quantity"] += movement.quantity
            bucket["out_count"] += 1
        elif movement.movement_type == "adjustment":
            bucket["adjustment_quantity"] += movement.quantity

    monthly_data = [buckets[key] for key in sorted(buckets.keys(), reverse=True)]
    for bucket in monthly_data:
        # Adjustments are recorded as a magnitude (positive) so they are shown
        # separately rather than folded into the net in/out figure.
        bucket["net_change"] = bucket["in_quantity"] - bucket["out_quantity"]

    total_in = sum(m["in_quantity"] for m in monthly_data)
    total_out = sum(m["out_quantity"] for m in monthly_data)
    total_transactions = sum(m["in_count"] + m["out_count"] for m in monthly_data)

    return render_template(
        "products/monthly_report.html",
        monthly_data=monthly_data,
        total_in=total_in,
        total_out=total_out,
        total_transactions=total_transactions,
        months=months,
    )


@products_bp.route("/reports/valuation/")
@login_required
def valuation_report():
    categories = sorted(
        Category.query.all(), key=lambda c: c.total_value, reverse=True
    )
    total_value = sum((c.total_value for c in categories), Decimal("0.00"))

    return render_template(
        "products/valuation_report.html",
        categories=categories,
        total_value=total_value,
    )


# ---------------------------------------------------------------------------
# JSON APIs
# ---------------------------------------------------------------------------

@products_bp.route("/api/products/search/")
@login_required
def product_search_api():
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify({"products": []})

    like = f"%{query}%"
    products = (
        Product.query.filter(
            db.or_(Product.name.ilike(like), Product.sku.ilike(like)),
            Product.status == "active",
        )
        .limit(10)
        .all()
    )

    return jsonify(
        {
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "sku": p.sku,
                    "price": str(p.price),
                    "quantity": p.quantity,
                }
                for p in products
            ]
        }
    )


@products_bp.route("/api/dashboard/stats/")
@login_required
def dashboard_stats_api():
    products = Product.query.all()
    total_stock_value = sum((p.stock_value for p in products), Decimal("0.00"))

    return jsonify(
        {
            "total_products": len(products),
            "total_stock_value": str(total_stock_value),
            "low_stock_count": len(
                [p for p in products if p.quantity > 0 and p.is_low_stock]
            ),
            "out_of_stock_count": len([p for p in products if p.quantity == 0]),
        }
    )
