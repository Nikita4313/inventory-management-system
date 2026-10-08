"""Authentication and user-management blueprint (migrated from ``accounts``)."""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from .extensions import db
from .forms import validate_profile, validate_registration
from .models import (
    ROLE_CHOICES,
    Category,
    Product,
    StockMovement,
    User,
)
from .utils import admin_required

auth_bp = Blueprint("auth", __name__)


def _safe_next(target):
    """Only allow same-site relative redirects."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return None


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_registration(request.form)
        if not errors:
            user = User(
                username=cleaned["username"],
                email=cleaned["email"],
                first_name=cleaned["first_name"],
                last_name=cleaned["last_name"],
                role="viewer",  # self-registered accounts start read-only
            )
            user.set_password(cleaned["password1"])
            db.session.add(user)
            db.session.commit()

            login_user(user)
            flash(
                f"Welcome {user.first_name}! Your account has been created.",
                "success",
            )
            return redirect(url_for("products.dashboard"))

    return render_template("accounts/register.html", errors=errors)


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------

@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("products.dashboard"))

    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            error = "Invalid username or password. Please try again."
        elif not user.is_active:
            error = "This account has been deactivated. Contact an administrator."
        else:
            login_user(user)
            flash(f"Welcome back, {user.display_name}!", "success")
            return redirect(
                _safe_next(request.args.get("next"))
                or url_for("products.dashboard")
            )

    return render_template("accounts/login.html", error=error)


@auth_bp.route("/logout/")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("auth.login"))


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@auth_bp.route("/profile/", methods=["GET", "POST"])
@login_required
def profile():
    errors = {}
    if request.method == "POST":
        cleaned, errors = validate_profile(request.form, instance=current_user)
        if not errors:
            current_user.first_name = cleaned["first_name"]
            current_user.last_name = cleaned["last_name"]
            current_user.email = cleaned["email"]
            current_user.phone = cleaned["phone"]
            current_user.department = cleaned["department"]
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("auth.profile"))

    return render_template(
        "accounts/profile.html",
        user_profile=current_user,
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Administration
# ---------------------------------------------------------------------------

@auth_bp.route("/admin-panel/")
@admin_required
def admin_panel():
    context = {
        "user_count": User.query.count(),
        "staff_count": User.query.filter_by(role="staff").count(),
        "viewer_count": User.query.filter_by(role="viewer").count(),
        "product_count": Product.query.count(),
        "category_count": Category.query.count(),
        "movement_count": StockMovement.query.count(),
        "recent_users": User.query.order_by(User.date_joined.desc()).limit(5).all(),
    }
    return render_template("accounts/admin_panel.html", **context)


@auth_bp.route("/users/")
@admin_required
def user_list():
    query = (request.args.get("q") or "").strip()
    users = User.query
    if query:
        like = f"%{query}%"
        users = users.filter(
            db.or_(
                User.username.ilike(like),
                User.email.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
            )
        )
    users = users.order_by(User.date_joined.desc()).all()
    return render_template("accounts/user_list.html", users=users, query=query)


@auth_bp.route("/users/<int:user_id>/edit/", methods=["GET", "POST"])
@admin_required
def user_edit(user_id):
    user_profile = db.session.get(User, user_id)
    if user_profile is None:
        abort(404)

    if request.method == "POST":
        role = (request.form.get("role") or "").strip()
        if role not in dict(ROLE_CHOICES):
            flash("Select a valid role.", "danger")
        else:
            user_profile.role = role
            db.session.commit()
            flash(f"Updated role for {user_profile.username}", "success")
            return redirect(url_for("auth.user_list"))

    return render_template(
        "accounts/user_edit.html",
        user_profile=user_profile,
        role_choices=ROLE_CHOICES,
    )
