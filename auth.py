"""
Authentication routes and utilities for the inventory management application
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from models import db, User, UserProfile, Category, Product, StockMovement
from forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, AdminUserForm
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration view"""
    if current_user.is_authenticated:
        return redirect(url_for('products.dashboard'))
    
    form = UserRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Create user profile with viewer role
        profile = UserProfile(user_id=user.id, role='viewer')
        db.session.add(profile)
        db.session.commit()
        
        login_user(user)
        flash(f'Welcome {user.first_name or user.username}! Your account has been created.', 'success')
        return redirect(url_for('products.dashboard'))
    
    return render_template('accounts/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login view"""
    if current_user.is_authenticated:
        return redirect(url_for('products.dashboard'))
    
    form = UserLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash(f'Welcome back, {user.first_name or user.username}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('products.dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('accounts/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout view"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile view and edit"""
    form = UserProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.profile.phone = form.phone.data
        current_user.profile.department = form.department.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.profile.phone
        form.department.data = current_user.profile.department
    
    return render_template('accounts/profile.html', form=form, user_profile=current_user.profile)


@auth_bp.route('/admin-panel')
@login_required
def admin_panel():
    """Show administrative overview to application administrators."""
    if not current_user.profile.is_admin:
        flash('You do not have permission to access the admin panel.', 'error')
        return redirect(url_for('products.dashboard'))
    
    context = {
        'user_count': UserProfile.query.count(),
        'staff_count': UserProfile.query.filter_by(role='staff').count(),
        'viewer_count': UserProfile.query.filter_by(role='viewer').count(),
        'product_count': Product.query.count(),
        'category_count': Category.query.count(),
        'movement_count': StockMovement.query.count(),
        'recent_users': UserProfile.query.join(User).order_by(UserProfile.created_at.desc()).limit(5).all(),
    }
    return render_template('accounts/admin_panel.html', **context)


@auth_bp.route('/users')
@login_required
def user_list():
    """Admin only: List all users"""
    if not current_user.profile.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('products.dashboard'))
    
    query = request.args.get('q', '')
    
    users_query = UserProfile.query.join(User)
    
    if query:
        users_query = users_query.filter(
            or_(
                User.username.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%')
            )
        )
    
    users = users_query.all()
    
    return render_template('accounts/user_list.html', users=users, query=query)


@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Admin only: Edit user role"""
    if not current_user.profile.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('products.dashboard'))
    
    user_profile = UserProfile.query.filter_by(user_id=user_id).first_or_404()
    
    form = AdminUserForm()
    if form.validate_on_submit():
        user_profile.role = form.role.data
        user_profile.phone = form.phone.data
        user_profile.department = form.department.data
        
        db.session.commit()
        flash(f'Updated role for {user_profile.user.username}', 'success')
        return redirect(url_for('auth.user_list'))
    elif request.method == 'GET':
        form.role.data = user_profile.role
        form.phone.data = user_profile.phone
        form.department.data = user_profile.department
    
    return render_template('accounts/user_edit.html', form=form, user_profile=user_profile)


# ========== Helper Functions ==========

def user_can_edit(user):
    """Check if user can edit inventory"""
    return hasattr(user, 'profile') and user.profile.can_edit


def user_can_delete(user):
    """Check if user can delete items"""
    return hasattr(user, 'profile') and user.profile.can_delete
