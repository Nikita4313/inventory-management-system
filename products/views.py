from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count, F, Value
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Category, Product, StockMovement
from .forms import (
    CategoryForm, ProductForm, StockAdjustmentForm,
    StockMovementFilterForm, ReportFilterForm
)


# ========== Helper: Permission Check ==========

def user_can_edit(user):
    """Check if user can edit inventory"""
    return hasattr(user, 'profile') and user.profile.can_edit


def user_can_delete(user):
    """Check if user can delete items"""
    return hasattr(user, 'profile') and user.profile.can_delete


# ========== Dashboard ==========

@login_required
def dashboard(request):
    """Main dashboard with key metrics"""
    products = Product.objects.select_related('category').all()

    # Key metrics
    total_products = products.count()
    total_stock_value = products.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or Decimal('0.00')

    low_stock_products = products.filter(quantity__lte=F('minimum_stock'), quantity__gt=0)
    out_of_stock = products.filter(quantity=0)

    # Recent movements
    recent_movements = StockMovement.objects.select_related(
        'product', 'performed_by'
    )[:10]

    # Category breakdown
    category_stats = Category.objects.annotate(
        num_products=Count('products'),
        total_value=Sum(F('products__price') * F('products__quantity'))
    ).order_by('-total_value')

    context = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'low_stock_count': low_stock_products.count(),
        'out_of_stock_count': out_of_stock.count(),
        'low_stock_products': low_stock_products[:5],
        'out_of_stock_products': out_of_stock[:5],
        'recent_movements': recent_movements,
        'category_stats': category_stats,
    }
    return render(request, 'products/dashboard.html', context)


# ========== Category CRUD ==========

@login_required
def category_list(request):
    """List all categories"""
    categories = Category.objects.annotate(
        num_products=Count('products'),
        total_value=Sum(F('products__price') * F('products__quantity'))
    ).order_by('name')

    return render(request, 'products/category_list.html', {'categories': categories})


@login_required
def category_create(request):
    """Create a new category"""
    if not user_can_edit(request.user):
        messages.error(request, 'You do not have permission to create categories.')
        return redirect('products:category_list')

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm()

    return render(request, 'products/category_form.html', {
        'form': form,
        'title': 'Create Category'
    })


@login_required
def category_edit(request, pk):
    """Edit a category"""
    if not user_can_edit(request.user):
        messages.error(request, 'You do not have permission to edit categories.')
        return redirect('products:category_list')

    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('products:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'products/category_form.html', {
        'form': form,
        'title': f'Edit Category: {category.name}'
    })


@login_required
def category_delete(request, pk):
    """Delete a category"""
    if not user_can_delete(request.user):
        messages.error(request, 'You do not have permission to delete categories.')
        return redirect('products:category_list')

    category = get_object_or_404(
        Category.objects.annotate(
            num_products=Count('products'),
            total_value=Sum(F("products__price") * F("products__quantity"))
        ), pk=pk
    )

    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('products:category_list')

    return render(request, 'products/category_confirm_delete.html', {'category': category})


# ========== Product CRUD ==========

@login_required
def product_list(request):
    """List all products with search and filter"""
    products = Product.objects.select_related('category').all()

    # Search
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query) |
            Q(description__icontains=query)
        )

    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        products = products.filter(category_id=category_id)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        products = products.filter(status=status)

    # Filter by stock level
    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'low':
        products = products.filter(quantity__lte=F('minimum_stock'), quantity__gt=0)
    elif stock_filter == 'out':
        products = products.filter(quantity=0)
    elif stock_filter == 'in_stock':
        products = products.filter(quantity__gt=F('minimum_stock'))

    total_stock_value = products.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or Decimal('0.00')

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status,
        'selected_stock': stock_filter,
        'total_stock_value': total_stock_value,
    }
    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, pk):
    """View product details with stock history"""
    product = get_object_or_404(Product.objects.select_related('category', 'created_by'), pk=pk)
    movements = product.movements.select_related('performed_by')[:20]

    context = {
        'product': product,
        'movements': movements,
        'can_edit': user_can_edit(request.user),
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def product_create(request):
    """Create a new product"""
    if not user_can_edit(request.user):
        messages.error(request, 'You do not have permission to create products.')
        return redirect('products:product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.created_by = request.user
            product.save()
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm()

    return render(request, 'products/product_form.html', {
        'form': form,
        'title': 'Add New Product'
    })


@login_required
def product_edit(request, pk):
    """Edit a product"""
    if not user_can_edit(request.user):
        messages.error(request, 'You do not have permission to edit products.')
        return redirect('products:product_list')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    return render(request, 'products/product_form.html', {
        'form': form,
        'title': f'Edit Product: {product.name}'
    })


@login_required
def product_delete(request, pk):
    """Delete a product"""
    if not user_can_delete(request.user):
        messages.error(request, 'You do not have permission to delete products.')
        return redirect('products:product_list')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('products:product_list')

    return render(request, 'products/product_confirm_delete.html', {'product': product})


# ========== Stock Management ==========

@login_required
def stock_adjust(request, pk):
    """Adjust stock for a product"""
    if not user_can_edit(request.user):
        messages.error(request, 'You do not have permission to adjust stock.')
        return redirect('products:product_list')

    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment_type = form.cleaned_data['adjustment_type']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data.get('notes', '')

            try:
                if adjustment_type == 'add':
                    product.add_stock(quantity, user=request.user, notes=notes)
                    messages.success(request, f'Added {quantity} units to {product.name}')
                elif adjustment_type == 'remove':
                    product.remove_stock(quantity, user=request.user, notes=notes)
                    messages.success(request, f'Removed {quantity} units from {product.name}')
                elif adjustment_type == 'set':
                    old_quantity = product.quantity
                    product.quantity = quantity
                    product.save()
                    StockMovement.objects.create(
                        product=product,
                        movement_type='adjustment',
                        quantity=abs(quantity - old_quantity),
                        reference=f'Stock adjusted from {old_quantity} to {quantity}',
                        notes=notes,
                        performed_by=request.user
                    )
                    messages.success(request, f'Set {product.name} quantity to {quantity}')

                return redirect('products:product_detail', pk=product.pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = StockAdjustmentForm()

    return render(request, 'products/stock_adjust.html', {
        'form': form,
        'product': product
    })


@login_required
def stock_movements(request):
    """View all stock movements with filter"""
    movements = StockMovement.objects.select_related('product', 'performed_by').all()

    form = StockMovementFilterForm(request.GET)
    if form.is_valid():
        product_query = form.cleaned_data.get('product')
        movement_type = form.cleaned_data.get('movement_type')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if product_query:
            movements = movements.filter(
                Q(product__name__icontains=product_query) |
                Q(product__sku__icontains=product_query)
            )
        if movement_type:
            movements = movements.filter(movement_type=movement_type)
        if date_from:
            movements = movements.filter(created_at__date__gte=date_from)
        if date_to:
            movements = movements.filter(created_at__date__lte=date_to)

    return render(request, 'products/stock_movements.html', {
        'movements': movements[:100],
        'form': form
    })


# ========== Reports ==========

@login_required
def low_stock_report(request):
    """Report of low stock items"""
    products = Product.objects.select_related('category').filter(
        quantity__lte=F('minimum_stock'),
        status='active'
    ).order_by('quantity')

    out_of_stock = products.filter(quantity=0)
    low_stock = products.filter(quantity__gt=0)

    # Calculate restock value
    restock_value = Decimal('0.00')
    for p in low_stock:
        deficit = p.minimum_stock - p.quantity
        restock_value += p.price * deficit
    for p in out_of_stock:
        restock_value += p.price * p.minimum_stock

    return render(request, 'products/low_stock_report.html', {
        'products': products,
        'out_of_stock_count': out_of_stock.count(),
        'low_count': low_stock.count(),
        'restock_value': restock_value,
        'report_title': 'Low Stock Report'
    })


@login_required
def monthly_sales_report(request):
    """Monthly sales/stock movement summary"""
    months = int(request.GET.get('months', 12))
    start_date = timezone.now() - timedelta(days=months * 30)

    monthly_data_raw = StockMovement.objects.filter(
        created_at__gte=start_date
    ).annotate(
        month=TruncMonth('created_at')
    ).values('month', 'movement_type').annotate(
        total_quantity=Sum('quantity'),
        transaction_count=Count('id')
    ).order_by('month')

    # Organize by month
    months_dict = {}
    for entry in monthly_data_raw:
        month_key = entry['month'].strftime('%Y-%m')
        if month_key not in months_dict:
            months_dict[month_key] = {
                'month': entry['month'],
                'in_quantity': 0,
                'out_quantity': 0,
                'adjustment_quantity': 0,
                'in_count': 0,
                'out_count': 0,
            }
        if entry['movement_type'] == 'in':
            months_dict[month_key]['in_quantity'] += entry['total_quantity']
            months_dict[month_key]['in_count'] += entry['transaction_count']
        elif entry['movement_type'] == 'out':
            months_dict[month_key]['out_quantity'] += entry['total_quantity']
            months_dict[month_key]['out_count'] += entry['transaction_count']
        elif entry['movement_type'] == 'adjustment':
            months_dict[month_key]['adjustment_quantity'] += entry['total_quantity']

    monthly_data = list(reversed(list(months_dict.values())))

    # Compute summary totals
    total_in = sum(m['in_quantity'] for m in monthly_data)
    total_out = sum(m['out_quantity'] for m in monthly_data)
    total_transactions = sum(
        m['in_count'] + m['out_count'] for m in monthly_data
    )

    return render(request, 'products/monthly_report.html', {
        'monthly_data': monthly_data,
        'total_in': total_in,
        'total_out': total_out,
        'total_transactions': total_transactions,
        'report_title': 'Monthly Stock Movement Report'
    })


@login_required
def inventory_valuation_report(request):
    """Inventory valuation report by category"""
    categories = Category.objects.annotate(
        num_products=Count('products'),
        total_quantity=Sum('products__quantity'),
        total_value=Sum(F('products__price') * F('products__quantity'))
    ).order_by('-total_value')

    total_value = Product.objects.aggregate(
        total=Sum(F('price') * F('quantity'))
    )['total'] or Decimal('0.00')

    return render(request, 'products/valuation_report.html', {
        'categories': categories,
        'total_value': total_value,
        'report_title': 'Inventory Valuation Report'
    })


# ========== API Endpoints ==========

@login_required
def product_search_api(request):
    """API endpoint for product search (for autocomplete)"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'products': []})

    products = Product.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query),
        status='active'
    )[:10]

    data = [{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': str(p.price),
        'quantity': p.quantity,
    } for p in products]

    return JsonResponse({'products': data})


@login_required
def dashboard_stats_api(request):
    """API endpoint for dashboard statistics"""
    products = Product.objects.all()

    stats = {
        'total_products': products.count(),
        'total_stock_value': str(products.aggregate(
            total=Sum(F('price') * F('quantity'))
        )['total'] or Decimal('0.00')),
        'low_stock_count': products.filter(
            quantity__lte=F('minimum_stock'), quantity__gt=0
        ).count(),
        'out_of_stock_count': products.filter(quantity=0).count(),
    }

    return JsonResponse(stats)
