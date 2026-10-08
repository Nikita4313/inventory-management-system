from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """Product category for organizing inventory"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Core inventory item with stock tracking"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text='Stock Keeping Unit - unique identifier')
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    quantity = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        help_text='Current stock quantity'
    )
    minimum_stock = models.IntegerField(
        default=10, 
        validators=[MinValueValidator(0)],
        help_text='Alert when stock falls below this level'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
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
        return self.price * self.quantity
    
    def add_stock(self, quantity, user=None, notes=''):
        """Add stock and record the movement"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        self.quantity += quantity
        self.save()
        
        StockMovement.objects.create(
            product=self,
            movement_type='in',
            quantity=quantity,
            reference=f"Stock added: {quantity} units",
            notes=notes,
            performed_by=user
        )
    
    def remove_stock(self, quantity, user=None, notes=''):
        """Remove stock and record the movement"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if quantity > self.quantity:
            raise ValueError(f"Insufficient stock. Available: {self.quantity}")
        
        self.quantity -= quantity
        self.save()
        
        StockMovement.objects.create(
            product=self,
            movement_type='out',
            quantity=quantity,
            reference=f"Stock removed: {quantity} units",
            notes=notes,
            performed_by=user
        )


class StockMovement(models.Model):
    """Audit trail for all stock changes"""
    
    MOVEMENT_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reference = models.CharField(max_length=200, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Stock Movements'
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} ({self.quantity})"
