from django.urls import path
from . import views

urlpatterns = [
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/signup/', views.api_signup, name='api_signup'),
    path('api/checkUsernameExists/', views.api_check_username_exists, name='api_check_username_exists'),
    path('api/editprofile/', views.api_edit_profile, name='api_edit_profile'),
    path('api/oauth/', views.oauth, name='oauth'),
    path('api/enable2FA/', views.enable2FA, name='enable2FA'),
    path('api/disable2FA/', views.disable2FA, name='disable2FA'),
    path('api/confirm2FA/', views.confirmEnable2FA, name='confirm2FA'),
    path('api/verify2FA/<int:user_id>/', views.verify2FA, name='verify2FA'),

    # Getter
    path('api/getUserInfo/<str:user_id>/', views.api_get_user_info, name='api_get_user_info'),
]
