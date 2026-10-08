from django.contrib import admin
from django.db.models import Count, F, Sum
from .models import Category, Product, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'num_products', 'created_at']
    search_fields = ['name']
    ordering = ['name']

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            num_products=Count('products')
        )

    def num_products(self, obj):
        return obj.num_products
    num_products.short_description = 'Products'
    num_products.admin_order_field = 'num_products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'quantity', 'minimum_stock', 'status']
    list_filter = ['status', 'category']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category', 'created_by')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'performed_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'product__sku', 'reference']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'performed_by')


# Customize Admin Site
admin.site.site_header = 'Inventory Management System'
admin.site.site_title = 'Inventory Admin'
admin.site.index_title = 'Administration'
