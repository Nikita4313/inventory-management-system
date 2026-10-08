from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),

    # Application administration
    path('admin-panel/', views.admin_panel_view, name='admin_panel'),
    
    # Admin: User Management
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
]
