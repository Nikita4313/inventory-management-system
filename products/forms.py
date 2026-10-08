from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
from .models import Category, Product, StockMovement


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Category name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Category description (optional)'
            }),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name


class ProductForm(forms.ModelForm):
    """Form for creating and editing products"""
    
    class Meta:
        model = Product
        fields = ['name', 'sku', 'description', 'category', 'price', 'quantity', 
                  'minimum_stock', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Product name'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stock Keeping Unit (e.g., ELEC-001)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Product description (optional)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
            'minimum_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '10',
                'min': '0'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if Product.objects.filter(sku__iexact=sku).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("A product with this SKU already exists.")
        return sku
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price <= Decimal('0.00'):
            raise forms.ValidationError("Price must be greater than zero.")
        return price


class StockAdjustmentForm(forms.Form):
    """Plain Form (not ModelForm) for adjusting stock levels.
    
    The 'set' adjustment type requires min_value=0 so users can set stock to 0.
    The 'add' and 'remove' types require min_value=1.
    """
    
    ADJUSTMENT_TYPES = [
        ('add', 'Add Stock'),
        ('remove', 'Remove Stock'),
        ('set', 'Set Quantity'),
    ]
    
    adjustment_type = forms.ChoiceField(
        choices=ADJUSTMENT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='add'
    )
    quantity = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Quantity',
            'min': '0'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Reason for adjustment (optional)'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        adjustment_type = cleaned_data.get('adjustment_type')
        quantity = cleaned_data.get('quantity')
        
        if quantity is not None:
            if adjustment_type in ('add', 'remove') and quantity < 1:
                raise forms.ValidationError(
                    "Quantity must be at least 1 for add/remove operations."
                )
            if adjustment_type == 'set' and quantity < 0:
                raise forms.ValidationError(
                    "Quantity cannot be negative."
                )
        
        return cleaned_data


class StockMovementFilterForm(forms.Form):
    """Form for filtering stock movements"""
    
    MOVEMENT_TYPE_CHOICES = [('', 'All Types')] + StockMovement.MOVEMENT_TYPES
    
    product = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by product name or SKU...'
        })
    )
    movement_type = forms.ChoiceField(
        choices=MOVEMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )


class ReportFilterForm(forms.Form):
    """Form for report filters"""
    
    PERIOD_CHOICES = [
        ('week', 'Last 7 Days'),
        ('month', 'Last 30 Days'),
        ('quarter', 'Last 3 Months'),
        ('year', 'Last Year'),
    ]
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        initial='month',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
