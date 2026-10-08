"""Custom ``flask`` CLI commands: init-db, create-admin and seed."""

from decimal import Decimal

import click

from .extensions import db
from .models import Category, Product, StockMovement, User


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Create all database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-admin")
    @click.option("--username", default="admin", help="Administrator username.")
    @click.option("--email", default="admin@example.com", help="Administrator email.")
    @click.option("--password", default="admin123", help="Administrator password.")
    def create_admin(username, email, password):
        """Create (or reset) an administrator account."""
        user = User.query.filter_by(username=username).first()
        if user is None:
            user = User(
                username=username,
                email=email,
                first_name="Admin",
                last_name="User",
                role="admin",
            )
            db.session.add(user)
            click.echo(f"Created administrator '{username}'.")
        else:
            user.role = "admin"
            click.echo(f"Updated existing account '{username}'.")
        user.set_password(password)
        db.session.commit()
        click.echo(f"Password set to '{password}'. Log in at /accounts/login/")

    @app.cli.command("seed")
    def seed():
        """Populate the database with demo users, categories and products."""
        demo_users = [
            ("admin", "admin@example.com", "System", "Administrator", "admin", "admin123"),
            ("staff", "staff@example.com", "Sara", "Stock", "staff", "staff123"),
            ("viewer", "viewer@example.com", "Victor", "Read", "viewer", "viewer123"),
        ]
        for username, email, first, last, role, password in demo_users:
            if User.query.filter_by(username=username).first():
                continue
            user = User(
                username=username,
                email=email,
                first_name=first,
                last_name=last,
                role=role,
                phone="+1-555-0100",
                department="Operations",
            )
            user.set_password(password)
            db.session.add(user)
        db.session.commit()

        admin = User.query.filter_by(username="admin").first()

        categories = [
            ("Electronics", "Devices, accessories and gadgets"),
            ("Stationery", "Office and writing supplies"),
            ("Furniture", "Desks, chairs and storage"),
        ]
        cat_map = {}
        for name, description in categories:
            cat = Category.query.filter_by(name=name).first()
            if cat is None:
                cat = Category(name=name, description=description)
                db.session.add(cat)
            cat_map[name] = cat
        db.session.commit()

        products = [
            ("Wireless Mouse", "ELEC-001", "Electronics", "29.99", 45, 10),
            ("Mechanical Keyboard", "ELEC-002", "Electronics", "89.50", 8, 10),
            ("USB-C Hub", "ELEC-003", "Electronics", "45.00", 0, 5),
            ("A4 Notebook", "STAT-001", "Stationery", "3.75", 200, 50),
            ("Gel Pen Pack", "STAT-002", "Stationery", "5.25", 12, 25),
            ("Ergonomic Chair", "FURN-001", "Furniture", "199.00", 6, 4),
            ("Standing Desk", "FURN-002", "Furniture", "349.00", 3, 5),
        ]
        for name, sku, cat_name, price, qty, min_stock in products:
            if Product.query.filter_by(sku=sku).first():
                continue
            product = Product(
                name=name,
                sku=sku,
                category=cat_map[cat_name],
                price=Decimal(price),
                quantity=qty,
                minimum_stock=min_stock,
                status="active",
                created_by=admin,
                description=f"{name} \u2014 demo inventory item.",
            )
            db.session.add(product)
            db.session.flush()
            db.session.add(
                StockMovement(
                    product=product,
                    movement_type="in",
                    quantity=qty,
                    reference=f"Initial stock: {qty} units",
                    notes="Seeded demo data",
                    performed_by=admin,
                )
            )
        db.session.commit()

        click.echo(
            "Seed complete. Sign in with:\n"
            "  admin / admin123   (Administrator)\n"
            "  staff / staff123   (Staff)\n"
            "  viewer / viewer123 (Read-only)"
        )
