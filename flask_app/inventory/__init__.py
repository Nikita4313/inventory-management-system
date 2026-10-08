"""
Application factory for the Flask Inventory Management System.

Usage::

    python run.py                      # development server
    flask --app run.py seed            # load demo data
    flask --app run.py create-admin    # create an administrator
"""

from flask import Flask, render_template

from .config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    from .extensions import csrf, db, login_manager
    from .models import User  # noqa: F401  (ensures tables are registered)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # Blueprints -----------------------------------------------------------
    from .auth import auth_bp
    from .products import products_bp

    app.register_blueprint(auth_bp, url_prefix="/accounts")
    app.register_blueprint(products_bp)

    # Templates helpers / filters -----------------------------------------
    from .utils import register_template_helpers

    register_template_helpers(app)

    # CLI commands ---------------------------------------------------------
    from .cli import register_cli

    register_cli(app)

    # Error pages ----------------------------------------------------------
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    # Create tables on first run ------------------------------------------
    with app.app_context():
        db.create_all()

    return app
