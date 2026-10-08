from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm, AdminUserForm
)
from .models import UserProfile
from products.models import Category, Product, StockMovement


def register_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('products:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Self-registered accounts can view inventory until an admin assigns a role.
            user.profile.role = 'viewer'
            user.profile.save()
            
            login(request, user)
            messages.success(request, f'Welcome {user.first_name}! Your account has been created.')
            return redirect('products:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('products:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            
            # Redirect based on role
            if user.profile.is_admin:
                return redirect('products:dashboard')
            return redirect('products:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """User profile view and edit"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'accounts/profile.html', {
        'form': form,
        'user_profile': request.user.profile
    })


@login_required
def admin_panel_view(request):
    """Show administrative overview to application administrators."""
    if not request.user.profile.is_admin:
        messages.error(request, 'You do not have permission to access the admin panel.')
        return redirect('products:dashboard')

    context = {
        'user_count': UserProfile.objects.count(),
        'staff_count': UserProfile.objects.filter(role='staff').count(),
        'viewer_count': UserProfile.objects.filter(role='viewer').count(),
        'product_count': Product.objects.count(),
        'category_count': Category.objects.count(),
        'movement_count': StockMovement.objects.count(),
        'recent_users': UserProfile.objects.select_related('user').order_by('-created_at')[:5],
    }
    return render(request, 'accounts/admin_panel.html', context)


@login_required
def user_list_view(request):
    """Admin only: List all users"""
    if not request.user.profile.is_admin:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('products:dashboard')
    
    users = UserProfile.objects.select_related('user').all()
    
    # Search
    query = request.GET.get('q', '')
    if query:
        users = users.filter(
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    
    return render(request, 'accounts/user_list.html', {
        'users': users,
        'query': query
    })


@login_required
def user_edit_view(request, user_id):
    """Admin only: Edit user role"""
    if not request.user.profile.is_admin:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('products:dashboard')
    
    user_profile = get_object_or_404(UserProfile, user_id=user_id)
    
    if request.method == 'POST':
        form = AdminUserForm(request.POST, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, f'Updated role for {user_profile.user.username}')
            return redirect('accounts:user_list')
    else:
        form = AdminUserForm(instance=user_profile)
    
    return render(request, 'accounts/user_edit.html', {
        'form': form,
        'user_profile': user_profile
    })
