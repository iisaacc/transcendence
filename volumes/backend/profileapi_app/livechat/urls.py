from django.http import HttpResponse
from django.urls import path
from django.http import JsonResponse
import logging
import json
from .models import Message
from livechat import views
logger = logging.getLogger(__name__)

urlpatterns = [
    # Save chat message
    path('api/saveChatMessage/', views.saveChatMessage, name='save_chat_message'),
	path('api/getSentChatMessages/<int:user_id>/', views.getSentChatMessages, name='get_sent_chat_messages'),
	path('api/getReceivedChatMessages/<int:user_id>/', views.getReceivedChatMessages, name='get_received_chat_messages'),
	path('api/getConversation/<int:user_1_id>/<int:user_2_id>/', views.getConversation, name='get_conversation'),
	path('api/markConversationAsRead/<int:user_1_id>/<int:user_2_id>/', views.markConversationAsRead, name='mark_conversation_read'),
]