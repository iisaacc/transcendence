from django.http import HttpResponse
from django.urls import path
from django.http import JsonResponse
import logging
import json
from .models import Profile
from profileapi import views
logger = logging.getLogger(__name__)
from django.urls import include, path

urlpatterns = [
    # Signup
    path('api/signup/', views.api_signup, name='api_signup'),

    # Edit profile
    path('api/editprofile/', views.api_edit_profile, name='api_edit_profile'),

    # Getter
    path('api/profile/<str:user_id>/', views.get_profile_api, name='profile_api'),
	  path('api/getFullProfile/<str:user_id>/', views.get_full_profile, name='get_full_profile'),
    path('api/getfriends/<str:user_id>/', views.get_friends, name='get_friends'),
	  path('api/getUsersIds/', views.get_users_ids, name='get_users_ids'),

    # Notifications
    path('api/createnotif/', views.create_notifications, name='create_notifications'),
    path('api/getnotif/<str:user_id>/', views.get_notifications, name='get_notifications'),
    path('api/setnotifasread/<str:sender_id>/<str:receiver_id>/<str:type>/<str:response>/', views.set_notif_as_readen, name='set_notif_as_readen'),
    path('api/setallnotifasread/<str:receiver_id>/', views.set_all_notifs_as_readen, name='set_all_notifs_as_readen'),
    path('api/checkdoublenotif/<str:sender_id>/<str:receiver_id>/<str:type>/', views.check_if_double_request_exists, name='check_if_double_request_exists'),

    # Friends
    path('api/checkfriendship/<int:sender_id>/<int:receiver_id>/', views.check_friendship, name='check_friendship'),
	  path('api/blockFriend/<int:friend_id>/', views.block_friends, name='block'),
  	path('api/unblockFriend/<int:friend_id>/', views.unblock_friends, name='unblock'),
	
    path('livechat/', include('livechat.urls')),

    # Check display names
    path('api/checkDisplaynameExists/', views.check_displayname_exists, name='check_displayname_exists'),

    # Blocked
    path('api/getBlockedUsers/<int:sender_id>/<int:receiver_id>/', views.get_blocked_users, name='get_blocked_users'),
]