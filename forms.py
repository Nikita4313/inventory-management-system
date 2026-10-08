"""
Flask-WTF forms for the inventory management application
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, IntegerField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Optional, Length, NumberRange, Regexp
from wtforms.widgets import DateInput, DateTimeInput
from models import User, UserProfile, Category, Product


class UserRegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField(
        'Username',
        validators=[
            DataRequired(),
            Length(min=3, max=80)
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email()
        ]
    )
    first_name = StringField('First Name', validators=[Optional(), Length(max=100)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=100)])
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=6)
        ]
    )
    password_confirm = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(),
            EqualTo('password', message='Passwords must match')
        ]
    )
    submit = SubmitField('Register')
    
    def validate_username(self, field):
        """Check if username already exists"""
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists')
    
    def validate_email(self, field):
        """Check if email already exists"""
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already exists')


class UserLoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UserProfileForm(FlaskForm):
    """User profile edit form"""
    first_name = StringField('First Name', validators=[Optional(), Length(max=100)])
    last_name = StringField('Last Name', validators=[Optional(), Length(max=100)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Update Profile')


class AdminUserForm(FlaskForm):
    """Admin user edit form"""
    role = SelectField(
        'Role',
        choices=[
            ('viewer', 'Read-Only Viewer'),
            ('staff', 'Staff Member'),
            ('admin', 'Administrator'),
        ]
    )
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Update User')


class CategoryForm(FlaskForm):
    """Category create/edit form"""
    name = StringField(
        'Category Name',
        validators=[
            DataRequired(),
            Length(min=1, max=100)
        ]
    )
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Save Category')


class ProductForm(FlaskForm):
    """Product create/edit form"""
    name = StringField(
        'Product Name',
        validators=[
            DataRequired(),
            Length(min=1, max=200)
        ]
    )
    sku = StringField(
        'SKU',
        validators=[
            DataRequired(),
            Length(min=1, max=50),
            Regexp(r'^[A-Z0-9\-_.]+$', message='SKU can only contain uppercase letters, numbers, hyphens, dots, and underscores')
        ]
    )
    description = TextAreaField('Description', validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    price = DecimalField(
        'Price',
        validators=[
            DataRequired(),
            NumberRange(min=0.01)
        ],
        places=2
    )
    quantity = IntegerField(
        'Quantity',
        validators=[
            DataRequired(),
            NumberRange(min=0)
        ]
    )
    minimum_stock = IntegerField(
        'Minimum Stock Level',
        validators=[
            DataRequired(),
            NumberRange(min=0)
        ]
    )
    status = SelectField(
        'Status',
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('discontinued', 'Discontinued'),
        ]
    )
    submit = SubmitField('Save Product')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category.choices = [(c.id, c.name) for c in Category.query.all()]


class StockAdjustmentForm(FlaskForm):
    """Stock adjustment form"""
    adjustment_type = SelectField(
        'Adjustment Type',
        choices=[
            ('add', 'Add Stock'),
            ('remove', 'Remove Stock'),
            ('set', 'Set to Exact Quantity'),
        ]
    )
    quantity = IntegerField(
        'Quantity',
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Adjust Stock')


class StockMovementFilterForm(FlaskForm):
    """Filter form for stock movements"""
    product = StringField('Product Name/SKU', validators=[Optional()])
    movement_type = SelectField(
        'Movement Type',
        choices=[
            ('', 'All Types'),
            ('in', 'Stock In'),
            ('out', 'Stock Out'),
            ('adjustment', 'Adjustment'),
            ('return', 'Return'),
        ],
        validators=[Optional()]
    )
    date_from = StringField('From Date', validators=[Optional()], render_kw={'type': 'date'})
    date_to = StringField('To Date', validators=[Optional()], render_kw={'type': 'date'})
    submit = SubmitField('Filter')
