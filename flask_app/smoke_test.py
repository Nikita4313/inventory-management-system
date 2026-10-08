"""
End-to-end smoke test for the Flask Inventory Management System.

Exercises every route with Flask's test client against a throwaway SQLite
database. Run from inside ``flask_app``::

    python smoke_test.py
"""

import re
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

from inventory import create_app
from inventory.config import Config
from inventory.extensions import db
from inventory.models import Category, Product, StockMovement, User

DB_FILE = Path(tempfile.gettempdir()) / "inventory_smoke.db"


class TestConfig(Config):
    TESTING = True
    DEBUG = False
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DB_FILE.as_posix()
    SECRET_KEY = "smoke-test-secret"


PASSED = []
FAILED = []


def check(label, condition, detail=""):
    if condition:
        PASSED.append(label)
        print(f"  ok   {label}")
    else:
        FAILED.append(f"{label} {detail}")
        print(f"  FAIL {label} {detail}")


class Session:
    """Test client wrapper that keeps one CSRF token for the whole session.

    Flask-WTF stores the token in the session and it is not rotated on login,
    so we can fetch it once from the login page and reuse it.
    """

    def __init__(self, app):
        self.client = app.test_client()
        self.token = None

    def _fetch_token(self):
        html = self.client.get("/accounts/login/").get_data(as_text=True)
        match = re.search(r'name="csrf_token" value="([^"]+)"', html)
        self.token = match.group(1) if match else None
        return self.token

    def get(self, path):
        return self.client.get(path)

    def post(self, path, data=None):
        if self.token is None:
            self._fetch_token()
        payload = dict(data or {})
        payload["csrf_token"] = self.token
        return self.client.post(path, data=payload)

    def login(self, username, password, next_url=None):
        self._fetch_token()
        path = "/accounts/login/"
        if next_url:
            path += f"?next={next_url}"
        return self.post(path, {"username": username, "password": password})


def seed(app):
    with app.app_context():
        db.drop_all()
        db.create_all()

        people = [
            ("admin", "admin@example.com", "Ada", "Admin", "admin"),
            ("staff", "staff@example.com", "Sam", "Staff", "staff"),
            ("viewer", "viewer@example.com", "Vic", "Viewer", "viewer"),
            ("promotee", "promotee@example.com", "Pat", "Promotee", "viewer"),
        ]
        for username, email, first, last, role in people:
            user = User(username=username, email=email, first_name=first,
                        last_name=last, role=role)
            user.set_password(f"{username}123")
            db.session.add(user)
        db.session.commit()

        admin = User.query.filter_by(username="admin").first()
        cat = Category(name="Electronics", description="Gadgets")
        db.session.add(cat)
        db.session.commit()

        mouse = Product(name="Wireless Mouse", sku="ELEC-001", category=cat,
                        price=Decimal("29.99"), quantity=45, minimum_stock=10,
                        status="active", created_by=admin)
        hub = Product(name="USB-C Hub", sku="ELEC-002", category=cat,
                      price=Decimal("45.00"), quantity=0, minimum_stock=5,
                      status="active", created_by=admin)
        db.session.add_all([mouse, hub])
        db.session.commit()
        db.session.add(StockMovement(product=mouse, movement_type="in",
                                     quantity=45, reference="Initial stock",
                                     performed_by=admin))
        db.session.commit()


def main():
    if DB_FILE.exists():
        DB_FILE.unlink()

    app = create_app(TestConfig)
    seed(app)

    # ---- anonymous access ------------------------------------------------
    print("\nAnonymous user")
    with app.test_client() as client:
        resp = client.get("/")
        check("anonymous / redirects to login",
              resp.status_code == 302 and "/accounts/login/" in resp.headers["Location"],
              f"got {resp.status_code}")
        check("login page renders", client.get("/accounts/login/").status_code == 200)
        check("register page renders", client.get("/accounts/register/").status_code == 200)

    # ---- administrator ---------------------------------------------------
    print("\nAdministrator")
    session = Session(app)
    resp = session.login("admin", "admin123")
    check("admin login redirects", resp.status_code == 302, f"got {resp.status_code}")

    pages = [
        "/products/", "/categories/", "/movements/",
        "/reports/low-stock/", "/reports/monthly/", "/reports/valuation/",
        "/accounts/profile/", "/accounts/admin-panel/", "/accounts/users/",
        "/products/1/", "/products/create/", "/categories/create/",
        "/products/1/edit/", "/products/1/stock/", "/products/1/delete/",
        "/accounts/users/1/edit/",
    ]
    check("GET /", session.get("/").status_code == 200)
    for path in pages:
        resp = session.get(path)
        check(f"GET {path}", resp.status_code == 200, f"got {resp.status_code}")

    # APIs
    resp = session.get("/api/products/search/?q=wire")
    check("search API returns match",
          resp.status_code == 200 and len(resp.get_json()["products"]) == 1)
    stats = session.get("/api/dashboard/stats/").get_json()
    check("stats API totals",
          stats["total_products"] == 2 and stats["out_of_stock_count"] == 1, str(stats))

    # filters
    in_stock = session.get("/products/?stock=in_stock").get_data(as_text=True)
    check("stock filter excludes out-of-stock",
          "ELEC-002" not in in_stock and "ELEC-001" in in_stock)
    low_stock = session.get("/products/?stock=low").get_data(as_text=True)
    check("stock filter shows only low stock", "ELEC-001" not in low_stock)
    check("product search filter",
          "Wireless Mouse" in session.get("/products/?q=wireless").get_data(as_text=True))
    check("movement filter ok",
          session.get("/movements/?movement_type=in&date_from=2000-01-01").status_code == 200)
    check("monthly selector reflects preset",
          'value="3" selected' in session.get("/reports/monthly/?months=3").get_data(as_text=True))
    check("monthly selector keeps non-preset window",
          'value="5" selected' in session.get("/reports/monthly/?months=5").get_data(as_text=True))
    check("monthly report shows seeded movement",
          "Total Stock In" in session.get("/reports/monthly/").get_data(as_text=True))

    # categories
    resp = session.post("/categories/create/", {"name": "Furniture", "description": "Desks"})
    with app.app_context():
        cat = Category.query.filter_by(name="Furniture").first()
        cat_id = cat.id if cat else None
    check("create category", resp.status_code == 302 and cat is not None)

    resp = session.post("/categories/create/", {"name": "furniture"})
    check("duplicate category rejected",
          resp.status_code == 200 and "already exists" in resp.get_data(as_text=True))

    # products
    resp = session.post("/products/create/", {
        "name": "Standing Desk", "sku": "FURN-001", "description": "Desk",
        "category": str(cat_id), "price": "349.00", "quantity": "3",
        "minimum_stock": "5", "status": "active",
    })
    with app.app_context():
        desk = Product.query.filter_by(sku="FURN-001").first()
        desk_id = desk.id if desk else None
    check("create product", resp.status_code == 302 and desk is not None)

    resp = session.post("/products/create/", {
        "name": "Bad", "sku": "BAD-1", "price": "0", "quantity": "1",
        "minimum_stock": "5", "status": "active",
    })
    check("product price validation",
          resp.status_code == 200 and "greater than zero" in resp.get_data(as_text=True))

    resp = session.post("/products/create/", {
        "name": "Dup", "sku": "elec-001", "price": "5", "quantity": "1",
        "minimum_stock": "5", "status": "active",
    })
    check("duplicate SKU rejected", "already exists" in resp.get_data(as_text=True))

    # stock movements
    resp = session.post(f"/products/{desk_id}/stock/",
                        {"adjustment_type": "add", "quantity": "7", "notes": "restock"})
    with app.app_context():
        qty = db.session.get(Product, desk_id).quantity
    check("stock add +7", resp.status_code == 302 and qty == 10, f"qty={qty}")

    resp = session.post(f"/products/{desk_id}/stock/",
                        {"adjustment_type": "remove", "quantity": "100000"})
    check("stock remove over-limit blocked",
          "Insufficient stock" in resp.get_data(as_text=True))

    resp = session.post(f"/products/{desk_id}/stock/",
                        {"adjustment_type": "set", "quantity": "4"})
    with app.app_context():
        qty = db.session.get(Product, desk_id).quantity
        movements = StockMovement.query.filter_by(product_id=desk_id).count()
    check("stock set 4 (+2 audit rows)", resp.status_code == 302 and qty == 4 and movements == 2,
          f"qty={qty} movements={movements}")

    # edit
    resp = session.post(f"/products/{desk_id}/edit/", {
        "name": "Standing Desk Pro", "sku": "FURN-001", "price": "399.00",
        "quantity": "4", "minimum_stock": "5", "status": "active",
    })
    with app.app_context():
        renamed = db.session.get(Product, desk_id).name
    check("edit product", resp.status_code == 302 and renamed == "Standing Desk Pro")

    # admin: role management + profile
    with app.app_context():
        promotee_id = User.query.filter_by(username="promotee").first().id
    resp = session.post(f"/accounts/users/{promotee_id}/edit/", {"role": "staff"})
    with app.app_context():
        new_role = db.session.get(User, promotee_id).role
    check("admin changes role", resp.status_code == 302 and new_role == "staff")

    resp = session.post("/accounts/profile/", {
        "first_name": "Ada", "last_name": "Lovelace",
        "email": "admin@example.com", "phone": "555", "department": "Ops",
    })
    with app.app_context():
        last_name = User.query.filter_by(username="admin").first().last_name
    check("profile update", resp.status_code == 302 and last_name == "Lovelace")

    # category deletion keeps products but clears their category (SET NULL)
    resp = session.post(f"/categories/{cat_id}/delete/", {})
    with app.app_context():
        cat_gone = db.session.get(Category, cat_id) is None
        desk_cat = db.session.get(Product, desk_id).category_id
    check("delete category keeps products (uncategorised)",
          resp.status_code == 302 and cat_gone and desk_cat is None,
          f"gone={cat_gone} desk_cat={desk_cat}")

    # delete product
    resp = session.post(f"/products/{desk_id}/delete/", {})
    with app.app_context():
        product_gone = db.session.get(Product, desk_id) is None
    check("delete product", resp.status_code == 302 and product_gone)

    # error page + logout
    resp = session.get("/products/999999/")
    check("styled 404 page",
          resp.status_code == 404 and "Page not found" in resp.get_data(as_text=True),
          f"got {resp.status_code}")

    check("logout redirects", session.get("/accounts/logout/").status_code == 302)
    check("logged out -> protected route redirects", session.get("/").status_code == 302)

    # ---- staff (can edit, cannot delete) ---------------------------------
    print("\nStaff")
    staff = Session(app)
    staff.login("staff", "staff123")
    check("staff can open product create", staff.get("/products/create/").status_code == 200)
    check("staff blocked from admin panel",
          staff.get("/accounts/admin-panel/").status_code == 302)
    resp = staff.post("/products/1/delete/", {})
    with app.app_context():
        still_there = db.session.get(Product, 1) is not None
    check("staff cannot delete product", resp.status_code == 302 and still_there)

    # ---- viewer (read-only) ---------------------------------------------
    print("\nViewer")
    viewer = Session(app)
    viewer.login("viewer", "viewer123")
    check("viewer can view dashboard", viewer.get("/").status_code == 200)
    check("viewer can view product list", viewer.get("/products/").status_code == 200)
    check("viewer blocked from product create",
          viewer.get("/products/create/").status_code == 302)
    check("viewer blocked from category create",
          viewer.get("/categories/create/").status_code == 302)
    check("viewer blocked from stock adjust",
          viewer.get("/products/1/stock/").status_code == 302)
    check("viewer blocked from admin panel",
          viewer.get("/accounts/admin-panel/").status_code == 302)
    check("viewer blocked from user list",
          viewer.get("/accounts/users/").status_code == 302)
    resp = viewer.post("/products/1/delete/", {})
    with app.app_context():
        still_there = db.session.get(Product, 1) is not None
    check("viewer cannot delete product", resp.status_code == 302 and still_there)

    # ---- registration ----------------------------------------------------
    print("\nRegistration")
    guest = Session(app)
    resp = guest.post("/accounts/register/", {
        "username": "newbie", "email": "new@example.com",
        "first_name": "New", "last_name": "Bie",
        "password1": "supersecret1", "password2": "supersecret1",
    })
    with app.app_context():
        newbie = User.query.filter_by(username="newbie").first()
    check("register creates a viewer", resp.status_code == 302
          and newbie is not None and newbie.role == "viewer")
    check("new user is logged in", guest.get("/").status_code == 200)

    # a fresh anonymous visitor cannot register a duplicate email
    outsider = Session(app)
    resp = outsider.post("/accounts/register/", {
        "username": "dupe", "email": "new@example.com",
        "first_name": "D", "last_name": "D",
        "password1": "supersecret1", "password2": "supersecret1",
    })
    check("duplicate email rejected",
          resp.status_code == 200 and "already registered" in resp.get_data(as_text=True),
          f"got {resp.status_code}")

    resp = outsider.post("/accounts/register/", {
        "username": "shorty", "email": "shorty@example.com",
        "first_name": "S", "last_name": "S",
        "password1": "abc", "password2": "abc",
    })
    check("short password rejected",
          "at least 8 characters" in resp.get_data(as_text=True))

    resp = outsider.post("/accounts/register/", {
        "username": "mismatch", "email": "mismatch@example.com",
        "first_name": "M", "last_name": "M",
        "password1": "supersecret1", "password2": "different1",
    })
    check("password mismatch rejected",
          "did not match" in resp.get_data(as_text=True))

    # ---- security --------------------------------------------------------
    print("\nSecurity")
    with app.test_client() as raw:
        resp = raw.post("/accounts/login/", data={"username": "admin", "password": "admin123"})
        check("POST without CSRF token rejected", resp.status_code == 400,
              f"got {resp.status_code}")

    check("login page has csrf token",
          'name="csrf_token"' in session.get("/accounts/login/").get_data(as_text=True))

    # an external ?next target must be ignored (falls back to the dashboard)
    thug = Session(app)
    resp = thug.login("admin", "admin123", next_url="https://evil.example.com/steal")
    location = resp.headers.get("Location", "")
    check("external next target ignored",
          resp.status_code == 302 and "evil.example.com" not in location,
          f"got {resp.status_code} -> {location}")

    # a same-site relative ?next target is honoured
    friend = Session(app)
    resp = friend.login("admin", "admin123", next_url="/products/?stock=low")
    location = resp.headers.get("Location", "")
    check("relative next target honoured",
          resp.status_code == 302 and location.endswith("/products/?stock=low"),
          f"got {resp.status_code} -> {location}")

    # protocol-relative targets are treated as external
    trickster = Session(app)
    resp = trickster.login("admin", "admin123", next_url="//evil.example.com")
    location = resp.headers.get("Location", "")
    check("protocol-relative next target ignored",
          resp.status_code == 302 and "evil.example.com" not in location,
          f"got {resp.status_code} -> {location}")

    # ---- access control on writes, not just reads ------------------------
    print("\nAccess control (writes)")
    anon = Session(app)
    anon._fetch_token()  # anonymous visitor with a *valid* CSRF token

    resp = anon.get("/products/create/")
    check("anonymous GET of protected page redirects to login",
          resp.status_code == 302 and "/accounts/login/" in resp.headers["Location"],
          f"got {resp.status_code}")

    resp = anon.post("/products/create/", {
        "name": "Injected", "sku": "HACK-1", "price": "1.00",
        "quantity": "1", "minimum_stock": "1", "status": "active",
    })
    with app.app_context():
        leaked = Product.query.filter_by(sku="HACK-1").first()
        leaked_cat = Category.query.filter_by(name="Hacked").first()
    anon.post("/categories/create/", {"name": "Hacked"})
    with app.app_context():
        leaked_cat = Category.query.filter_by(name="Hacked").first()
    check("anonymous POST creates nothing",
          resp.status_code == 302 and leaked is None and leaked_cat is None,
          f"got {resp.status_code}, product={leaked}, category={leaked_cat}")

    print(f"\n{len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        print("Failures:")
        for item in FAILED:
            print("  -", item)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
