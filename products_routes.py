"""
Products routes and utilities for the inventory management application
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
from decimal import Decimal
from models import db, Category, Product, StockMovement, User
from forms import (
    CategoryForm, ProductForm, StockAdjustmentForm, StockMovementFilterForm
)
from auth import user_can_edit, user_can_delete

products_bp = Blueprint('products', __name__)


# ========== Dashboard ==========

@products_bp.route('/')
@products_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with key metrics"""
    products = Product.query.all()
    
    # Key metrics
    total_products = len(products)
    total_stock_value = sum(
        (Decimal(str(p.price)) * Decimal(str(p.quantity)) if p.price else Decimal('0'))
        for p in products
    ) if products else Decimal('0.00')
    
    low_stock_products = [p for p in products if p.quantity <= p.minimum_stock and p.quantity > 0]
    out_of_stock = [p for p in products if p.quantity == 0]
    
    # Recent movements
    recent_movements = StockMovement.query.order_by(StockMovement.created_at.desc()).limit(10).all()
    
    # Category breakdown
    categories = Category.query.all()
    category_stats = []
    for cat in categories:
        products_in_cat = Product.query.filter_by(category_id=cat.id).all()
        num_products = len(products_in_cat)
        total_value = sum(
            (Decimal(str(p.price)) * Decimal(str(p.quantity)) if p.price else Decimal('0'))
            for p in products_in_cat
        ) if products_in_cat else Decimal('0.00')
        category_stats.append({
            'category': cat,
            'num_products': num_products,
            'total_value': total_value
        })
    
    category_stats = sorted(category_stats, key=lambda x: x['total_value'], reverse=True)
    
    return render_template('products/dashboard.html',
        total_products=total_products,
        total_stock_value=total_stock_value,
        low_stock_count=len(low_stock_products),
        out_of_stock_count=len(out_of_stock),
        low_stock_products=low_stock_products[:5],
        out_of_stock_products=out_of_stock[:5],
        recent_movements=recent_movements,
        category_stats=category_stats
    )


# ========== Category CRUD ==========

@products_bp.route('/categories')
@login_required
def category_list():
    """List all categories"""
    categories = Category.query.all()
    
    category_stats = []
    for cat in categories:
        products = Product.query.filter_by(category_id=cat.id).all()
        num_products = len(products)
        total_value = sum(
            (Decimal(str(p.price)) * Decimal(str(p.quantity)) if p.price else Decimal('0'))
            for p in products
        ) if products else Decimal('0.00')
        category_stats.append({
            'category': cat,
            'num_products': num_products,
            'total_value': total_value
        })
    
    return render_template('products/category_list.html', categories=category_stats)


@products_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def category_create():
    """Create a new category"""
    if not user_can_edit(current_user):
        flash('You do not have permission to create categories.', 'error')
        return redirect(url_for('products.category_list'))
    
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data, description=form.description.data)
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('products.category_list'))
    
    return render_template('products/category_form.html', form=form, title='Create Category')


@products_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(category_id):
    """Edit a category"""
    if not user_can_edit(current_user):
        flash('You do not have permission to edit categories.', 'error')
        return redirect(url_for('products.category_list'))
    
    category = Category.query.get_or_404(category_id)
    
    form = CategoryForm()
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()
        
        flash('Category updated successfully!', 'success')
        return redirect(url_for('products.category_list'))
    elif request.method == 'GET':
        form.name.data = category.name
        form.description.data = category.description
    
    return render_template('products/category_form.html', form=form, title=f'Edit Category: {category.name}')


@products_bp.route('/categories/<int:category_id>/delete', methods=['GET', 'POST'])
@login_required
def category_delete(category_id):
    """Delete a category"""
    if not user_can_delete(current_user):
        flash('You do not have permission to delete categories.', 'error')
        return redirect(url_for('products.category_list'))
    
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category_name = category.name
        db.session.delete(category)
        db.session.commit()
        
        flash(f'Category "{category_name}" deleted successfully!', 'success')
        return redirect(url_for('products.category_list'))
    
    products = category.products
    total_value = sum(
        (Decimal(str(product.price)) * Decimal(str(product.quantity)) for product in products),
        Decimal('0.00')
    )
    return render_template(
        'products/category_confirm_delete.html',
        category=category,
        form=FlaskForm(),
        num_products=len(products),
        category_total_value=total_value
    )


# ========== Product CRUD ==========

@products_bp.route('/products')
@login_required
def product_list():
    """List all products with search and filter"""
    query_search = request.args.get('q', '')
    category_id = request.args.get('category', '')
    status = request.args.get('status', '')
    stock_filter = request.args.get('stock', '')
    
    query = Product.query
    
    # Search
    if query_search:
        query = query.filter(
            or_(
                Product.name.ilike(f'%{query_search}%'),
                Product.sku.ilike(f'%{query_search}%'),
                Product.description.ilike(f'%{query_search}%')
            )
        )
    
    # Filter by category
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # Filter by status
    if status:
        query = query.filter_by(status=status)
    
    # Filter by stock level
    if stock_filter == 'low':
        query = query.filter(and_(Product.quantity <= Product.minimum_stock, Product.quantity > 0))
    elif stock_filter == 'out':
        query = query.filter_by(quantity=0)
    elif stock_filter == 'in_stock':
        query = query.filter(Product.quantity > Product.minimum_stock)
    
    products = query.all()
    
    total_stock_value = sum(
        (Decimal(str(p.price)) * Decimal(str(p.quantity)) if p.price else Decimal('0'))
        for p in products
    ) if products else Decimal('0.00')
    
    categories = Category.query.all()
    
    return render_template('products/product_list.html',
        products=products,
        categories=categories,
        query=query_search,
        selected_category=category_id,
        selected_status=status,
        selected_stock=stock_filter,
        total_stock_value=total_stock_value
    )


@products_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """View product details with stock history"""
    product = Product.query.get_or_404(product_id)
    movements = StockMovement.query.filter_by(product_id=product_id).order_by(StockMovement.created_at.desc()).limit(20).all()
    
    return render_template('products/product_detail.html',
        product=product,
        movements=movements,
        can_edit=user_can_edit(current_user)
    )


@products_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
def product_create():
    """Create a new product"""
    if not user_can_edit(current_user):
        flash('You do not have permission to create products.', 'error')
        return redirect(url_for('products.product_list'))
    
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            sku=form.sku.data,
            description=form.description.data,
            category_id=form.category.data if form.category.data else None,
            price=form.price.data,
            quantity=form.quantity.data,
            minimum_stock=form.minimum_stock.data,
            status=form.status.data,
            created_by_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        
        flash(f'Product "{product.name}" created successfully!', 'success')
        return redirect(url_for('products.product_detail', product_id=product.id))
    
    return render_template('products/product_form.html', form=form, title='Add New Product')


@products_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    """Edit a product"""
    if not user_can_edit(current_user):
        flash('You do not have permission to edit products.', 'error')
        return redirect(url_for('products.product_list'))
    
    product = Product.query.get_or_404(product_id)
    
    form = ProductForm()
    if form.validate_on_submit():
        product.name = form.name.data
        product.sku = form.sku.data
        product.description = form.description.data
        product.category_id = form.category.data if form.category.data else None
        product.price = form.price.data
        product.quantity = form.quantity.data
        product.minimum_stock = form.minimum_stock.data
        product.status = form.status.data
        
        db.session.commit()
        
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('products.product_detail', product_id=product.id))
    elif request.method == 'GET':
        form.name.data = product.name
        form.sku.data = product.sku
        form.description.data = product.description
        form.category.data = product.category_id
        form.price.data = product.price
        form.quantity.data = product.quantity
        form.minimum_stock.data = product.minimum_stock
        form.status.data = product.status
    
    return render_template('products/product_form.html', form=form, title=f'Edit Product: {product.name}')


@products_bp.route('/products/<int:product_id>/delete', methods=['GET', 'POST'])
@login_required
def product_delete(product_id):
    """Delete a product"""
    if not user_can_delete(current_user):
        flash('You do not have permission to delete products.', 'error')
        return redirect(url_for('products.product_list'))
    
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        
        flash(f'Product "{product_name}" deleted successfully!', 'success')
        return redirect(url_for('products.product_list'))
    
    return render_template(
        'products/product_confirm_delete.html',
        product=product,
        form=FlaskForm()
    )


# ========== Stock Management ==========

@products_bp.route('/products/<int:product_id>/stock', methods=['GET', 'POST'])
@login_required
def stock_adjust(product_id):
    """Adjust stock for a product"""
    if not user_can_edit(current_user):
        flash('You do not have permission to adjust stock.', 'error')
        return redirect(url_for('products.product_list'))
    
    product = Product.query.get_or_404(product_id)
    
    form = StockAdjustmentForm()
    if form.validate_on_submit():
        adjustment_type = form.adjustment_type.data
        quantity = form.quantity.data
        notes = form.notes.data
        
        try:
            if adjustment_type == 'add':
                product.add_stock(quantity, user=current_user, notes=notes)
                flash(f'Added {quantity} units to {product.name}', 'success')
            elif adjustment_type == 'remove':
                product.remove_stock(quantity, user=current_user, notes=notes)
                flash(f'Removed {quantity} units from {product.name}', 'success')
            elif adjustment_type == 'set':
                old_quantity = product.quantity
                product.quantity = quantity
                db.session.commit()
                
                StockMovement.create(
                    product_id=product.id,
                    movement_type='adjustment',
                    quantity=abs(quantity - old_quantity),
                    reference=f'Stock adjusted from {old_quantity} to {quantity}',
                    notes=notes,
                    performed_by_id=current_user.id
                )
                
                flash(f'Set {product.name} quantity to {quantity}', 'success')
            
            return redirect(url_for('products.product_detail', product_id=product.id))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('products/stock_adjust.html', form=form, product=product)


@products_bp.route('/movements')
@login_required
def stock_movements():
    """View all stock movements with filter"""
    form = StockMovementFilterForm()
    
    query = StockMovement.query
    
    if form.validate_on_submit() or request.method == 'GET':
        product_query = request.args.get('product', '')
        movement_type = request.args.get('movement_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        if product_query:
            query = query.filter(
                or_(
                    Product.name.ilike(f'%{product_query}%'),
                    Product.sku.ilike(f'%{product_query}%')
                )
            ).join(Product)
        
        if movement_type:
            query = query.filter_by(movement_type=movement_type)
        
        if date_from:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(StockMovement.created_at >= date_from_obj)
        
        if date_to:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(StockMovement.created_at <= date_to_obj)
    
    movements = query.order_by(StockMovement.created_at.desc()).limit(100).all()
    
    return render_template('products/stock_movements.html', movements=movements, form=form)


# ========== Reports ==========

@products_bp.route('/reports/low-stock')
@login_required
def low_stock_report():
    """Report of low stock items"""
    products_query = Product.query.filter(Product.status == 'active').all()
    products = sorted(
        [p for p in products_query if p.quantity <= p.minimum_stock],
        key=lambda x: x.quantity
    )
    
    out_of_stock = [p for p in products if p.quantity == 0]
    low_stock = [p for p in products if p.quantity > 0]
    
    # Calculate restock value
    restock_value = Decimal('0.00')
    for p in low_stock:
        deficit = p.minimum_stock - p.quantity
        restock_value += Decimal(str(p.price)) * Decimal(str(deficit)) if p.price else Decimal('0')
    for p in out_of_stock:
        restock_value += Decimal(str(p.price)) * Decimal(str(p.minimum_stock)) if p.price else Decimal('0')
    
    return render_template('products/low_stock_report.html',
        products=products,
        out_of_stock_count=len(out_of_stock),
        low_count=len(low_stock),
        restock_value=restock_value,
        report_title='Low Stock Report'
    )


@products_bp.route('/reports/monthly')
@login_required
def monthly_sales_report():
    """Monthly sales/stock movement summary"""
    months = int(request.args.get('months', 12))
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    
    movements = StockMovement.query.filter(StockMovement.created_at >= start_date).all()
    
    # Organize by month
    months_dict = {}
    for movement in movements:
        month_key = movement.created_at.strftime('%Y-%m')
        if month_key not in months_dict:
            months_dict[month_key] = {
                'month': movement.created_at,
                'in_quantity': 0,
                'out_quantity': 0,
                'adjustment_quantity': 0,
                'in_count': 0,
                'out_count': 0,
            }
        
        if movement.movement_type == 'in':
            months_dict[month_key]['in_quantity'] += movement.quantity
            months_dict[month_key]['in_count'] += 1
        elif movement.movement_type == 'out':
            months_dict[month_key]['out_quantity'] += movement.quantity
            months_dict[month_key]['out_count'] += 1
        elif movement.movement_type == 'adjustment':
            months_dict[month_key]['adjustment_quantity'] += movement.quantity
    
    monthly_data = sorted(months_dict.values(), key=lambda x: x['month'], reverse=True)
    
    # Compute summary totals
    total_in = sum(m['in_quantity'] for m in monthly_data)
    total_out = sum(m['out_quantity'] for m in monthly_data)
    total_transactions = sum(m['in_count'] + m['out_count'] for m in monthly_data)
    
    return render_template('products/monthly_report.html',
        monthly_data=monthly_data,
        total_in=total_in,
        total_out=total_out,
        total_transactions=total_transactions,
        report_title='Monthly Stock Movement Report'
    )


@products_bp.route('/reports/valuation')
@login_required
def inventory_valuation_report():
    """Inventory valuation report"""
    products = Product.query.all()
    
    categories_by_id = {}
    total_value = Decimal('0.00')
    
    for product in products:
        if product.category_id not in categories_by_id:
            cat = product.category
            categories_by_id[product.category_id] = {
                'name': cat.name if cat else 'Uncategorized',
                'num_products': 0,
                'total_quantity': 0,
                'total_value': Decimal('0.00')
            }
        
        product_value = Decimal(str(product.price)) * Decimal(str(product.quantity)) if product.price else Decimal('0')
        category_data = categories_by_id[product.category_id]
        category_data['num_products'] += 1
        category_data['total_quantity'] += product.quantity
        category_data['total_value'] += product_value
        total_value += product_value

    categories = list(categories_by_id.values())
    
    return render_template('products/valuation_report.html',
        categories=categories,
        total_value=total_value,
        report_title='Inventory Valuation Report'
    )


# ========== API Endpoints ==========

@products_bp.route('/api/products/search')
@login_required
def product_search_api():
    """API endpoint for product search"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    products = Product.query.filter(
        or_(
            Product.name.ilike(f'%{query}%'),
            Product.sku.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = [
        {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'quantity': p.quantity,
            'status': p.stock_status
        }
        for p in products
    ]
    
    return jsonify(results)


@products_bp.route('/api/dashboard/stats')
@login_required
def dashboard_stats_api():
    """API endpoint for dashboard statistics"""
    products = Product.query.all()
    
    total_products = len(products)
    total_stock_value = sum(
        (Decimal(str(p.price)) * Decimal(str(p.quantity)) if p.price else Decimal('0'))
        for p in products
    )
    
    low_stock = len([p for p in products if p.quantity <= p.minimum_stock and p.quantity > 0])
    out_of_stock = len([p for p in products if p.quantity == 0])
    
    return jsonify({
        'total_products': total_products,
        'total_stock_value': float(total_stock_value),
        'low_stock': low_stock,
        'out_of_stock': out_of_stock
    })
