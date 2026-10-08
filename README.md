# Inventory Management System — Flask

The active application in the repository root is built with Flask. It manages
products, categories, stock movements, users, and inventory reports.

> The original Django source files (`manage.py`, `inventory_system/`,
> `accounts/`, and `products/`) are retained for reference. They are not the
> application started by the instructions below. The `flask_app/` directory
> contains a separate Flask port; these instructions run the Flask app in the
> repository root.

## Quick start

### Requirements

- Python 3.8 or later
- pip

### Windows (PowerShell)

From the repository root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python setup.py
```

When prompted, choose **y** to create an Admin account and enter a username,
email, and password. Choose **n** for sample data if your inventory is already
present. Then start the application:

```powershell
python run.py
```

Open <http://127.0.0.1:5000/>. Sign in at
<http://127.0.0.1:5000/auth/login>.

### macOS or Linux

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py
python run.py
```

## Roles

- **Admin** — manage users and inventory, including deletions.
- **Staff** — create and edit inventory and adjust stock.
- **Viewer** — view inventory without making changes.

Newly registered accounts are Viewers. An Admin can change a user's role from
the User Management page.

## Project files

- `run.py` — starts the root Flask application.
- `app.py` — configures the Flask app, extensions, and routes.
- `models.py` — SQLAlchemy database models.
- `auth.py`, `products_routes.py` — authentication and inventory routes.
- `templates/`, `static/` — the Flask/Jinja interface and static assets.
- `setup.py` — initializes the database and can create an Admin account.
- `flask_app/` — a separate Flask implementation with its own README.
- `manage.py`, `inventory_system/`, `accounts/`, `products/` — retained
  original Django source; not used when running `python run.py`.

The root Flask app and Django source use separate SQLite databases. The root
Flask app's local database is stored under `instance/` and should not be
committed.
