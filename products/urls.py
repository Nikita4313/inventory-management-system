from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Stock Management
    path('products/<int:pk>/stock/', views.stock_adjust, name='stock_adjust'),
    path('movements/', views.stock_movements, name='stock_movements'),
    
    # Reports
    path('reports/low-stock/', views.low_stock_report, name='low_stock_report'),
    path('reports/monthly/', views.monthly_sales_report, name='monthly_report'),
    path('reports/valuation/', views.inventory_valuation_report, name='valuation_report'),
    
    # API Endpoints
    path('api/products/search/', views.product_search_api, name='product_search_api'),
    path('api/dashboard/stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
]
