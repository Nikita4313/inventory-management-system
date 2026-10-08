"""
Flask extension instances.

They are created here (unbound) and initialised with the application inside the
app factory, which avoids circular imports across the package.
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
