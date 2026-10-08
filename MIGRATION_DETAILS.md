# Django to Flask Conversion - Technical Details

## Overview

This document details the conversion of the Inventory Management System from Django to Flask.

## Architecture Changes

### Django Structure
```
Django Project
├── manage.py           # Django management tool
├── inventory_system/   # Project configuration
│   ├── settings.py    # Global configuration
│   ├── urls.py        # URL routing
│   └── wsgi.py        # WSGI entry point
├── accounts/          # Django app
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
└── products/          # Django app
    ├── models.py
    ├── views.py
    ├── forms.py
    └── urls.py
```

### Flask Structure
```
Flask Project
├── app.py             # App factory
├── config.py          # Configuration
├── models.py          # SQLAlchemy models
├── forms.py           # Flask-WTF forms
├── auth.py            # Auth blueprint
├── products_routes.py # Products blueprint
├── run.py             # Entry point
└── templates/         # Jinja2 templates
```

## Component Mapping

### 1. Models (Django ORM → SQLAlchemy)

#### User Model
**Django:**
```python
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
```

**Flask:**
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role = db.Column(db.String(20))
```

#### Key Differences:
- Flask doesn't have built-in User model - implemented from scratch
- Used `UserMixin` from Flask-Login for authentication support
- SQLAlchemy relationships defined with `db.relationship()` and `db.ForeignKey()`
- Manual password hashing using Werkzeug security
- No migrations needed (create_all() used instead)

### 2. Views (Django Functions → Flask Blueprints)

#### Django View
```python
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/product_list.html', {'products': products})
```

#### Flask Route
```python
from flask import Blueprint, render_template
from flask_login import login_required

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
@login_required
def product_list():
    products = Product.query.all()
    return render_template('products/product_list.html', products=products)
```

#### Key Differences:
- Blueprints replace Django apps
- Routes defined with decorators instead of URLconf
- No request object passed to view (use `request` from flask module)
- Template context passed as keyword arguments
- Status codes handled with tuples: `return render_template(...), 404`

### 3. Forms (Django Forms → Flask-WTF)

#### Django Form
```python
from django import forms

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'price', 'category']

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if Product.objects.exclude(pk=self.instance.pk).filter(sku=sku).exists():
            raise forms.ValidationError("SKU already exists")
        return sku
```

#### Flask-WTF Form
```python
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField
from wtforms.validators import DataRequired, ValidationError

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    sku = StringField('SKU', validators=[DataRequired()])
    price = DecimalField('Price', validators=[DataRequired()])
    category = SelectField('Category', coerce=int)

    def validate_sku(self, field):
        product = Product.query.filter_by(sku=field.data).first()
        if product:
            raise ValidationError('SKU already exists')
```

#### Key Differences:
- No ModelForm - need to manually bind form fields to model
- CSRF token handling automatic with Flask-WTF
- Validation methods prefixed with `validate_` followed by field name
- Form rendering with `{{ form.field() }}` in templates
- File uploads handled differently with `FileField` and form processing

### 4. Authentication (Django Auth → Flask-Login)

#### Django Login
```python
from django.contrib.auth import authenticate, login

def login_view(request):
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
```

#### Flask-Login
```python
from flask_login import login_user, LoginManager

@auth_bp.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
```

#### Key Differences:
- `LoginManager` configured in app factory
- Manual password verification needed (no authenticate())
- Session handling automatic with Flask-Login
- `@login_required` decorator same but from different module
- `current_user` available globally vs `request.user` in Django

### 5. Database Queries

#### Django ORM
```python
# Filter
products = Product.objects.filter(status='active', quantity__gt=0)

# Aggregation
total = Product.objects.aggregate(Sum('quantity'))['quantity']

# Joins
products = Product.objects.select_related('category')

# Exists
if Product.objects.filter(sku=sku).exists():
```

#### SQLAlchemy
```python
# Filter
products = Product.query.filter(Product.status == 'active', Product.quantity > 0).all()

# Aggregation
total = db.session.query(func.sum(Product.quantity)).scalar()

# Joins
products = Product.query.options(joinedload(Product.category)).all()

# Exists
if Product.query.filter_by(sku=sku).first():
```

#### Key Differences:
- Method chaining with `query` object vs `objects` manager
- Explicit `and_()` / `or_()` for complex filters
- Need to import `func` for aggregation functions
- Must call `.all()`, `.first()`, or `.scalar()` to execute
- Relationship loading with `joinedload()` or `selectinload()`

### 6. Templates (Django → Jinja2)

#### Django Template Syntax
```html
{% load static %}
{% url 'products:product_detail' product.pk %}
{% static 'css/style.css' %}
{% for item in items %}{{ item }}{% endfor %}
{{ product.get_status_display }}
{{ user.first_name|default:user.username }}
```

#### Jinja2 Template Syntax
```html
{{ url_for('products.product_detail', product_id=product.id) }}
{{ url_for('static', filename='css/style.css') }}
{% for item in items %}{{ item }}{% endfor %}
{{ product.get_status_display() }}
{{ current_user.first_name or current_user.username }}
```

#### Key Differences:
- No `{% load %}` statement needed
- URL reversal with `url_for()` function instead of `{% url %}`
- Static files with `url_for('static', filename=...)`
- Method calls require `()` in Jinja2
- `user` → `current_user` from Flask-Login
- No custom template filters by default

### 7. Configuration

#### Django Settings
```python
# settings.py
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.auth',
    'products',
    'accounts',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

#### Flask Config
```python
# config.py
class Config:
    SECRET_KEY = config('SECRET_KEY')
    DEBUG = config('DEBUG', cast=bool)
    SQLALCHEMY_DATABASE_URI = config('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# app.py
app.config.from_object(config_dict['development'])
db.init_app(app)
```

#### Key Differences:
- Settings in classes vs module-level variables
- No INSTALLED_APPS - blueprints registered manually
- Database URI combined into single string
- Extensions initialized in app factory
- Environment-specific configs in separate classes

## Migration Checklist

- [x] Convert models to SQLAlchemy
- [x] Implement User authentication with Flask-Login
- [x] Convert forms to Flask-WTF
- [x] Convert views to blueprints
- [x] Update all templates to Jinja2
- [x] Setup configuration system
- [x] Implement database initialization
- [x] Add error handlers
- [x] Create setup script
- [x] Test app initialization

## Known Differences

### Features Removed (Django-specific)
- Admin interface (not needed for Flask - can add later)
- Migrations (using create_all instead)
- Management commands (created `flask` CLI commands instead)
- Signals (use SQLAlchemy event system if needed)
- Middleware (use before_request/after_request hooks)

### New Requirements (Flask-specific)
- Manual WSGI server configuration for production
- Explicit blueprint registration
- Manual URL building with url_for()
- Explicit extension initialization

### Performance Considerations
- Flask is lighter weight than Django
- No ORM query optimization (select_related) by default
- Lazy query evaluation with SQLAlchemy
- No built-in caching layer (can add Redis if needed)

## Testing

The `test_app.py` script verifies:
1. Flask app initialization
2. Configuration loading
3. Database model definitions
4. Blueprint registration
5. Template rendering (basic)

For comprehensive testing, add:
- Unit tests with pytest
- Integration tests for routes
- Database tests with rollback
- Form validation tests

## Deployment

### Development
```bash
python run.py
```

### Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

### Production (uWSGI)
```bash
uwsgi --http :5000 --wsgi-file app.py --callable create_app --processes 4 --threads 2
```

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com)
- [Flask-Login Documentation](https://flask-login.readthedocs.io)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io)

## Future Enhancements

Potential additions to the Flask version:
- Database migrations with Alembic
- API documentation with OpenAPI/Swagger
- Caching layer with Redis
- Async task queue with Celery
- WebSocket support with Flask-SocketIO
- Admin interface with Flask-Admin
- Search functionality with Elasticsearch
- Docker containerization
