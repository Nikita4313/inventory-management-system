# Inventory Management System - Flask Edition

A modern, feature-rich inventory management system built with Flask and SQLAlchemy. This project provides a complete solution for managing products, categories, stock movements, and user access control.

## Features

- **User Authentication & Authorization**
  - User registration and login
  - Role-based access control (Admin, Staff, Viewer)
  - User profile management
  - Admin panel for user management

- **Product Management**
  - Create, read, update, delete products
  - Product categorization
  - SKU tracking with unique identification
  - Status management (Active, Inactive, Discontinued)

- **Stock Management**
  - Real-time stock tracking
  - Stock movement history (audit trail)
  - Stock adjustment (add, remove, set exact quantity)
  - Low stock alerts
  - Out-of-stock tracking

- **Reporting & Analytics**
  - Dashboard with key metrics
  - Low stock report
  - Monthly stock movement report
  - Inventory valuation report
  - API endpoints for data access

- **Modern UI**
  - Responsive design with Font Awesome icons
  - Interactive sidebar navigation
  - Flash messages for user feedback
  - Clean and professional interface

## Technology Stack

- **Backend**: Flask 3.0.0
- **Database**: SQLAlchemy (SQLite by default, supports PostgreSQL/MySQL)
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Validation**: WTForms validators
- **Environment**: python-decouple

## Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Step 1: Clone/Extract Project
```bash
cd inventory_management
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Set Up Environment Variables
```bash
# Copy example and modify if needed
cp .env.example .env
```

### Step 5: Initialize Database
```bash
# Create database tables
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

### Step 6: Create Admin User
```bash
python run.py
# Then in another terminal:
flask create-admin
```

Follow the prompts to create an admin user.

## Running the Application

### Development Server
```bash
python run.py
```

The application will be available at `http://127.0.0.1:5000`

### With Flask CLI
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

## Project Structure

```
inventory_management/
├── app.py                 # Flask application factory
├── config.py              # Configuration settings
├── models.py              # SQLAlchemy models
├── forms.py               # Flask-WTF forms
├── auth.py                # Authentication blueprint
├── products.py            # Products blueprint
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── .env.example           # Environment template
├── templates/             # Jinja2 templates
│   ├── base.html          # Base template
│   ├── auth/              # Authentication templates
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── profile.html
│   │   ├── admin_panel.html
│   │   └── user_list.html
│   ├── products/          # Product templates
│   │   ├── dashboard.html
│   │   ├── product_list.html
│   │   ├── product_detail.html
│   │   ├── product_form.html
│   │   ├── category_list.html
│   │   └── ... (other templates)
│   └── errors/            # Error templates
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
└── static/                # Static files
    └── css/style.css
```

## Database Models

### User
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `password_hash` - Hashed password
- `first_name`, `last_name` - User names
- `is_active` - Account status
- `created_at`, `updated_at` - Timestamps

### UserProfile
- `id` - Primary key
- `user_id` - Foreign key to User
- `role` - User role (admin, staff, viewer)
- `phone`, `department` - Additional info
- `created_at`, `updated_at` - Timestamps

### Category
- `id` - Primary key
- `name` - Category name (unique)
- `description` - Optional description
- `created_at`, `updated_at` - Timestamps

### Product
- `id` - Primary key
- `name` - Product name
- `sku` - Stock Keeping Unit (unique)
- `description` - Product description
- `category_id` - Foreign key to Category
- `price` - Product price (Decimal)
- `quantity` - Current stock quantity
- `minimum_stock` - Low stock threshold
- `status` - Product status (active, inactive, discontinued)
- `created_by_id` - Foreign key to User
- `created_at`, `updated_at` - Timestamps

### StockMovement
- `id` - Primary key
- `product_id` - Foreign key to Product
- `movement_type` - Type (in, out, adjustment, return)
- `quantity` - Movement quantity
- `reference` - Reference information
- `notes` - Additional notes
- `performed_by_id` - Foreign key to User
- `created_at` - Timestamp

## API Endpoints

### Authentication Routes
- `GET/POST /auth/register` - User registration
- `GET/POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET/POST /auth/profile` - User profile
- `GET /auth/admin-panel` - Admin panel
- `GET /auth/users` - User list
- `GET/POST /auth/users/<user_id>/edit` - Edit user

### Product Routes
- `GET /` or `/dashboard` - Dashboard
- `GET /products` - Product list
- `GET/POST /products/create` - Create product
- `GET /products/<product_id>` - Product detail
- `GET/POST /products/<product_id>/edit` - Edit product
- `GET/POST /products/<product_id>/delete` - Delete product
- `GET/POST /products/<product_id>/stock` - Adjust stock

### Category Routes
- `GET /categories` - Category list
- `GET/POST /categories/create` - Create category
- `GET/POST /categories/<category_id>/edit` - Edit category
- `GET/POST /categories/<category_id>/delete` - Delete category

### Stock Movement Routes
- `GET /movements` - Stock movements list

### Report Routes
- `GET /reports/low-stock` - Low stock report
- `GET /reports/monthly` - Monthly report
- `GET /reports/valuation` - Valuation report

### API Endpoints
- `GET /api/products/search` - Product search
- `GET /api/dashboard/stats` - Dashboard statistics

## Configuration

Edit the `config.py` file to configure the application:

```python
# Database configuration
SQLALCHEMY_DATABASE_URI = 'sqlite:///inventory.db'

# Session configuration
PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

# CSRF protection
WTF_CSRF_ENABLED = True
```

## Environment Variables

Create a `.env` file with the following variables:

```env
# Secret key for Flask
SECRET_KEY=your-secret-key-here

# Environment (development, production, testing)
FLASK_ENV=development

# Debug mode
DEBUG=True

# Server configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Database URL
DATABASE_URL=sqlite:///inventory.db
```

## User Roles

### Admin
- Full access to all features
- Can create, edit, delete products and categories
- Can adjust stock
- Can manage users and roles
- Can view all reports

### Staff
- Can view all products and inventory
- Can create, edit products (not delete)
- Can adjust stock
- Cannot manage users
- Can view reports

### Viewer
- Can view products and inventory
- Cannot create, edit, or delete products
- Cannot adjust stock
- Read-only access

## Security Features

- Password hashing with Werkzeug security
- CSRF protection on all forms
- Role-based access control
- Secure session cookies
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy

## Troubleshooting

### Database Issues
```bash
# Reset database (WARNING: deletes all data)
python
>>> from app import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.drop_all()
...     db.create_all()
>>> exit()
```

### Missing Templates
Ensure the `templates` directory exists with all subdirectories:
- `templates/auth/`
- `templates/products/`
- `templates/errors/`

### Port Already in Use
```bash
# Change port in .env
FLASK_PORT=5001

# Or use command line
python run.py --port 5001
```

## Support for Different Databases

### PostgreSQL
```env
DATABASE_URL=postgresql://username:password@localhost/inventory_db
```

Requires: `pip install psycopg2-binary`

### MySQL
```env
DATABASE_URL=mysql+pymysql://username:password@localhost/inventory_db
```

Requires: `pip install pymysql`

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
For production deployments, consider using Flask-Migrate:
```bash
pip install Flask-Migrate
flask db init
flask db migrate
flask db upgrade
```

## License

This project is provided as-is for inventory management purposes.

## Support

For issues or questions, please refer to the Flask documentation:
- Flask: https://flask.palletsprojects.com
- SQLAlchemy: https://www.sqlalchemy.org
- Flask-Login: https://flask-login.readthedocs.io
- Flask-WTF: https://flask-wtf.readthedocs.io
