# Inventory Management System - Flask Conversion Complete!

## Quick Start Guide

This Django project has been successfully converted to Flask!

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database and Create Admin User
```bash
python setup.py
```

This script will:
- Create the database tables
- Prompt you to create an admin user
- Optionally create sample data

### Step 3: Run the Application
```bash
python run.py
```

The application will be available at: **http://127.0.0.1:5000**

### Step 4: Login
Use the admin credentials you created during setup.

---

## What Was Converted

### From Django to Flask:

| Component | Django | Flask |
|-----------|--------|-------|
| **Framework** | Django 4.2.16 | Flask 3.0.0 |
| **ORM** | Django ORM | SQLAlchemy |
| **Authentication** | Django Auth | Flask-Login |
| **Forms** | Django Forms | Flask-WTF |
| **Templates** | Django Templates | Jinja2 |
| **Database** | SQLite | SQLite (configurable) |

### Key Files:

- **app.py** - Flask application factory
- **config.py** - Configuration settings
- **models.py** - SQLAlchemy models (converted from Django models)
- **forms.py** - Flask-WTF forms (converted from Django forms)
- **auth.py** - Authentication blueprint
- **products_routes.py** - Product routes blueprint
- **templates/** - All templates converted to Jinja2 syntax

---

## Features Preserved

✓ User authentication and authorization
✓ Role-based access control (Admin, Staff, Viewer)
✓ Product management (CRUD operations)
✓ Category management
✓ Stock movement tracking
✓ Low stock reporting
✓ Monthly reports
✓ Inventory valuation
✓ User profile management
✓ Admin panel

---

## Project Structure

```
inventory_management/
├── app.py                    # Flask app factory
├── config.py                 # Configuration
├── models.py                 # Database models
├── forms.py                  # WTForms
├── auth.py                   # Auth blueprint
├── products_routes.py        # Products blueprint
├── run.py                    # Entry point
├── setup.py                  # Setup script
├── requirements.txt          # Dependencies
├── .env                      # Environment config
├── templates/                # Jinja2 templates
│   ├── base.html
│   ├── auth/
│   ├── products/
│   ├── errors/
└── static/                   # CSS, JS, images
```

---

## Environment Variables

The **.env** file is already configured with defaults:

```env
SECRET_KEY=flask-inventory-secret-key-change-in-production-2024
FLASK_ENV=development
DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
DATABASE_URL=sqlite:///inventory.db
```

---

## Database

The application uses SQLite by default. To use PostgreSQL or MySQL:

1. **Install driver:**
   ```bash
   # PostgreSQL
   pip install psycopg2-binary
   
   # MySQL
   pip install pymysql
   ```

2. **Update .env:**
   ```env
   # PostgreSQL
   DATABASE_URL=postgresql://user:pass@localhost/inventory

   # MySQL
   DATABASE_URL=mysql+pymysql://user:pass@localhost/inventory
   ```

---

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout
- `GET/POST /auth/profile` - User profile

### Products
- `GET /` - Dashboard
- `GET /products` - Product list
- `POST /products/create` - Create product
- `GET /products/<id>` - Product detail
- `POST /products/<id>/edit` - Edit product
- `POST /products/<id>/delete` - Delete product
- `POST /products/<id>/stock` - Adjust stock

### Reports
- `GET /reports/low-stock` - Low stock report
- `GET /reports/monthly` - Monthly report
- `GET /reports/valuation` - Valuation report

### API
- `GET /api/products/search` - Search products
- `GET /api/dashboard/stats` - Dashboard stats

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Install dependencies: `pip install -r requirements.txt`

### Issue: "Database is locked"
**Solution:** Close any other instances of the app and try again

### Issue: Port 5000 already in use
**Solution:** Change port in .env file or use: `python run.py --port 5001`

### Issue: Admin user won't authenticate
**Solution:** Run `python setup.py` again to create a new admin user

---

## Testing

To verify everything is working:

```bash
python test_app.py
```

This will test:
- Flask app initialization
- Database connectivity
- Model loading

---

## Next Steps

1. **Customize:** Modify templates and styling as needed
2. **Deploy:** Use a production WSGI server like Gunicorn
3. **Extend:** Add new features or models as required
4. **Secure:** Update SECRET_KEY for production

---

## Production Deployment

For production, use a proper WSGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

---

## Support

- Flask Documentation: https://flask.palletsprojects.com
- SQLAlchemy: https://www.sqlalchemy.org
- Flask-Login: https://flask-login.readthedocs.io
- Flask-WTF: https://flask-wtf.readthedocs.io

---

**Conversion Complete!** Happy coding! 🚀
