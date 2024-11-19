import json, asyncio, logging, requests, os
from datetime import datetime
from .handleInvite import get_authentif_variables

logger = logging.getLogger(__name__)

async def sendChatMessage(content, users_connected, self):
  sender_id = content.get('sender_id', '')
  receiver_id = content.get('receiver_id', '')
  message = content.get('message', '')
  date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # Check if user_id is in users_connected
  if receiver_id in users_connected:
    for connection in users_connected[receiver_id]:
      await connection.send_json({
          'type': 'chat',
          'subtype': 'chat_message',
          'message': message,
          'sender_id': sender_id,
          'receiver_id': receiver_id,
          'date': date
      })

  # Save chat message request in database
  profileapi_url = 'https://profileapi:9002/livechat/api/saveChatMessage/'
  message_data = { 'sender_id': sender_id, 'receiver_id': receiver_id, 'message': message, 'type': 'chat_message', 'date': date }
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  try:
    response = requests.post(
          profileapi_url, json=message_data, headers=headers, verify=os.getenv("CERTFILE"))

    response.raise_for_status()
  except Exception as e:
    return

async def getConversation(content, self):
  # Get the database chat messages
  receiver_id = content.get('receiver_id', '')
  profileapi_url = 'https://profileapi:9002/livechat/api/getConversation/' + str(self.user_id) + '/' + str(receiver_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  conversation = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  conversation.raise_for_status()
  if conversation.status_code == 200:
    conversation = sorted(conversation.json(), key=lambda x: x['timestamp'])
    await self.send_json({
      'type': 'chat',
      'subtype': 'load_conversation',
      'conversation': conversation,
      'sender_id': self.user_id,
      'receiver_id': receiver_id
    })

async def checkForChatMessages(self):
  # Get the database chat messages
  profileapi_url = 'https://profileapi:9002/livechat/api/getReceivedChatMessages/' + str(self.user_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  response.raise_for_status()
  if response.status_code == 200:
    chat_messages = sorted(response.json(), key=lambda x: x['timestamp'])
    
  unread_messages_count = 0
  for chat_message in chat_messages:
    if chat_message['read'] == False:
      unread_messages_count += 1
  await self.send_json({
    'type': 'chat',
    'subtype': 'unread_messages',
    'chat_messages': chat_messages,
    'unread_messages_count': unread_messages_count
  })

async def setReadMessages(self):
  # Get the database chat messages
  profileapi_url = 'https://profileapi:9002/livechat/api/setReadMessages/' + str(self.user_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  response.raise_for_status()

async def innitListening(self):
  await self.send_json({
      'type': 'chat',
      'subtype': 'init_listening',
    })
  
async def markConversationAsRead(content, self):
  # Get the database chat messages
  receiver_id = content.get('receiver_id', '')
  sender_id = content.get('sender_id', '')
  profileapi_url = 'https://profileapi:9002/livechat/api/markConversationAsRead/' + str(sender_id) + '/' + str(receiver_id) + '/'
  csrf_token = self.scope['cookies']['csrftoken']
  headers = {
      'X-CSRFToken': csrf_token,
      'Cookie': f'csrftoken={csrf_token}',
      'Content-Type': 'application/json',
      'HTTP_HOST': 'profileapi',
      'Referer': 'https://gateway:8443',
  }
  response = requests.get(profileapi_url, headers=headers, verify=os.getenv("CERTFILE"))

  response.raise_for_status()


async def innitChat(self):
  await innitListening(self)
  await checkForChatMessages(self)