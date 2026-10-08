# 📦 Inventory Management System

> ## 🧵 This repo contains **two** implementations
>
> | Version | Location | Documentation | Run it |
> |---|---|---|---|
> | 🟢 **Flask (new)** | [`flask_app/`](flask_app/) | [`flask_app/README.md`](flask_app/README.md) | `cd flask_app` → `python run.py` (or run `setup.bat` / `setup.sh`) |
> | 🔵 Django (original) | project root | this file | `pip install -r requirements.txt` → `python manage.py runserver` |
>
> Both use the **same features and UI**, but each has its **own database** —
> `flask_app/inventory.db` for Flask and `db.sqlite3` for Django — so they can
> run side by side (Flask on port **5000**, Django on port **8000**).
>
> The Flask edition replaces Django's `admin` site with its own Admin Panel and
> CLI commands (`flask --app run.py seed`, `create-admin`). Existing data is
> **not** shared automatically, and password hashes differ between the two, so
> treat the Flask DB as a fresh start (use `seed` for demo data).

---

A complete, production-ready **Inventory Management System**. Features role-based access control, full CRUD operations, stock tracking with audit trails, and reporting dashboards.

---

## 🚀 Quick Start (Django version)

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git (optional)

### Step 1: Clone or Navigate to Project
```bash
cd C:\Users\soura\Downloads\inventory_management
```

### Step 2: Create a Virtual Environment (Recommended)
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

### Step 4: Run Migrations
```bash
python manage.py migrate
```

### Step 5: Create an Admin User
```bash
python manage.py createsuperuser
```
Follow the prompts to set a username, email, and password. This user will have **Administrator** role automatically.

### Step 6: Start the Development Server
```bash
python manage.py runserver
```

### Step 7: Open in Browser
- **Application**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Django Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📁 Project Structure

```text
inventory_management/
├── inventory_system/          # Django project settings
│   ├── settings.py            # Configuration (DB, auth, static files)
│   ├── urls.py                # Root URL routing
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
│
├── accounts/                  # Authentication & user management
│   ├── models.py              # UserProfile with Admin/Staff/Viewer roles
│   ├── views.py               # Login, logout, register, profile, user management
│   ├── forms.py               # Registration, login, profile, admin forms
│   ├── urls.py                # Auth URL routes
│   ├── admin.py               # Custom admin with profile inline
│   └── migrations/
│
├── products/                  # Core inventory management
│   ├── models.py              # Category, Product, StockMovement models
│   ├── views.py               # Dashboard, CRUD, stock adjust, reports, API
│   ├── forms.py               # Category, Product, StockAdjustment, Filter forms
│   ├── urls.py                # Product URL routes
│   ├── admin.py               # Custom admin for products
│   └── migrations/
│
├── templates/                 # HTML templates
│   ├── base.html              # Sidebar navigation layout
│   ├── accounts/              # Auth pages (login, register, profile, user mgmt)
│   └── products/              # Dashboard, CRUD, reports
│
├── static/
│   └── css/style.css          # Complete modern CSS (500+ lines)
│
├── flask_app/                 # 🟢 New Flask port (see flask_app/README.md)
│
├── db.sqlite3                 # SQLite database (auto-created)
├── manage.py                  # Django management script
├── requirements.txt           # Django dependencies
└── README.md                  # This file
```

---

## 🔐 Features

### User Authentication
- **Register** with full form validation (username, email, password confirmation)
- **Login/Logout** with session management
- **Profile** editing (name, email, phone, department)

### Role-Based Access Control
| Role | Permissions |
|------|------------|
| **Admin** | Full access: CRUD all items, manage users, view all reports, delete anything |
| **Staff** | Create/edit products and categories, adjust stock, view reports |
| **Viewer** | Read-only access to dashboard, products, categories, and reports |

### Inventory Management
- **Categories**: Create, edit, delete product categories with product count/value tracking
- **Products**: Full CRUD with SKU uniqueness, price validation, minimum stock thresholds
- **Stock Adjustment**: Add, remove, or set stock quantities with audit trail
- **Stock Movements**: Complete history of all stock changes with filtering

### Reports
- **Low Stock Report**: Items below minimum stock with restock value calculation
- **Monthly Report**: Stock in/out/adjustment trends by month
- **Valuation Report**: Inventory value by category with percentage breakdown

### Dashboard
- Key metrics cards (total products, stock value, low stock count, out-of-stock count)
- Low stock alerts with product details
- Category breakdown with values
- Recent stock movements

### API Endpoints
- `GET /api/products/search/?q=<query>` — Product search autocomplete
- `GET /api/dashboard/stats/` — Dashboard statistics JSON

---

## 🛡️ Data Validation & Constraints

| Field | Validation |
|-------|-----------|
| **SKU** | Unique across all products |
| **Category Name** | Unique (case-insensitive) |
| **Email** | Unique, valid email format |
| **Price** | DecimalField, minimum $0.01 |
| **Quantity** | IntegerField, minimum 0 |
| **Minimum Stock** | IntegerField, minimum 0 |

- **Foreign Keys**: `SET_NULL` for category/user references (preserves data if referenced item is deleted)
- **Database Indexes**: On SKU and category+status for query performance
- **Form Validation**: Custom `clean_*` methods for uniqueness and business rules

---

## 🎨 UI Features

- **Sidebar Navigation**: Collapsible sidebar with section grouping
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Color-Coded Badges**: Green (in stock), amber (low stock), red (out of stock)
- **Auto-Dismiss Alerts**: Toast messages fade after 5 seconds
- **Modern CSS**: CSS variables, smooth transitions, hover effects
- **Grid Layouts**: Responsive stat cards, filter bars, form layouts
- **Inter Font**: Professional typography from Google Fonts
- **Font Awesome Icons**: 100+ icons throughout the interface

---

## 🧪 Testing the Application

### As Admin (full access):
1. Create an admin user with `python manage.py createsuperuser`
2. Log in at `http://127.0.0.1:8000/accounts/login/`
3. You should see the full sidebar including "Administration" section
4. Create categories, add products, adjust stock, view reports
5. Manage user roles at `http://127.0.0.1:8000/accounts/users/`

### As Staff (CRUD access):
1. Register a new user at `http://127.0.0.1:8000/accounts/register/`
2. Or create one via Django admin and set role to "Staff Member"
3. You can create/edit products and categories but cannot delete or manage users

### As Viewer (read-only):
1. Create a user and set role to "Read-Only Viewer" via Django admin
2. You can only view dashboard, products, categories, and reports

### Flask version:
See [`flask_app/README.md`](flask_app/README.md) — run `python smoke_test.py` inside
`flask_app/` for an end-to-end route/authorisation test suite.

---

## 📝 Development Notes

- **Database**: Uses SQLite by default. To switch to PostgreSQL, update `DATABASES` in `settings.py`
- **Secret Key**: Change `SECRET_KEY` in `settings.py` before deploying to production
- **Debug Mode**: Set `DEBUG = False` in production and configure `ALLOWED_HOSTS`
- **Static Files**: Run `python manage.py collectstatic` for production deployment

---

## 🐛 Troubleshooting

**"No module named 'django'"**
→ Install dependencies: `pip install -r requirements.txt`

**"Database is locked"**
→ Close any other Django server instances running

**"Template does not exist"**
→ Make sure you're in the project root directory when running `manage.py`

**Port 8000 already in use**
→ Use a different port: `python manage.py runserver 8080`

---

## 📄 License

This project is for educational purposes. Free to use and modify.

---

*Django version: Django 4.2+ • Python 3.10+ • SQLite*
*Flask version: Flask 3 • Flask-SQLAlchemy • Flask-Login • SQLite — see `flask_app/`*
