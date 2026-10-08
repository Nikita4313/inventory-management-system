# 📦 Inventory Management System — Flask edition

A 1:1 port of the original **Django** Inventory Management System to **Flask**.
Same features, same UI (the original stylesheet is reused untouched), same
role-based access control.

The Django project was left completely intact, so you can compare or fall back
to it at any time.

---

## 🧱 Stack

| Concern | Django original | Flask port |
|---|---|---|
| Framework | Django 4.2 | Flask 3 |
| ORM | Django ORM | Flask-SQLAlchemy (SQLAlchemy 2) |
| Auth | `django.contrib.auth` | Flask-Login + Werkzeug password hashing |
| Templates | Django templates | Jinja2 |
| CSRF | `{% csrf_token %}` | Flask-WTF `CSRFProtect` + `csrf_token()` |
| Config | `decouple` | `decouple` |
| DB | `db.sqlite3` | `inventory.db` (separate file) |

---

## 🚀 Quick start

```bash
cd flask_app

# 1. Activate the project virtualenv (reuse the existing one)
..\venv\Scripts\activate        # Windows
# source ../venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Load demo data (creates users, categories, products)
flask --app run.py seed

# 4. Run it
python run.py
# or: flask --app run.py run --debug
```

Open <http://127.0.0.1:5000/>.

### Demo accounts

| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | Administrator — full access |
| `staff` | `staff123` | Staff — create/edit inventory |
| `viewer` | `viewer123` | Read-only |

> Prefer to start clean? Run `flask --app run.py create-admin` instead of `seed`.

---

## 📁 Structure

```
flask_app/
├── run.py                     # entry point (python run.py)
├── smoke_test.py              # end-to-end route tests
├── requirements.txt
├── .env.example               # copy to .env to override settings
└── inventory/                 # application package
    ├── __init__.py            # create_app() factory
    ├── config.py              # settings (env-driven)
    ├── extensions.py          # db / login_manager / csrf
    ├── models.py              # User, Category, Product, StockMovement
    ├── forms.py               # validation helpers
    ├── utils.py               # decorators + Jinja filters (intcomma, timesince…)
    ├── cli.py                 # init-db / create-admin / seed commands
    ├── auth.py                # /accounts/*  (was the `accounts` app)
    ├── products.py            # /  (was the `products` app)
    ├── templates/
    │   ├── base.html
    │   ├── _flash.html
    │   ├── accounts/…
    │   └── products/…
    └── static/css/style.css   # copied from the original project
```

---

## 🔗 Routes (identical to the Django version)

| Method | Path | Endpoint |
|---|---|---|
| GET | `/` | Dashboard |
| GET | `/products/` | Product list + filters |
| GET/POST | `/products/create/` | Add product |
| GET | `/products/<id>/` | Product detail |
| GET/POST | `/products/<id>/edit/` | Edit product |
| GET/POST | `/products/<id>/delete/` | Delete product |
| GET/POST | `/products/<id>/stock/` | Stock adjustment |
| GET | `/movements/` | Stock movement audit trail |
| GET | `/categories/` | Category list |
| GET/POST | `/categories/create/` | Add category |
| GET/POST | `/categories/<id>/edit/` | Edit category |
| GET/POST | `/categories/<id>/delete/` | Delete category |
| GET | `/reports/low-stock/` | Low stock report |
| GET | `/reports/monthly/` | Monthly movement report |
| GET | `/reports/valuation/` | Valuation report |
| GET | `/accounts/login/` | Login |
| GET/POST | `/accounts/register/` | Register (creates a read-only user) |
| GET | `/accounts/logout/` | Logout |
| GET/POST | `/accounts/profile/` | Profile |
| GET | `/accounts/admin-panel/` | Admin overview |
| GET | `/accounts/users/` | User management |
| GET/POST | `/accounts/users/<id>/edit/` | Change user role |
| GET | `/api/products/search/?q=` | Product search (JSON) |
| GET | `/api/dashboard/stats/` | Dashboard stats (JSON) |

There is **no** `/admin/` (that was Django's admin). Django's admin site is not
part of the Flask ecosystem — the app's own Admin Panel covers user management.

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and adjust:

```
SECRET_KEY=change-me
DEBUG=True
PORT=5000
DATABASE_URL=sqlite:///C:/path/to/inventory.db
```

Settings are read in `inventory/config.py`.

---

## 🧪 Tests

```bash
cd flask_app
python smoke_test.py
```

Runs every route (auth, CRUD, stock, reports, APIs, permissions) against a
temporary SQLite database and prints a pass/fail summary.

---

## 📝 Migration notes

- **Templates** were converted mechanically: `{% url %}` → `{{ url_for(...) }}`,
  `{% static %}` → `{{ url_for('static', …) }}`, `{% csrf_token %}` → hidden
  `csrf_token` input, Django date filters → `strftime`, and Django's
  `intcomma` / `timesince` / `truncatewords` filters are re-implemented in
  `utils.py`.
- **Models**: Django's `UserProfile` was folded into the `User` model (role,
  phone, department live on the user). `User.profile` still returns `self` so
  Django-style template access keeps working.
- **Permissions**: the `is_admin`, `can_edit`, `can_delete` properties mirror
  `UserProfile`, and `edit_required` / `admin_required` decorators replace the
  in-view permission checks.
- **Passwords** are stored with Werkzeug hashes, which are **not** compatible
  with Django's PBKDF2 hashes — so existing users need a password reset. The
  Flask app uses its own `inventory.db`; the Django `db.sqlite3` is untouched.
- Category deletion keeps products (sets them to *Uncategorised*), matching the
  original `SET_NULL` behaviour. Product deletion removes its movement history
  (matching `CASCADE`).
