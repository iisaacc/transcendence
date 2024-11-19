from django.shortcuts import render
from django.http import JsonResponse
from livechat.models import Message
from django.db import DatabaseError
from profileapi.models import Profile
import json
import os
import requests
import logging
logger = logging.getLogger(__name__)

# Create your views here.
def saveChatMessage(request):
	if request.method == 'POST':
		data = json.loads(request.body)
		logger.debug(f'data: {data}')
		sender = Profile.objects.get(user_id=data['sender_id'])
		receiver = Profile.objects.get(user_id=data['receiver_id'])
		try:
			message = Message(
				send_user=sender,
				dest_user=receiver,
				message=data['message'],
				timestamp=data['date']
			)
			message.save()
			return JsonResponse({'message': 'Message saved'}, status=201)
		except DatabaseError as e:
			return JsonResponse({'message': 'Error saving message'}, status=400)
	else:
		return JsonResponse({'message': 'Method not allowed'}, status=405)
	
def getSentChatMessages(request, user_id):
	id = int(user_id)
	if request.method == 'GET':
		try:
			user = Profile.objects.get(user_id=id)
			messages = Message.objects.filter(send_user=user)
			data = []
			for message in messages:
				data.append({
					'send_user': message.send_user.user_id,
					'dest_user': message.dest_user.user_id,
					'message': message.message,
					'timestamp': message.timestamp,
					'read': message.read
				})
			return JsonResponse(data, safe=False)
		except DatabaseError as e:
			return JsonResponse({'message': 'Error getting messages'}, status=400)
	else:
		return JsonResponse({'message': 'Method not allowed'}, status=405)
	
def getReceivedChatMessages(request, user_id):
	id = int(user_id)
	if request.method == 'GET':
		try:
			user = Profile.objects.get(user_id=id)
			messages = Message.objects.filter(dest_user=user)
			data = []
			for message in messages:
				data.append({
					'send_user': message.send_user.user_id,
					'dest_user': message.dest_user.user_id,
					'message': message.message,
					'timestamp': message.timestamp,
					'read': message.read
				})
			logger.debug(f'getReceivedChatMessages > data: {data}')
			return JsonResponse(data, safe=False)
		except DatabaseError as e:
			return JsonResponse({'message': 'Error getting messages'}, status=400)
	else:
		return JsonResponse({'message': 'Method not allowed'}, status=405)
	
def markConversationAsRead(request, user_1_id, user_2_id):
	user_1_id = int(user_1_id)
	user_2_id = int(user_2_id)
	if request.method == 'GET':
		try:
			user_1 = Profile.objects.get(user_id=user_1_id)
			user_2 = Profile.objects.get(user_id=user_2_id)
			messages = Message.objects.filter(send_user=user_1, dest_user=user_2, read=False)
			for message in messages:
				message.read = True
				message.save()
				
			messages = Message.objects.filter(send_user=user_2, dest_user=user_1, read=False)
			for message in messages:
				message.read = True
				message.save()
			return JsonResponse({'message': 'Conversation marked as read'}, status=200)
		except DatabaseError as e:
			return JsonResponse({'message': 'Error marking conversation as read'}, status=400)
	else:
		return JsonResponse({'message': 'Method not allowed'}, status=405)


def getConversation(request, user_1_id, user_2_id):
	user_1_id = int(user_1_id)
	user_2_id = int(user_2_id)
	if request.method == 'GET':
		try:
			user_1 = Profile.objects.get(user_id=user_1_id)
			user_2 = Profile.objects.get(user_id=user_2_id)
			messages = Message.objects.filter(send_user=user_1, dest_user=user_2) | Message.objects.filter(send_user=user_2, dest_user=user_1)
			data = []
			for message in messages:
				data.append({
					'sender_id': message.send_user.user_id,
					'receiver_id': message.dest_user.user_id,
					'message': message.message,
					'timestamp': message.timestamp,
					'read': message.read
				})
			markConversationAsRead(request, user_1_id, user_2_id)
			return JsonResponse(data, safe=False)
		except DatabaseError as e:
			return JsonResponse({'message': 'Error getting messages'}, status=400)
	else:
		return JsonResponse({'message': 'Method not allowed'}, status=405)
	